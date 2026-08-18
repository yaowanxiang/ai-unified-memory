#!/usr/bin/env python3
"""
AI Unified Memory 图形化客户端 - 多AI共享记忆管理仪表盘
一键同步/扫描/搜索/查看6大AI的记忆库，傻瓜化操作
"""
import os
import sys
import json
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

# 强制UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent / "scripts"
MEMORY_ROOT = Path(__file__).resolve().parent


class MemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 AI统一记忆中心 v1.0.0 - 多AI共享记忆")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.bg = "#0f172a"
        self.bg2 = "#1e293b"
        self.fg = "#f8fafc"
        self.accent = "#38bdf8"
        self.green = "#10b981"
        self.purple = "#a78bfa"
        self.root.configure(bg=self.bg)

        self._build_header()
        self._build_action_panel()
        self._build_search_panel()
        self._build_result_panel()
        self._build_statusbar()

    def _build_header(self):
        h = tk.Frame(self.root, bg=self.bg)
        h.pack(fill=tk.X, padx=20, pady=(15, 5))
        tk.Label(h, text="🧠 AI 统一记忆中心", font=("Microsoft YaHei", 20, "bold"),
                 bg=self.bg, fg=self.fg).pack(side=tk.LEFT)
        tk.Label(h, text="6大AI共享记忆 · 一键同步 · 傻瓜化管理",
                 font=("Microsoft YaHei", 10), bg=self.bg2, fg=self.accent,
                 padx=10, pady=4).pack(side=tk.RIGHT)

    def _build_action_panel(self):
        p = tk.Frame(self.root, bg=self.bg2, padx=15, pady=10)
        p.pack(fill=tk.X, padx=20, pady=8)

        tk.Label(p, text="⚡ 快捷操作（一键完成）", font=("Microsoft YaHei", 11, "bold"),
                 bg=self.bg2, fg=self.fg).pack(anchor=tk.W, pady=(0, 6))

        row = tk.Frame(p, bg=self.bg2)
        row.pack(fill=tk.X)

        self.sync_btn = tk.Button(row, text="🔄 一键同步", command=lambda: self._run_script("--full"),
                                  bg=self.green, fg="white", font=("Microsoft YaHei", 11, "bold"),
                                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2")
        self.sync_btn.pack(side=tk.LEFT)

        tk.Button(row, text="🔍 扫描记忆库", command=lambda: self._run_script("--scan"),
                  bg=self.accent, fg="#0f172a", font=("Microsoft YaHei", 11, "bold"),
                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=8)

        tk.Button(row, text="📊 查看状态", command=self._show_status,
                  bg=self.purple, fg="white", font=("Microsoft YaHei", 11, "bold"),
                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=8)

    def _build_search_panel(self):
        p = tk.Frame(self.root, bg=self.bg2, padx=15, pady=10)
        p.pack(fill=tk.X, padx=20, pady=8)

        tk.Label(p, text="🔎 搜索记忆", font=("Microsoft YaHei", 11, "bold"),
                 bg=self.bg2, fg=self.fg).pack(anchor=tk.W, pady=(0, 5))

        row = tk.Frame(p, bg=self.bg2)
        row.pack(fill=tk.X)
        self.search_entry = tk.Entry(row, font=("Microsoft YaHei", 11),
                                     bg=self.bg, fg=self.fg, insertbackground=self.fg,
                                     relief=tk.FLAT, highlightthickness=1,
                                     highlightbackground=self.accent)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(row, text="搜索", command=self._search,
                  bg=self.accent, fg="#0f172a", font=("Microsoft YaHei", 11, "bold"),
                  relief=tk.FLAT, padx=18, cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))

    def _build_result_panel(self):
        p = tk.Frame(self.root, bg=self.bg2)
        p.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)
        tk.Label(p, text="📋 输出", font=("Microsoft YaHei", 12, "bold"),
                 bg=self.bg2, fg=self.fg).pack(anchor=tk.W, padx=8, pady=(6, 2))
        self.result_text = scrolledtext.ScrolledText(
            p, font=("Microsoft YaHei", 10), bg="#0b1220", fg="#e2e8f0",
            insertbackground="#e2e8f0", relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground="#334155")
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.result_text.configure(state=tk.DISABLED)
        self.result_text.tag_configure("ok", foreground="#10b981")
        self.result_text.tag_configure("err", foreground="#ef4444")
        self.result_text.tag_configure("info", foreground="#38bdf8")

    def _build_statusbar(self):
        self.status = tk.Label(self.root, text="就绪 - 选择操作或输入搜索关键词",
                               font=("Microsoft YaHei", 9), bg=self.bg,
                               fg="#94a3b8", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=20, pady=(0, 8))

    def _run_script(self, flag):
        threading.Thread(target=self._script_worker, args=(flag,), daemon=True).start()

    def _script_worker(self, flag):
        try:
            if flag == "--full":
                script = SCRIPT_DIR / "coordinator.py"
                args = ["--full"]
                label = "一键同步"
            else:
                script = SCRIPT_DIR / "scan_all.py"
                args = []
                label = "扫描记忆库"

            self.root.after(0, lambda: self.status.config(text=f"⏳ 正在{label}…"))
            r = subprocess.run([sys.executable, str(script)] + args,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=300)
            output = r.stdout or r.stderr or "无输出"
            self.root.after(0, lambda: self._show_output(output, label, r.returncode))
        except Exception as e:
            self.root.after(0, lambda: self._show_output(f"错误: {e}", "执行", 1))

    def _show_output(self, output, label, code):
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        tag = "ok" if code == 0 else "err"
        self.result_text.insert(tk.END, f"⚡ {label} {'成功 ✅' if code == 0 else '失败 ❌'}\n\n", tag)
        self.result_text.insert(tk.END, output[:4000])
        self.result_text.configure(state=tk.DISABLED)
        self.status.config(text=f"{label}完成" if code == 0 else f"{label}失败")

    def _search(self):
        kw = self.search_entry.get().strip()
        if not kw:
            messagebox.showwarning("提示", "请输入搜索关键词！")
            return
        threading.Thread(target=self._search_worker, args=(kw,), daemon=True).start()

    def _search_worker(self, kw):
        try:
            script = SCRIPT_DIR / "search.py"
            self.root.after(0, lambda: self.status.config(text=f"⏳ 搜索「{kw}」…"))
            r = subprocess.run([sys.executable, str(script), kw],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
            output = r.stdout or r.stderr or "未找到相关记忆"
            self.root.after(0, lambda: self._show_output(output, f"搜索: {kw}", r.returncode))
        except Exception as e:
            self.root.after(0, lambda: self._show_output(f"错误: {e}", "搜索", 1))

    def _show_status(self):
        threading.Thread(target=self._status_worker, daemon=True).start()

    def _status_worker(self):
        try:
            # 统计记忆库概况
            cats = []
            for d in sorted(MEMORY_ROOT.iterdir()):
                if d.is_dir() and d.name[:2].isdigit():
                    md_files = [f for f in d.rglob("*.md")]
                    cats.append(f"{d.name}: {len(md_files)} 个文件")
            self.root.after(0, lambda: self._show_output("\n".join(cats), "记忆库状态", 0))
        except Exception as e:
            self.root.after(0, lambda: self._show_output(f"错误: {e}", "状态", 1))


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    MemoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
