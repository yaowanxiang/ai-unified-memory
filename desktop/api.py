# -*- coding: utf-8 -*-
"""
api.py — AI Unified Memory 桌面客户端后端 API
功能: 状态 / 记忆浏览 / 语义检索 / 冲突消解 / 调度 / 消息 / 热记忆
"""
import os
import sys
import json
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

# 让 scripts 可导入（兼容开发与 PyInstaller 打包环境）
import sys as _sys
FROZEN = bool(getattr(_sys, "frozen", False))
if FROZEN:
    _MEIPASS = Path(_sys._MEIPASS)
    SCRIPTS = _MEIPASS / "scripts"          # 打包: --add-data "scripts:scripts"
else:
    SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import common
import memory_engine

# 打包环境: 数据重定向到用户可写目录 (~/.ai-unified-memory/)，避免写入只读 _MEIPASS
if FROZEN:
    DATA_DIR = Path.home() / ".ai-unified-memory"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    common.ROOT = str(DATA_DIR)
    # 首次运行: 从 example 复制 CONFIG.json
    cfg_file = DATA_DIR / "CONFIG.json"
    if not cfg_file.exists():
        example = SCRIPTS.parent / "CONFIG.example.json"
        if example.exists():
            import shutil
            shutil.copy(example, cfg_file)
    # 初始化目录结构
    for d in ("01_公用库", "02_专有库", "03_交换区/INBOX",
              "03_交换区/OUTBOX", "04_快照备份", "00_调度中心"):
        (DATA_DIR / d).mkdir(parents=True, exist_ok=True)


class SearchReq(BaseModel):
    query: str
    limit: int = 10
    scope: str = "public"


class MsgSendReq(BaseModel):
    to: str
    title: str
    body: str = ""


class MsgReadReq(BaseModel):
    id: str


class CoordReq(BaseModel):
    full: bool = False


def build_app(base_dir: Path) -> FastAPI:
    app = FastAPI(title="AI Unified Memory Desktop")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "name": "aum-desktop"}

    @app.get("/api/status")
    def status():
        st = common.read_status()
        return {
            "last_coordinator": st.get("last_coordinator", "—"),
            "public_count": st.get("public_count", 0),
            "ais": {
                ai: {
                    "last_scan": (info or {}).get("last_scan", "—"),
                    "last_scan_count": (info or {}).get("last_scan_count", 0),
                }
                for ai, info in st.get("ais", {}).items()
            },
        }

    @app.get("/api/memories")
    def memories(category: str = None):
        """列出公用库记忆（可按分类过滤）"""
        from common import pub_dir
        cats = ["00_用户画像", "01_项目知识", "02_领域知识",
                "03_技能工具", "04_经验教训", "05_决策记录"]
        if category:
            cats = [c for c in cats if category in c]
        out = []
        for cat in cats:
            cat_dir = os.path.join(pub_dir(), cat)
            if not os.path.isdir(cat_dir):
                continue
            files = [f for f in os.listdir(cat_dir) if f.endswith(".md") and f != "README.md"]
            items = []
            for fn in sorted(files):
                path = os.path.join(cat_dir, fn)
                text = common.read_text(path) or ""
                title = fn.rsplit("_", 1)[0].replace("_", " ") if "_" in fn else fn[:-3]
                mtime = os.path.getmtime(path)
                import datetime
                updated = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                items.append({"title": title, "path": path, "updated": updated,
                              "size": os.path.getsize(path)})
            out.append({"category": cat, "items": items})
        return out

    @app.get("/api/memory")
    def memory(path: str):
        """读取单条记忆"""
        if not path or not os.path.exists(path):
            return {"error": "文件不存在"}
        text = common.read_text(path)
        return {"path": path, "content": text,
                "timeline": memory_engine.timeline(path)}

    @app.post("/api/search")
    def search(req: SearchReq):
        results = memory_engine.semantic_search(req.query, req.limit, req.scope)
        for r in results:
            memory_engine.record_hit(r["path"])
        return {"results": results}

    @app.get("/api/hot")
    def hot(limit: int = 10):
        return {"hot": memory_engine.hot_memories(limit)}

    @app.post("/api/resolve")
    def resolve():
        result = memory_engine.resolve_conflicts()
        return result

    @app.post("/api/coordinator")
    def coordinator(req: CoordReq):
        """后台线程运行调度器"""
        import subprocess
        c = common.cfg()
        script = os.path.join(c["root"], "scripts", "coordinator.py")
        if not os.path.exists(script):
            # 打包环境: scripts 与包同目录
            script = os.path.join(str(SCRIPTS), "coordinator.py")
        result = {"started": True, "log": []}

        def run():
            try:
                cmd = [sys.executable, script] + (["--full"] if req.full else [])
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=600)
                result["log"] = (r.stdout or "").splitlines()[-50:]
                result["exit"] = r.returncode
                result["done"] = True
            except Exception as e:
                result["log"] = [f"ERROR: {e}"]
                result["done"] = True

        threading.Thread(target=run, daemon=True).start()
        return result

    @app.get("/api/msgs")
    def msgs(inbox: str = None):
        import msg
        return {"messages": msg.list_msgs(inbox)}

    @app.post("/api/msg")
    def send_msg(req: MsgSendReq):
        import msg
        mid = msg.send(req.to, req.title, req.body)
        return {"id": mid}

    @app.post("/api/msg/read")
    def read_msg(req: MsgReadReq):
        import msg
        r = msg.read_msg(req.id)
        return r or {"error": "消息不存在"}

    @app.get("/api/ais")
    def ais():
        c = common.cfg()
        return {"ais": list(c["ais"].keys())}

    return app
