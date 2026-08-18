# -*- coding: utf-8 -*-
"""
desktop.py — AI Unified Memory 桌面客户端入口
功能: 记忆浏览 / 语义检索 / 冲突消解 / 调度运行 / 跨AI消息 / 热记忆
架构: pywebview + 内嵌 FastAPI (threading)
"""
import os
import sys
import socket
import threading
import time
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path.home() / ".ai-unified-memory"
else:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"

APP_TITLE = "AI Unified Memory — 多AI共享记忆中心"
DEFAULT_SIZE = (1280, 820)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_api(port: int) -> None:
    sys.path.insert(0, str(BASE_DIR.parent))   # 让 scripts 可导入
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from api import build_app

    app = build_app(BASE_DIR)
    app.routes[:] = [r for r in app.routes
                     if not (getattr(r, "path", None) == "/"
                             and getattr(r, "methods", None) == {"GET"})]
    web_dir = BASE_DIR / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True))
    config = uvicorn.Config(app, host="127.0.0.1", port=port,
                            log_level="warning", access_log=False)
    uvicorn.Server(config).run()


def _wait_ready(port: int, timeout: float = 12.0) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main() -> None:
    if FROZEN:
        import multiprocessing
        multiprocessing.freeze_support()
    port = find_free_port()
    threading.Thread(target=_run_api, args=(port,), daemon=True).start()
    _wait_ready(port)
    import webview
    webview.create_window(APP_TITLE, f"http://127.0.0.1:{port}/",
                          width=DEFAULT_SIZE[0], height=DEFAULT_SIZE[1],
                          min_size=(980, 640))
    webview.start()


if __name__ == "__main__":
    main()
