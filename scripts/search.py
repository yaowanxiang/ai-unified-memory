# -*- coding: utf-8 -*-
"""
search.py — 统一检索接口（按需调用）
跨公用库 + 专有库 + 交换区全文检索，支持关键词/正则
用法:
  python search.py "关键词"
  python search.py "关键词" --limit 10 --ai Hermes
"""
import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, read_text, pub_dir, priv_dir, log

def walk_md(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".md") or fn.endswith(".json"):
                yield os.path.join(dirpath, fn)

def search_all(query, limit=10, ai_filter=None):
    c = cfg()
    results = []
    query_l = query.lower()
    # 公用库
    for path in walk_md(pub_dir()):
        text = read_text(path) or ""
        if query_l in text.lower():
            results.append(("公用库", path, text))
    # 专有库（可选过滤）
    for ai_name in c["ais"]:
        if ai_filter and ai_name != ai_filter:
            continue
        for path in walk_md(priv_dir(ai_name)):
            text = read_text(path) or ""
            if query_l in text.lower():
                results.append((f"专有库/{ai_name}", path, text))
    # 交换区
    for path in walk_md(os.path.join(c["root"], c["exchange"])):
        text = read_text(path) or ""
        if query_l in text.lower():
            results.append(("交换区", path, text))
    # 去重 + 截断
    seen, out = set(), []
    for loc, path, text in results:
        if path in seen:
            continue
        seen.add(path)
        # 提取命中上下文
        idx = text.lower().find(query_l)
        ctx = text[max(0, idx-120): idx+280].replace("\n", " ")
        out.append({"location": loc, "path": path, "context": ctx})
        if len(out) >= limit:
            break
    return out

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    query = args[0]
    limit = 10
    ai_filter = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--ai" in args:
        ai_filter = args[args.index("--ai") + 1]
    results = search_all(query, limit, ai_filter)
    print(f"\n🔍 检索: 「{query}」 → {len(results)} 条结果\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['location']}] {os.path.basename(r['path'])}")
        print(f"   {r['path']}")
        print(f"   …{r['context']}…")
        print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
