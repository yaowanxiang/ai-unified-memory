# -*- coding: utf-8 -*-
"""
dispatch.py — 分发引擎：将公用库记忆生成各AI的"共享记忆注入"文件
每个AI的注入文件包含: 核心用户画像 + 最近项目 + 关键教训 + 决策记录
各AI在会话启动时读取自己的注入文件即可获得共享记忆
用法: python dispatch.py [--ai Hermes]
"""
import os
import sys
import re
import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (cfg, log, read_text, write_text, pub_dir, priv_dir, now_str)

CAT_ORDER = [
    ("00_用户画像", "🧑 用户画像", "01"),
    ("01_项目知识", "📁 项目知识", "02"),
    ("02_领域知识", "📚 领域知识", "03"),
    ("03_技能工具", "🛠 技能与工具", "04"),
    ("04_经验教训", "⚠️ 经验教训（黄金法则）", "05"),
    ("05_决策记录", "🎯 决策记录", "06"),
]

def collect_public_memos(limit_per_cat=8):
    """按分类收集公用库记忆条目，返回 {category: [ (title, summary, file) ]}"""
    result = {}
    for cat, label, order in CAT_ORDER:
        cat_dir = os.path.join(pub_dir(), cat)
        if not os.path.isdir(cat_dir):
            result[cat] = []
            continue
        items = []
        for fn in sorted(os.listdir(cat_dir)):
            if not fn.endswith(".md") or fn == "README.md":
                continue
            path = os.path.join(cat_dir, fn)
            text = read_text(path) or ""
            # 提取标题和摘要
            title = fn.rsplit("_", 1)[0].replace("_", " ")
            summary = ""
            m = re.search(r"^summary:\s*(.+)$", text, re.M)
            if m:
                summary = m.group(1).strip()
            # 取正文前300字作为摘要
            body = text.split("---", 2)[-1].strip() if text.count("---") >= 2 else text
            first_lines = [ln.strip() for ln in body.splitlines() if ln.strip()][:3]
            excerpt = " ".join(first_lines)[:300]
            items.append((title, summary or excerpt, fn))
        items.sort(key=lambda x: x[0])
        result[cat] = items[:limit_per_cat]
    return result

def re_search(pattern, text, flags=0):
    import re
    return re.search(pattern, text, flags)

def build_inject_doc(ai_name, memos):
    lines = []
    lines.append("# 🤝 AI 共享记忆注入（自动生成）")
    lines.append("")
    lines.append(f"> 本文件由 AI Unified Memory 调度中心自动生成 | 生成时间: {now_str()}")
    lines.append(f"> 面向: **{ai_name}** — 会话启动时请先阅读本文件，获取全AI共享记忆。")
    lines.append(f"> 完整检索: 运行 `python D:/AI\\ memory/scripts/search.py <关键词>`")
    lines.append("")
    lines.append("---")
    lines.append("")
    for cat, label, order in CAT_ORDER:
        items = memos.get(cat, [])
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        if not items:
            lines.append("_（暂无）_")
            lines.append("")
            continue
        for title, summary, fn in items:
            lines.append(f"- **{title}**")
            if summary:
                lines.append(f"  - {summary[:200]}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📮 交换区提醒")
    lines.append("")
    inbox = os.path.join(cfg()["root"], cfg()["exchange"], "INBOX", ai_name)
    if os.path.isdir(inbox):
        msgs = [f for f in os.listdir(inbox) if f.endswith(".md")]
        if msgs:
            lines.append(f"你有 {len(msgs)} 条待处理消息:")
            for m in sorted(msgs)[-5:]:
                lines.append(f"- `{m}`")
        else:
            lines.append("_（无待处理消息）_")
    lines.append("")
    lines.append(f"_来源: {cfg()['root']}\\01_公用库 (权威源) | 调度: 00_调度中心\\coordinator.py_")
    return "\n".join(lines)

def run(ai_name=None):
    memos = collect_public_memos()
    c = cfg()
    targets = [ai_name] if ai_name else list(c["ais"].keys())
    for ai in targets:
        if ai not in c["ais"]:
            log(f"[分发] 未知AI: {ai}", "WARN")
            continue
        doc = build_inject_doc(ai, memos)
        out = os.path.join(cfg()["root"], c["ais"][ai]["inject_file"])
        write_text(out, doc)
        log(f"[分发] {ai} 注入文件已更新: {out}")
    return len(targets)

def main():
    import sys as _s
    ai = None
    if "--ai" in _s.argv:
        ai = _s.argv[_s.argv.index("--ai") + 1]
    log("=== 分发引擎开始 ===")
    n = run(ai)
    log(f"=== 分发完成: {n} 个AI注入文件已更新 ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
