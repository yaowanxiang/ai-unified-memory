# -*- coding: utf-8 -*-
"""
msg.py — 交换区消息工具：跨AI消息传递（调度协调机制核心）
各AI通过 INBOX/OUTBOX 传递任务、知识、请求，实现无缝衔接。

用法:
  python msg.py send --to Codex --title "帮我查资料" --body "内容..."
  python msg.py list [--inbox Codex]
  python msg.py read --id <消息ID> [--mark-read]
"""
import os
import sys
import uuid
import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, log, write_text, read_text, now_str, load_json, save_json

def msg_dir():
    c = cfg()
    return os.path.join(c["root"], c["exchange"])

def send(to_ai, title, body, from_ai="调度中心"):
    c = cfg()
    if to_ai not in c["ais"]:
        log(f"[消息] 未知接收方: {to_ai}", "ERROR")
        return None
    mid = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:6]
    inbox = os.path.join(msg_dir(), "INBOX", to_ai)
    os.makedirs(inbox, exist_ok=True)
    content = (f"---\nid: {mid}\nfrom: {from_ai}\nto: {to_ai}\n"
               f"time: {now_str()}\nstatus: unread\ntitle: {title}\n---\n\n{body}\n")
    path = os.path.join(inbox, f"{mid}.md")
    write_text(path, content)
    log(f"[消息] {from_ai} → {to_ai}: {title} ({path})")
    return mid

def list_msgs(inbox_ai=None):
    c = cfg()
    base = os.path.join(msg_dir(), "INBOX")
    if not os.path.isdir(base):
        return []
    out = []
    for ai in (os.listdir(base) if not inbox_ai else [inbox_ai]):
        ai_dir = os.path.join(base, ai)
        if not os.path.isdir(ai_dir):
            continue
        for fn in sorted(os.listdir(ai_dir)):
            if not fn.endswith(".md"):
                continue
            text = read_text(os.path.join(ai_dir, fn)) or ""
            title = ""
            status = "unread"
            for ln in text.splitlines():
                if ln.startswith("title:"):
                    title = ln.split(":", 1)[1].strip()
                if ln.startswith("status:"):
                    status = ln.split(":", 1)[1].strip()
            out.append({"id": fn.replace(".md", ""), "to": ai, "title": title,
                        "status": status, "path": os.path.join(ai_dir, fn)})
    return out

def read_msg(mid, mark_read=True):
    c = cfg()
    base = os.path.join(msg_dir(), "INBOX")
    for ai in os.listdir(base):
        path = os.path.join(base, ai, f"{mid}.md")
        if os.path.exists(path):
            text = read_text(path)
            if mark_read:
                text = text.replace("status: unread", "status: read")
                write_text(path, text)
            return {"path": path, "content": text}
    return None

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == "send":
        to = args[args.index("--to") + 1] if "--to" in args else None
        title = args[args.index("--title") + 1] if "--title" in args else "无标题"
        body = args[args.index("--body") + 1] if "--body" in args else ""
        if not to:
            print("需要 --to <AI名>")
            return 1
        mid = send(to, title, body)
        print(f"✅ 消息已发送: {mid}")
    elif cmd == "list":
        inbox_ai = args[args.index("--inbox") + 1] if "--inbox" in args else None
        msgs = list_msgs(inbox_ai)
        print(f"\n📮 消息列表 ({len(msgs)} 条):\n")
        for m in msgs:
            icon = "🔴" if m["status"] == "unread" else "⚪"
            print(f"{icon} [{m['to']}] {m['id']} | {m['title']}")
    elif cmd == "read":
        mid = args[1] if len(args) > 1 else None
        mark = "--no-mark" not in args
        if not mid:
            print("需要消息ID")
            return 1
        r = read_msg(mid, mark)
        if r:
            print(r["content"])
        else:
            print(f"未找到消息: {mid}")
    else:
        print(__doc__)
    return 0

if __name__ == "__main__":
    sys.exit(main())
