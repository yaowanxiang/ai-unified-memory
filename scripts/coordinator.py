# -*- coding: utf-8 -*-
"""
coordinator.py — 主协调器（调度中心核心）
全流程: 扫描 → 提升 → 分发 → 索引 → 快照 → 状态
用法: python coordinator.py [--full] [--no-snapshot]
"""
import os
import sys
import shutil
import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, log, read_status, save_status, now_str, today_str, load_json, save_json

def run_script(name, *args):
    """调用同级脚本。"""
    import subprocess
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    cmd = [sys.executable, script] + list(args)
    log(f"执行: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout:
        for line in r.stdout.strip().splitlines():
            log(f"  {line}")
    if r.returncode != 0:
        log(f"脚本 {name} 失败: {r.stderr[-500:]}", "ERROR")
        return False
    return True

def build_index():
    """生成公用库记忆索引 README。"""
    from common import pub_dir
    index_lines = ["# 🧠 公用库记忆索引", "", f"> 自动生成: {now_str()}", ""]
    total = 0
    for cat in ["00_用户画像", "01_项目知识", "02_领域知识", "03_技能工具",
                "04_经验教训", "05_决策记录"]:
        cat_dir = os.path.join(pub_dir(), cat)
        if not os.path.isdir(cat_dir):
            continue
        files = [f for f in os.listdir(cat_dir) if f.endswith(".md") and f != "README.md"]
        total += len(files)
        index_lines.append(f"## {cat} ({len(files)})")
        index_lines.append("")
        for f in sorted(files):
            index_lines.append(f"- {f}")
        index_lines.append("")
    index_lines.insert(3, f"**总记忆条目: {total}**")
    from common import write_text
    write_text(os.path.join(pub_dir(), "06_记忆索引", "INDEX.md"),
               "\n".join(index_lines))
    log(f"索引已生成: {total} 条公用记忆")
    return total

def snapshot():
    """快照公用库到 04_快照备份/日期/。"""
    from common import pub_dir
    c = cfg()
    snap_root = os.path.join(c["root"], c["snapshot"])
    today = today_str()
    dest = os.path.join(snap_root, today)
    if os.path.exists(dest):
        log(f"快照已存在: {dest}，跳过")
        return
    shutil.copytree(pub_dir(), dest)
    log(f"快照完成: {dest}")

def main():
    full = "--full" in sys.argv
    no_snap = "--no-snapshot" in sys.argv
    log("🚀 === AI 统一记忆协调器启动 ===")
    ok = True
    ok &= run_script("scan_all.py", "--full" if full else "")
    ok &= run_script("promote.py")
    ok &= run_script("dispatch.py")
    n = build_index()
    if not no_snap:
        snapshot()
    status = read_status()
    status["last_coordinator"] = now_str()
    status["public_count"] = n
    status["last_mode"] = "full" if full else "incremental"
    save_status(status)
    log(f"✅ === 协调完成: 公用记忆 {n} 条 | 模式: {status['last_mode']} ===")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
