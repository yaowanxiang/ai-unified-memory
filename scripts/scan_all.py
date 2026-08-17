# -*- coding: utf-8 -*-
"""
scan_all.py — 扫描各AI记忆源，提取增量记忆条目
输出: 各AI专有库下的 _scanned/ 目录（原始条目），并更新 STATUS.json
用法: python scan_all.py [--full]
"""
import os
import sys
import hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (cfg, log, read_text, write_text, load_json, save_json,
                    read_status, save_status, priv_dir, content_hash, now_str, today_str)

def scan_ai(ai_name, ai_cfg, status, full=False):
    src = ai_cfg.get("memory_source", "")
    files = ai_cfg.get("memory_files", [])
    recursive = ai_cfg.get("recursive_md", False)
    if not src or not os.path.isdir(src):
        log(f"[{ai_name}] 记忆源不存在: {src}", "WARN")
        return 0
    scanned_dir = os.path.join(priv_dir(ai_name), "_scanned")
    os.makedirs(scanned_dir, exist_ok=True)
    ai_status = status.setdefault("ais", {}).setdefault(ai_name, {})
    seen_hashes = set(ai_status.get("seen_hashes", []))
    count = 0
    # 递归模式：扫描整个记忆目录树的所有 .md 文件
    if recursive:
        md_files = []
        for dirpath, dirnames, filenames in os.walk(src):
            for fn in filenames:
                if fn.endswith(".md"):
                    md_files.append(os.path.join(dirpath, fn))
        # 按相对路径分类存放快照，保留原目录结构
        for path in sorted(md_files):
            rel = os.path.relpath(path, src).replace("\\", "_").replace("/", "_")
            mtime = os.path.getmtime(path)
            key = "rec_" + rel
            if not full and ai_status.get(key + "_mtime", 0) == mtime:
                continue
            text = read_text(path)
            if not text or len(text.strip()) < 10:
                continue
            h = content_hash(text)
            if h in seen_hashes:
                ai_status[key + "_mtime"] = mtime
                continue
            snap = os.path.join(scanned_dir, "rec_" + rel + ".snap.md")
            write_text(snap, f"# 源文件: {path}\n# 扫描时间: {now_str()}\n\n" + text)
            seen_hashes.add(h)
            ai_status[key + "_mtime"] = mtime
            count += 1
            log(f"[{ai_name}] 捕获记忆 {rel} ({len(text)}字符)")
        ai_status["recursive_file_count"] = len(md_files)
        ai_status["last_scan"] = now_str()
        ai_status["last_scan_count"] = count
        ai_status["seen_hashes"] = list(seen_hashes)[-1000:]
        return count
    # 固定文件模式
    for fn in files:
        path = os.path.join(src, fn)
        if not os.path.exists(path):
            continue
        mtime = os.path.getmtime(path)
        if not full and ai_status.get(fn + "_mtime", 0) == mtime:
            continue  # 未变更
        text = read_text(path)
        if not text:
            continue
        h = content_hash(text)
        if h in seen_hashes:
            ai_status[fn + "_mtime"] = mtime
            continue
        # 存原始快照
        snap = os.path.join(scanned_dir, fn.replace(".", "_") + ".snap.md")
        write_text(snap, f"# 源文件: {path}\n# 扫描时间: {now_str()}\n\n" + text)
        seen_hashes.add(h)
        ai_status[fn + "_mtime"] = mtime
        count += 1
        log(f"[{ai_name}] 捕获记忆文件 {fn} ({len(text)}字符, hash={h})")
    # OpenClaw agents 目录扫描（agent 名称列表）
    agents_dir = ai_cfg.get("agents_dir", "")
    if agents_dir and os.path.isdir(agents_dir):
        agent_list = sorted(os.listdir(agents_dir))
        agents_snap = os.path.join(scanned_dir, "openclaw_agents.snap.md")
        write_text(agents_snap, f"# OpenClaw Agents 清单\n# 扫描时间: {now_str()}\n\n" +
                   "\n".join(f"- {a}" for a in agent_list))
        ai_status["agent_count"] = len(agent_list)
        log(f"[{ai_name}] OpenClaw agents 清单: {len(agent_list)} 个")
    ai_status["seen_hashes"] = list(seen_hashes)[-500:]  # 防膨胀
    ai_status["last_scan"] = now_str()
    ai_status["last_scan_count"] = count
    return count

def main():
    full = "--full" in sys.argv
    status = read_status()
    c = cfg()
    total = 0
    log(f"=== 扫描开始 {'(全量)' if full else '(增量)'} ===")
    for ai_name, ai_cfg in c["ais"].items():
        if not ai_cfg.get("enabled", True):
            continue
        n = scan_ai(ai_name, ai_cfg, status, full)
        total += n
    status["last_full_run"] = now_str()
    save_status(status)
    log(f"=== 扫描完成: 捕获 {total} 条新记忆 ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
