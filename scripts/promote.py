# -*- coding: utf-8 -*-
"""
promote.py — 提升引擎：扫描各AI专有库 _scanned 原始记忆 → 全局去重 → 分类 → 写入公用库
用法: python promote.py
"""
import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (cfg, log, read_text, write_text, load_json, save_json,
                    pub_dir, priv_dir, content_hash, classify_category,
                    memo_header, safe_filename, now_str)

GLOBAL_INDEX = "00_调度中心/GLOBAL_INDEX.json"
CATS = ["00_用户画像", "01_项目知识", "02_领域知识",
        "03_技能工具", "04_经验教训", "05_决策记录"]

def load_global_index():
    return load_json(os.path.join(cfg()["root"], GLOBAL_INDEX), {"entries": {}})

def save_global_index(idx):
    save_json(os.path.join(cfg()["root"], GLOBAL_INDEX), idx)

def promote_file(snap_path, ai_name, gidx):
    """把一条快照文件提升为公用库记忆条目。返回 (title, out_path) 或 None"""
    text = read_text(snap_path)
    if not text or len(text.strip()) < 20:
        return None
    # 剔除扫描时间戳行（防重复提升）
    import re as _re
    text_for_hash = _re.sub(r"^# 扫描时间: .*$", "", text, flags=_re.M)
    h = content_hash(text_for_hash.strip())
    if h in gidx["entries"]:
        return None  # 全局去重
    # 标题提取：优先内容中的第一个有意义标题，否则用 AI名_文件名
    lines = text.splitlines()
    title = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("# ") and "源文件" not in s and "扫描时间" not in s:
            title = s[2:].strip()
            break
    if not title:
        src_file = ""
        for ln in lines:
            if ln.startswith("# 源文件"):
                src_file = ln.split(":", 1)[-1].strip() if ":" in ln else ""
                break
        base = os.path.basename(src_file or snap_path).replace(".snap.md", "").replace(".", "_")
        title = f"{ai_name}_{base}"
    # 标题清洗：去掉 .md 后缀、下划线转空格
    title = title.replace(".md", "").strip()
    category = classify_category(text)
    target_dir = os.path.join(pub_dir(), category)
    os.makedirs(target_dir, exist_ok=True)
    body = memo_header(title, ai_name, category, summary="扫描提升") + text
    fn = f"{safe_filename(title)}_{h}.md"
    out = os.path.join(target_dir, fn)
    write_text(out, body)
    gidx["entries"][h] = {"title": title, "file": fn, "category": category,
                          "source_ai": ai_name, "created": now_str()}
    log(f"[提升] {ai_name} → {category}/{fn}")
    return (title, out)

def run():
    gidx = load_global_index()
    promoted = 0
    for ai_name in cfg()["ais"]:
        scanned_dir = os.path.join(priv_dir(ai_name), "_scanned")
        if not os.path.isdir(scanned_dir):
            continue
        for fn in sorted(os.listdir(scanned_dir)):
            if not fn.endswith(".snap.md"):
                continue
            r = promote_file(os.path.join(scanned_dir, fn), ai_name, gidx)
            if r:
                promoted += 1
    save_global_index(gidx)
    return promoted

def main():
    log("=== 提升引擎开始 ===")
    n = run()
    log(f"=== 提升完成: 新增 {n} 条公用记忆 (累计 {len(load_global_index()['entries'])} 条) ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
