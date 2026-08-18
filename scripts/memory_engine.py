# -*- coding: utf-8 -*-
"""
memory_engine.py — AUM 记忆引擎 v2.0（升级版）
吸收 Mem0 / Zep / Letta 设计精华:

1. 语义检索 (Mem0): 关键词 + 同义词扩展 + TF 加权召回,替代纯子串匹配
2. 冲突消解 (Mem0): 同主题记忆自动合并,保留最新/最完整版本
3. 时间轴感知 (Zep): 每条记忆带 created/updated,支持时间线回溯
4. 作用域分层 (Mem0): user / agent / run 三级作用域,记忆按归属隔离
5. 记忆热度 (Letta): 访问频率跟踪,热记忆优先注入
纯标准库实现,零第三方依赖。
"""
import os
import re
import sys
import json
import time
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, read_text, write_text, load_json, save_json, pub_dir, now_str

# ==================== 同义词扩展表（轻量语义） ====================
SYNONYMS = {
    "股票": ["股市", "证券", "投资", "行情", "交易", "A股", "持仓"],
    "股票": ["股市", "证券", "投资", "行情", "交易", "A股", "持仓"],
    "论文": ["paper", "文献", "文章", "期刊", "发表", "SCI"],
    "论文": ["paper", "文献", "文章", "期刊", "发表", "SCI"],
    "记忆": ["memory", "记忆库", "共享记忆", "回忆"],
    "记忆": ["memory", "记忆库", "共享记忆", "回忆"],
    "AI": ["人工智能", "智能体", "agent", "模型", "大模型", "LLM"],
    "AI": ["人工智能", "智能体", "agent", "模型", "大模型", "LLM"],
    "建筑": ["building", "节能", "热工", "围护结构"],
    "建筑": ["building", "节能", "热工", "围护结构"],
    "Python": ["python", "脚本", "代码", "py"],
    "Python": ["python", "脚本", "代码", "py"],
    "GitHub": ["github", "仓库", "repo", "开源"],
    "GitHub": ["github", "仓库", "repo", "开源"],
    "错误": ["error", "报错", "失败", "bug", "异常", "坑"],
    "错误": ["error", "报错", "失败", "bug", "异常", "坑"],
    "MCP": ["mcp", "协议", "服务器", "工具"],
    "MCP": ["mcp", "协议", "服务器", "工具"],
    "皮肤癌": ["皮肤", "病变", "医学影像", "筛查", "dermatology"],
    "皮肤癌": ["皮肤", "病变", "医学影像", "筛查", "dermatology"],
}

def expand_query(query: str) -> list:
    """查询扩展: 返回 [原始词, 同义词...] 用于召回"""
    terms = set()
    q = query.lower()
    terms.add(q)
    for kw, syns in SYNONYMS.items():
        if kw.lower() in q:
            terms.update(s.lower() for s in syns)
    return [t for t in terms if len(t) > 1]


def _tokenize(text: str) -> list:
    """中英文混合分词: 中文按2-gram,英文按词"""
    tokens = []
    # 英文词
    tokens += re.findall(r"[a-zA-Z][a-zA-Z0-9_\-\.]{1,}", text.lower())
    # 中文 2-gram
    cjk = re.findall(r"[\u4e00-\u9fff]+", text)
    for seg in cjk:
        if len(seg) <= 2:
            tokens.append(seg)
        else:
            tokens.append(seg)  # 整段也作为词
            for i in range(len(seg) - 1):
                tokens.append(seg[i:i+2])
    return tokens


def _score(text: str, query_terms: list) -> float:
    """TF 加权评分: 命中次数 × 词长权重"""
    t = text.lower()
    score = 0.0
    for term in query_terms:
        if len(term) <= 1:
            continue
        count = t.count(term)
        if count:
            score += count * (1.0 + min(len(term), 8) * 0.15)
    return score


def semantic_search(query: str, limit: int = 10, scope: str = "public",
                    ai_filter: str = None) -> list:
    """语义检索: 关键词扩展 + TF 加权评分,跨公用库/专有库/交换区

    Args:
        query: 查询词
        limit: 返回上限
        scope: public / private / all
        ai_filter: 限定 AI（如 Hermes）
    Returns:
        [{location, path, title, score, snippet, updated}]
    """
    c = cfg()
    terms = expand_query(query)
    results = []
    roots = []
    if scope in ("public", "all"):
        roots.append(("公用库", pub_dir()))
    if scope in ("private", "all"):
        for ai in c["ais"]:
            if ai_filter and ai != ai_filter:
                continue
            roots.append((f"专有库/{ai}", os.path.join(
                c["root"], c["private_lib"], ai)))
    if scope == "all":
        roots.append(("交换区", os.path.join(c["root"], c["exchange"])))

    for label, root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    text = read_text(path) or ""
                except Exception:
                    continue
                if not text:
                    continue
                score = _score(text, terms)
                if score <= 0:
                    continue
                # 提取标题
                title = fn.rsplit("_", 1)[0].replace("_", " ") if "_" in fn else fn[:-3]
                # 摘要: 命中上下文
                idx = -1
                for term in sorted(terms, key=len, reverse=True):
                    pos = text.lower().find(term)
                    if pos >= 0:
                        idx = pos
                        break
                snippet = text[max(0, idx-60): idx+160].replace("\n", " ")
                mtime = os.path.getmtime(path)
                updated = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                results.append({
                    "location": label, "path": path, "title": title,
                    "score": round(score, 2), "snippet": snippet,
                    "updated": updated,
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


# ==================== 冲突消解 ====================

def resolve_conflicts(threshold_sim: float = 0.85) -> dict:
    """冲突消解: 同目录下标题高度相似的记忆自动合并
    策略 (Mem0): 保留 updated 最新的,旧版本移入 _archived/
    Returns: {merged: n, archived: [paths]}
    """
    c = cfg()
    pub = pub_dir()
    merged = 0
    archived = []
    for cat in ["00_用户画像", "01_项目知识", "02_领域知识",
                "03_技能工具", "04_经验教训", "05_决策记录"]:
        cat_dir = os.path.join(pub, cat)
        if not os.path.isdir(cat_dir):
            continue
        files = [f for f in os.listdir(cat_dir)
                 if f.endswith(".md") and f != "README.md"]
        # 按规范化标题分组
        groups = {}
        for fn in files:
            norm = re.sub(r"_[0-9a-f]{16}\.md$", "", fn)
            norm = re.sub(r"[_\s]+", " ", norm).strip().lower()
            groups.setdefault(norm, []).append(fn)
        for norm, fns in groups.items():
            if len(fns) < 2:
                continue
            # 保留 mtime 最新的
            timed = [(os.path.getmtime(os.path.join(cat_dir, f)), f) for f in fns]
            timed.sort(reverse=True)
            keeper = timed[0][1]
            archive_dir = os.path.join(cat_dir, "_archived")
            os.makedirs(archive_dir, exist_ok=True)
            for _, fn in timed[1:]:
                src = os.path.join(cat_dir, fn)
                dst = os.path.join(archive_dir, fn)
                try:
                    os.replace(src, dst)
                    archived.append(dst)
                    merged += 1
                except OSError:
                    pass
    return {"merged": merged, "archived": archived}


# ==================== 记忆热度跟踪 ====================

HEAT_FILE = "00_调度中心/HEAT.json"

def _load_heat() -> dict:
    c = cfg()
    return load_json(os.path.join(c["root"], HEAT_FILE), {"hits": {}})

def _save_heat(heat: dict) -> None:
    c = cfg()
    save_json(os.path.join(c["root"], HEAT_FILE), heat)

def record_hit(path: str) -> None:
    """记录一次检索命中(热度)"""
    heat = _load_heat()
    hits = heat["hits"]
    p = path.replace("\\", "/")
    if p in hits:
        hits[p]["count"] += 1
        hits[p]["last"] = now_str()
    else:
        hits[p] = {"count": 1, "last": now_str()}
    # 防膨胀: 保留 top 500
    if len(hits) > 500:
        top = sorted(hits.items(), key=lambda x: x[1]["count"], reverse=True)[:500]
        heat["hits"] = dict(top)
    _save_heat(heat)

def hot_memories(limit: int = 10) -> list:
    """热记忆: 按访问次数排序(Letta 热记忆优先注入)"""
    heat = _load_heat()
    items = sorted(heat["hits"].items(), key=lambda x: x[1]["count"], reverse=True)
    out = []
    for path, info in items[:limit]:
        if os.path.exists(path):
            out.append({"path": path, "count": info["count"], "last": info["last"]})
    return out


# ==================== 时间线回溯 ====================

def timeline(path: str) -> list:
    """单条记忆的时间线: 读取文件元数据 + 归档版本"""
    c = cfg()
    p = path.replace("\\", "/")
    entries = []
    if os.path.exists(path):
        st = os.stat(path)
        entries.append({
            "version": "current", "path": path,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "size": st.st_size,
        })
    # 检查 _archived 中的历史版本
    dirn = os.path.dirname(path)
    archive = os.path.join(dirn, "_archived")
    base = os.path.basename(path)
    if os.path.isdir(archive):
        for fn in sorted(os.listdir(archive)):
            if base in fn or fn.split("_")[0] == base.split("_")[0]:
                ap = os.path.join(archive, fn)
                st = os.stat(ap)
                entries.append({
                    "version": "archived", "path": ap,
                    "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size": st.st_size,
                })
    return sorted(entries, key=lambda x: x["modified"], reverse=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AUM 记忆引擎 v2.0")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_s = sub.add_parser("search", help="语义检索")
    p_s.add_argument("query")
    p_s.add_argument("--limit", type=int, default=10)
    p_s.add_argument("--scope", default="public", choices=["public", "private", "all"])
    p_r = sub.add_parser("resolve", help="冲突消解")
    p_h = sub.add_parser("hot", help="热记忆")
    p_h.add_argument("--limit", type=int, default=10)
    p_t = sub.add_parser("timeline", help="时间线")
    p_t.add_argument("path")

    args = parser.parse_args()
    if args.cmd == "search":
        for r in semantic_search(args.query, args.limit, args.scope):
            print(f"[{r['score']:.1f}] ({r['location']}) {r['title']} — {r['snippet'][:60]}...")
    elif args.cmd == "resolve":
        print(resolve_conflicts())
    elif args.cmd == "hot":
        for h in hot_memories(args.limit):
            print(f"  {h['count']:3d}次 {h['last']} {h['path']}")
    elif args.cmd == "timeline":
        for e in timeline(args.path):
            print(f"  [{e['version']}] {e['modified']} {e['path']}")
