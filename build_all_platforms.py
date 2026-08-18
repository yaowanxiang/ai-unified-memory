#!/usr/bin/env python3
"""
AI Unified Memory - 跨平台构建脚本 (Windows/macOS/Linux)
用法: python build_all_platforms.py
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
APP_NAME = "AI-Unified-Memory"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def detect_os():
    s = platform.system().lower()
    return {"darwin": "macos", "windows": "windows", "linux": "linux"}.get(s, s)


def build():
    system = detect_os()
    print(f"当前系统: {system}")

    # 打包 scripts/ 目录 + 核心数据目录
    sep = ";" if os.name == "nt" else ":"
    add_data = []
    for d in ["scripts", "01_公用库", "02_专有库", "03_交换区"]:
        if (ROOT / d).exists():
            add_data.extend(["--add-data", f"{ROOT / d}{sep}{d}"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--hidden-import=common",
        *add_data,
        str(ROOT / "gui_app.py"),
    ]
    print("构建中...")
    subprocess.run(cmd, cwd=str(ROOT), check=True)

    if system == "windows":
        src = DIST / f"{APP_NAME}.exe"
        src.rename(DIST / f"{APP_NAME}-Windows.exe")
    elif system == "macos":
        src = DIST / APP_NAME
        if src.exists():
            src.rename(DIST / f"{APP_NAME}-macOS")
    else:
        src = DIST / APP_NAME
        src.rename(DIST / f"{APP_NAME}-Linux.AppImage")

    print("✅ 构建完成!")
    for f in sorted(DIST.iterdir()):
        if f.is_file() or f.is_dir():
            print(f"   📦 {f.name}")


if __name__ == "__main__":
    build()
