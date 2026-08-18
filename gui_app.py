#!/usr/bin/env python3
"""
AI Unified Memory 图形化客户端 v2.0 - 多AI共享记忆管理仪表盘
功能: 记忆浏览(分类树) / 语义检索(memory_engine) / 一键同步 / 冲突消解 /
      热记忆 / 跨AI消息 / 时间线 / 统计面板
技术: 纯 tkinter 标准库,零第三方依赖,三平台可打包
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

FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:
    BASE_DIR = Path(sys._MEIPASS)
    MEMORY_ROOT = Path.home() / ".ai-unified-memory"
    SCRIPT_DIR = BASE_DIR / "scripts"
else:
    BASE_DIR = Path(__file__).resolve().parent
    MEMORY_ROOT = BASE_DIR
    SCRIPT_DIR = BASE_DIR / "scripts"

CATS = ["00_用户画像", "01_项目知识", "02_领域知识",
        "03_技能工具", "04_经验教训", "05_决策记录"]


class MemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 AI统一记忆中心 v2.0 - 多AI共享记忆")
        self.root.geometry("1000x720")
        self.root.minsize(880, 620)

        self.bg = "#0f172a"
        self.bg2 = "#1e293b"
        self.bg3 = "#0b1220"
        self.fg = "#f8fafc"
        self.accent = "#38bdf8"
        self.green = "#10b981"
        self.purple = "#a78bfa"
        self.orange = "#f59e0b"
        self.red = "#ef4444"
        self.root.configure(bg=self.bg)

        # 左侧导航
        self._build_sidebar()
        # 右侧 Notebook 页
        self._build_pages()
        self._build_statusbar()
        self._init_script_paths()

    def _init_script_paths(self):
        # 打包后 CONFIG.json 初始化
        if FROZEN:
            MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
            cfg_file = MEMORY_ROOT / "CONFIG.json"
            if not cfg_file.exists():
                ex = BASE_DIR / "CONFIG.example.json"
                if ex.exists():
                    import shutil
                    shutil.copy(ex, cfg_file)
            for d in ("01_公用库", "02_专有库", "03_交换区/INBOX",
                      "03_交换区/OUTBOX", "04_快照备份", "00_调度中心"):
                (MEMORY_ROOT / d).mkdir(parents=True, exist_ok=True)

    def _build_sidebar(self):
        side = tk.Frame(self.root, bg=self.bg2, width=190)
        side.pack(side=tk.LEFT, fill=tk.Y)
        side.pack_propagate(False)

        tk.Label(side, text="🧠 记忆中心", font=("Microsoft YaHei", 14, "bold"),
                 bg=self.bg2, fg=self.fg).pack(pady=(18, 4))
        tk.Label(side, text="v2.0 · 零依赖", font=("Microsoft YaHei", 9),
                 bg=self.bg2, fg=self.accent).pack(pady=(0, 14))

        btns = [
            ("📚 记忆浏览", self._load_browse),
            ("🔍 语义检索", lambda: self.notebook.select(1)),
            ("⚙️ 一键同步", self._run_sync),
            ("🧹 冲突消解", self._run_resolve),
            ("🔥 热记忆", self._load_hot),
            ("📮 跨AI消息", self._load_msgs),
            ("📊 统计面板", self._show_stats),
        ]
        for text, cmd in btns:
            b = tk.Button(side, text=text, command=cmd, bg=self.bg2, fg=self.fg,
                          font=("Microsoft YaHei", 11), relief=tk.FLAT,
                          anchor=tk.W, padx=18, pady=9, cursor="hand2",
                          activebackground=self.accent, activeforeground="#0f172a")
            b.pack(fill=tk.X)

        tk.Label(side, text="\n纯Python标准库\n三平台可打包", font=("Microsoft YaHei", 8),
                 bg=self.bg2, fg="#64748b").pack(side=tk.BOTTOM, pady=12)

    def _build_pages(self):
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 页1: 记忆浏览
        self.tab_browse = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(self.tab_browse, text="📚 记忆浏览")
        self._build_browse_tab()

        # 页2: 语义检索
        self.tab_search = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(self.tab_search, text="🔍 语义检索")
        self._build_search_tab()

        # 页3: 消息
        self.tab_msg = tk.Frame(self.notebook, bg=self.bg)
        self.notebook.add(self.tab_msg, text="📮 跨AI消息")
        self._build_msg_tab()

    # ============ 记忆浏览页 ============
    def _build_browse_tab(self):
        top = tk.Frame(self.tab_browse, bg=self.bg)
        top.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(top, text="公用库记忆（6大分类）", font=("Microsoft YaHei", 12, "bold"),
                 bg=self.bg, fg=self.fg).pack(side=tk.LEFT)
        tk.Button(top, text="刷新", command=self._load_browse, bg=self.accent,
                  fg="#0f172a", font=("Microsoft YaHei", 10, "bold"),
                  relief=tk.FLAT, padx=12, cursor="hand2").pack(side=tk.RIGHT)

        body = tk.Frame(self.tab_browse, bg=self.bg)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.cat_list = tk.Listbox(body, bg=self.bg2, fg=self.fg,
                                   font=("Microsoft YaHei", 10),
                                   selectbackground=self.accent,
                                   selectforeground="#0f172a", relief=tk.FLAT,
                                   highlightthickness=0, width=24)
        self.cat_list.pack(side=tk.LEFT, fill=tk.Y)
        self.cat_list.bind("<<ListboxSelect>>", self._on_cat_select)

        self.mem_list = tk.Listbox(body, bg=self.bg3, fg="#e2e8f0",
                                   font=("Microsoft YaHei", 10),
                                   selectbackground=self.purple,
                                   selectforeground="white", relief=tk.FLAT,
                                   highlightthickness=0)
        self.mem_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        self.mem_list.bind("<<ListboxSelect>>", self._on_mem_select)
        self.mem_list.bind("<Double-Button-1>", lambda e: self._view_mem_full())

        self.mem_view = scrolledtext.ScrolledText(
            body, font=("Microsoft YaHei", 9), bg=self.bg3, fg="#e2e8f0",
            insertbackground="#e2e8f0", relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground="#334155")
        self.mem_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        self.mem_view.configure(state=tk.DISABLED)

        self._load_browse()

    def _load_browse(self):
        def work():
            out = {}
            for cat in CATS:
                cat_dir = MEMORY_ROOT / "01_公用库" / cat
                files = []
                if cat_dir.is_dir():
                    for f in sorted(cat_dir.glob("*.md")):
                        if f.name != "README.md":
                            files.append(f)
                out[cat] = files
            self.root.after(0, lambda: self._fill_browse(out))
        threading.Thread(target=work, daemon=True).start()

    def _fill_browse(self, out):
        self.cat_list.delete(0, tk.END)
        self._browse_data = out
        for cat in CATS:
            n = len(out.get(cat, []))
            self.cat_list.insert(tk.END, f"{cat} ({n})")

    def _on_cat_select(self, evt):
        sel = self.cat_list.curselection()
        if not sel:
            return
        cat = CATS[sel[0]]
        self.mem_list.delete(0, tk.END)
        self._cur_cat_files = self._browse_data.get(cat, [])
        for f in self._cur_cat_files:
            self.mem_list.insert(tk.END, f.name)

    def _on_mem_select(self, evt):
        sel = self.mem_list.curselection()
        if not sel or not hasattr(self, "_cur_cat_files"):
            return
        path = self._cur_cat_files[sel[0]]
        self._show_mem_preview(path)

    def _show_mem_preview(self, path):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = "无法读取"
        self.mem_view.configure(state=tk.NORMAL)
        self.mem_view.delete("1.0", tk.END)
        self.mem_view.insert(tk.END, text[:6000])
        self.mem_view.configure(state=tk.DISABLED)

    def _view_mem_full(self):
        sel = self.mem_list.curselection()
        if not sel or not hasattr(self, "_cur_cat_files"):
            return
        path = self._cur_cat_files[sel[0]]
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = "无法读取"
        win = tk.Toplevel(self.root)
        win.title(f"📄 {path.name}")
        win.geometry("700x600")
        win.configure(bg=self.bg3)
        t = scrolledtext.ScrolledText(win, font=("Microsoft YaHei", 10),
                                      bg=self.bg3, fg="#e2e8f0", wrap=tk.WORD)
        t.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        t.insert(tk.END, text)

    # ============ 语义检索页 ============
    def _build_search_tab(self):
        top = tk.Frame(self.tab_search, bg=self.bg)
        top.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(top, text="关键词（支持同义词扩展 + TF加权）:",
                 font=("Microsoft YaHei", 10), bg=self.bg, fg=self.fg).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(top, font=("Microsoft YaHei", 11),
                                     bg=self.bg3, fg=self.fg,
                                     insertbackground=self.fg, relief=tk.FLAT,
                                     highlightthickness=1,
                                     highlightbackground=self.accent, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self.search_entry.bind("<Return>", lambda e: self._search())
        tk.Button(top, text="语义检索", command=self._search, bg=self.accent,
                  fg="#0f172a", font=("Microsoft YaHei", 11, "bold"),
                  relief=tk.FLAT, padx=16, cursor="hand2").pack(side=tk.LEFT)

        self.search_scope = ttk.Combobox(top, values=["public", "all", "private"],
                                         state="readonly", width=8)
        self.search_scope.set("public")
        self.search_scope.pack(side=tk.LEFT, padx=8)

        self.search_result = scrolledtext.ScrolledText(
            self.tab_search, font=("Microsoft YaHei", 10), bg=self.bg3,
            fg="#e2e8f0", insertbackground="#e2e8f0", relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground="#334155")
        self.search_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.search_result.configure(state=tk.DISABLED)
        self.search_result.tag_configure("hit", foreground="#38bdf8")
        self.search_result.tag_configure("path", foreground="#94a3b8")

    def _search(self):
        kw = self.search_entry.get().strip()
        if not kw:
            messagebox.showwarning("提示", "请输入关键词")
            return

        def work():
            try:
                script = SCRIPT_DIR / "memory_engine.py"
                args = [str(script), "search", kw, "--limit", "15",
                        "--scope", self.search_scope.get()]
                r = subprocess.run([sys.executable] + args, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace",
                                   timeout=120)
                output = r.stdout or r.stderr or "无结果"
                self.root.after(0, lambda: self._show_search(output))
            except Exception as e:
                self.root.after(0, lambda: self._show_search(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _show_search(self, text):
        self.search_result.configure(state=tk.NORMAL)
        self.search_result.delete("1.0", tk.END)
        self.search_result.insert(tk.END, text)
        self.search_result.configure(state=tk.DISABLED)

    # ============ 跨AI消息页 ============
    def _build_msg_tab(self):
        left = tk.Frame(self.tab_msg, bg=self.bg2, padx=12, pady=12)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(left, text="📨 发送消息", font=("Microsoft YaHei", 12, "bold"),
                 bg=self.bg2, fg=self.fg).pack(anchor=tk.W)
        tk.Label(left, text="接收AI:", bg=self.bg2, fg="#94a3b8",
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W, pady=(10, 2))
        self.msg_to = ttk.Combobox(left, values=["Hermes", "Codex", "OpenClaw",
                                                 "Qoder", "WorkBuddy", "ClaudeCode"],
                                   state="normal", width=24)
        self.msg_to.set("Codex")
        self.msg_to.pack()
        tk.Label(left, text="标题:", bg=self.bg2, fg="#94a3b8",
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W, pady=(8, 2))
        self.msg_title = tk.Entry(left, bg=self.bg3, fg=self.fg,
                                  insertbackground=self.fg, relief=tk.FLAT,
                                  highlightthickness=1, highlightbackground=self.accent)
        self.msg_title.pack(fill=tk.X, ipady=3)
        tk.Label(left, text="内容:", bg=self.bg2, fg="#94a3b8",
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W, pady=(8, 2))
        self.msg_body = tk.Text(left, height=6, bg=self.bg3, fg=self.fg,
                                insertbackground=self.fg, relief=tk.FLAT,
                                highlightthickness=1, highlightbackground=self.accent)
        self.msg_body.pack(fill=tk.X)
        tk.Button(left, text="📤 发送", command=self._send_msg, bg=self.green,
                  fg="white", font=("Microsoft YaHei", 11, "bold"),
                  relief=tk.FLAT, pady=6, cursor="hand2").pack(fill=tk.X, pady=(10, 0))

        right = tk.Frame(self.tab_msg, bg=self.bg)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Button(right, text="🔄 刷新收件箱", command=self._load_msgs, bg=self.purple,
                  fg="white", font=("Microsoft YaHei", 10, "bold"),
                  relief=tk.FLAT, padx=12, cursor="hand2").pack(anchor=tk.W)
        self.msg_list = tk.Listbox(right, bg=self.bg3, fg="#e2e8f0",
                                   font=("Microsoft YaHei", 10), relief=tk.FLAT,
                                   highlightthickness=0, height=6)
        self.msg_list.pack(fill=tk.X, pady=(6, 4))
        self.msg_list.bind("<Double-Button-1>", lambda e: self._read_msg())
        self.msg_view = scrolledtext.ScrolledText(
            right, font=("Microsoft YaHei", 10), bg=self.bg3, fg="#e2e8f0",
            insertbackground="#e2e8f0", relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground="#334155")
        self.msg_view.pack(fill=tk.BOTH, expand=True)
        self.msg_view.configure(state=tk.DISABLED)
        self._load_msgs()

    def _send_msg(self):
        to = self.msg_to.get().strip()
        title = self.msg_title.get().strip()
        body = self.msg_body.get("1.0", tk.END).strip()
        if not to or not title:
            messagebox.showwarning("提示", "请填写接收AI和标题")
            return

        def work():
            try:
                script = SCRIPT_DIR / "msg.py"
                r = subprocess.run([sys.executable, str(script), "send",
                                    "--to", to, "--title", title, "--body", body],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                self.root.after(0, lambda: messagebox.showinfo(
                    "发送", "✅ 消息已发送" if r.returncode == 0 else f"❌ {r.stderr}"))
                self.msg_title.delete(0, tk.END)
                self.msg_body.delete("1.0", tk.END)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _load_msgs(self):
        def work():
            try:
                script = SCRIPT_DIR / "msg.py"
                r = subprocess.run([sys.executable, str(script), "list"],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                lines = (r.stdout or "").splitlines()
                self.root.after(0, lambda: self._fill_msgs(lines))
            except Exception as e:
                self.root.after(0, lambda: self._fill_msgs([f"错误: {e}"]))
        threading.Thread(target=work, daemon=True).start()

    def _fill_msgs(self, lines):
        self.msg_list.delete(0, tk.END)
        self._msg_ids = {}
        for ln in lines:
            if "🔴" in ln or "⚪" in ln:
                self.msg_list.insert(tk.END, ln)
                parts = ln.split("|")
                if len(parts) > 1:
                    mid = parts[1].strip().split()[0]
                    self._msg_ids[self.msg_list.size() - 1] = mid

    def _read_msg(self):
        sel = self.msg_list.curselection()
        if not sel or not hasattr(self, "_msg_ids"):
            return
        mid = self._msg_ids.get(sel[0])
        if not mid:
            return

        def work():
            try:
                script = SCRIPT_DIR / "msg.py"
                r = subprocess.run([sys.executable, str(script), "read", mid],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                text = r.stdout or r.stderr or "读取失败"
                self.root.after(0, lambda: self._show_msg(text))
            except Exception as e:
                self.root.after(0, lambda: self._show_msg(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _show_msg(self, text):
        self.msg_view.configure(state=tk.NORMAL)
        self.msg_view.delete("1.0", tk.END)
        self.msg_view.insert(tk.END, text)
        self.msg_view.configure(state=tk.DISABLED)

    # ============ 快捷操作 ============
    def _run_script(self, *args, label="操作"):
        def work():
            try:
                script = SCRIPT_DIR / "coordinator.py"
                cmd = [sys.executable, str(script)] + list(args)
                self.root.after(0, lambda: self.status.config(text=f"⏳ {label}中…"))
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=600)
                tail = (r.stdout or r.stderr or "").splitlines()[-8:]
                self.root.after(0, lambda: self._show_msg(
                    f"⚡ {label} {'完成 ✅' if r.returncode == 0 else '失败 ❌'}\n" + "\n".join(tail)))
                self.root.after(0, lambda: self.status.config(text=f"{label}完成"))
            except Exception as e:
                self.root.after(0, lambda: self._show_msg(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _run_sync(self):
        self._run_script("--full", label="一键同步")

    def _run_resolve(self):
        def work():
            try:
                script = SCRIPT_DIR / "memory_engine.py"
                r = subprocess.run([sys.executable, str(script), "resolve"],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=120)
                self.root.after(0, lambda: self._show_msg(r.stdout or r.stderr or "完成"))
            except Exception as e:
                self.root.after(0, lambda: self._show_msg(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _load_hot(self):
        def work():
            try:
                script = SCRIPT_DIR / "memory_engine.py"
                r = subprocess.run([sys.executable, str(script), "hot", "--limit", "15"],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                self.root.after(0, lambda: self._show_msg(r.stdout or "暂无热记忆"))
            except Exception as e:
                self.root.after(0, lambda: self._show_msg(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _show_stats(self):
        def work():
            try:
                lines = ["📊 记忆库统计\n"]
                total = 0
                for cat in CATS:
                    cat_dir = MEMORY_ROOT / "01_公用库" / cat
                    n = len(list(cat_dir.glob("*.md"))) if cat_dir.is_dir() else 0
                    total += n
                    lines.append(f"  {cat}: {n} 条")
                lines.append(f"\n  合计: {total} 条公用记忆")
                # 专有库
                priv = MEMORY_ROOT / "02_专有库"
                if priv.is_dir():
                    lines.append("\n  专有库:")
                    for d in sorted(priv.iterdir()):
                        if d.is_dir():
                            n = len(list(d.glob("*.md")))
                            lines.append(f"    {d.name}: {n} 文件")
                self.root.after(0, lambda: self._show_msg("\n".join(lines)))
            except Exception as e:
                self.root.after(0, lambda: self._show_msg(f"错误: {e}"))
        threading.Thread(target=work, daemon=True).start()

    # ============ 状态栏 ============
    def _build_statusbar(self):
        self.status = tk.Label(self.root, text="就绪 - 使用左侧导航操作",
                               font=("Microsoft YaHei", 9), bg=self.bg,
                               fg="#94a3b8", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=20, pady=(0, 8))


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
