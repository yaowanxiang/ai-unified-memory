# -*- coding: utf-8 -*-
"""
common.py — AI Unified Memory 公共工具库
纯标准库实现，无第三方依赖。所有脚本共享此模块。
"""
import os
import sys
import json
import hashlib
import datetime
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cfg():
    with open(os.path.join(ROOT, "CONFIG.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    return datetime.datetime.now().strftime("%Y%m%d")

def log(msg, level="INFO"):
    ts = now_str()
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    logs_dir = os.path.join(ROOT, cfg()["logs"])
    os.makedirs(logs_dir, exist_ok=True)
    logfile = os.path.join(logs_dir, f"coordinator_{today_str()}.log")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def content_hash(text):
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()[:16]

def read_text(path):
    """读取文本，自动处理 UTF-8 / UTF-16 编码。"""
    if not os.path.exists(path):
        return None
    for enc in ("utf-8-sig", "utf-16", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def read_status():
    return load_json(os.path.join(ROOT, cfg()["status_file"]), {})

def save_status(status):
    save_json(os.path.join(ROOT, cfg()["status_file"]), status)

def pub_dir():
    return os.path.join(ROOT, cfg()["public_lib"])

def priv_dir(ai_name=None):
    base = os.path.join(ROOT, cfg()["private_lib"])
    return base if ai_name is None else os.path.join(base, ai_name)

def split_sections(text):
    """把记忆文本按空行/段落切成条目列表。"""
    lines = text.splitlines()
    sections, cur = [], []
    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            if cur:
                sections.append("\n".join(cur))
                cur = []
            continue
        cur.append(ln)
    if cur:
        sections.append("\n".join(cur))
    return [s for s in sections if len(s.strip()) > 3]

def classify_category(text):
    """打分制分类：每个分类统计关键词命中数，取最高分。"""
    t = text
    rules = [
        ("00_用户画像", ["姚老师", "yaowanxiang", "教授", "高校教师", "姓名", "称呼", "名字", "怎么称呼"]),
        ("01_项目知识", ["股票", "决策大脑", "AI Function Library", "项目", "课题", "皮肤癌", "PV/T", "虚拟交易", "记忆库", "四极一击", "论文", "科研"]),
        ("02_领域知识", ["建筑", "节能", "热舒适", "可再生能源", "医学", "金融", "机器学习", "深度学习", "领域", "研究"]),
        ("03_技能工具", ["skill", "技能", "工具", "MCP", "cron", "脚本", "GitHub", "仓库", "install", "python"]),
        ("04_经验教训", ["教训", "黄金法则", "铁律", "禁止", "绝不", "注意", "避免", "修复", "失败", "错误"]),
        ("05_决策记录", ["决策", "决定", "选择", "策略", "规划", "目标", "计划"]),
    ]
    best, best_score = "02_领域知识", 0
    for cat, keywords in rules:
        score = sum(t.count(kw) for kw in keywords)
        if score > best_score:
            best, best_score = cat, score
    return best

def memo_header(title, source_ai, category, tags="", summary=""):
    ts = now_str()
    return (f"---\n"
            f"title: {title}\n"
            f"source_ai: {source_ai}\n"
            f"category: {category}\n"
            f"tags: {tags}\n"
            f"summary: {summary}\n"
            f"created: {ts}\n"
            f"updated: {ts}\n"
            f"---\n\n")

def safe_filename(title, maxlen=40):
    title = re.sub(r'[\\/:*?"<>|#]', '_', title).strip()
    return title[:maxlen] or "untitled"

if __name__ == "__main__":
    print("common.py OK, ROOT =", ROOT)
