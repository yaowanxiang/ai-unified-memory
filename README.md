# AI Unified Memory (AUM) — Shared Memory Across Multiple AI Agents

> **One memory warehouse, many AI agents. Public library + private libraries + cross-AI messaging + fully automated scheduler.**
>
> **一个记忆仓库，多个 AI 共享。公用库 + 专有库 + AI 间消息 + 全自动调度器。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen.svg)](tests/)
[![CI](https://github.com/yaowanxiang/ai-unified-memory/actions/workflows/ci.yml/badge.svg)](https://github.com/yaowanxiang/ai-unified-memory/actions)
![Zero dependencies](https://img.shields.io/badge/deps-0-brightgreen)

---

## English Introduction

### What it is

When you run multiple AI agents (Hermes, Codex, OpenClaw, Qoder, WorkBuddy, Claude Code…), each one keeps its own private memory. The result:

- ❌ **Knowledge silos**: what one AI learned is invisible to the others
- ❌ **Repetition**: every AI re-learns the same user preferences and project facts
- ❌ **No coordination**: no way to pass messages, tasks, or lessons between AIs
- ❌ **No evolution**: memory never gets deduplicated, categorized, or versioned

**AUM** turns scattered per-AI memories into one **shared, evolving, self-maintaining** memory system:

- ✅ **Public Library** — authoritative shared memory (user profile, project knowledge, domain knowledge, lessons learned, decisions), categorized & deduplicated
- ✅ **Private Libraries** — per-AI mirrors of raw memories + an auto-generated **injection file** each AI reads at session start
- ✅ **Exchange Area** — INBOX/OUTBOX messaging between AIs (task dispatch, notifications)
- ✅ **Scheduler** — one command runs the full loop: **scan → promote → dispatch → index → snapshot**
- ✅ **Zero third-party dependencies** — pure Python standard library, runs anywhere

### Key Features

- 🔄 **One-click sync**: scan → promote → dispatch → index → snapshot, fully automated
- 🔍 **Cross-library search**: full-text keyword search across public + private + exchange
- 📊 **Memory stats**: live file statistics for every library
- 🖥️ **Graphical client**: no coding required — download an installer, double-click and go
- 🧠 **Auto-maintenance**: global dedup, keyword-scored auto-classification, daily snapshots
- 💬 **Cross-AI messaging**: send/read messages between AIs via INBOX/OUTBOX
- 📦 **Zero dependencies**: pure Python standard library, no pip install needed

### Installers (Graphical Client)

**No programming required — download, double-click, done:**

| Platform | Download |
|----------|----------|
| 🪟 Windows | `AI-Unified-Memory-Windows.exe` (download & run) |
| 🍎 macOS | `AI-Unified-Memory-macOS` (App) |
| 🐧 Linux | `AI-Unified-Memory-Linux.AppImage` |

**GUI features:**
- 🔄 **One-click sync**: scan → promote → dispatch → index → snapshot, fully automatic
- 🔍 **Search memory**: keyword search across all libraries
- 📊 **Memory library status**: per-library file statistics at a glance
- ⚡ Dark professional theme; every operation is a single click

> All the complex sync/classify/dispatch logic runs in the background — the user only needs to **click one button**.

#### Developer Mode

```bash
python gui_app.py                     # launch the GUI
python scripts/coordinator.py --full  # or full sync from the command line
```

### Quick Start

```bash
# 1. Copy config template and fill in your AI memory source paths
cp CONFIG.example.json CONFIG.json

# 2. Run the full synchronization loop (scan → promote → dispatch → index → snapshot)
python scripts/coordinator.py --full

# 3. Search shared memory on demand
python scripts/search.py "user profile" --limit 10

# 4. Cross-AI messaging
python scripts/msg.py send --to Codex --title "Please review" --body "..."
python scripts/msg.py list
python scripts/msg.py read <message-id>
```

### Architecture

```
                     ┌───────────────────────────────────┐
                     │         coordinator.py            │
                     │  scan → promote → dispatch → snap │
                     └───────┬───────────────┬───────────┘
                             │               │
              ┌──────────────▼──┐   ┌────────▼───────────┐
              │  01_公用库       │   │ 02_专有库           │
              │  Public Library │   │ Private Libraries  │
              │  (authoritative)│   │  Hermes/ Codex/    │
              │  6 categories   │   │  OpenClaw/ Qoder…  │
              └──────────────┬──┘   └────────┬───────────┘
                             │               │
              ┌──────────────▼──┐   ┌────────▼───────────┐
              │ 03_交换区        │   │ 04_快照备份         │
              │ Exchange        │   │ Daily snapshots    │
              │ INBOX/OUTBOX    │   │ (versioned)        │
              └─────────────────┘   └────────────────────┘
```

**Memory flow:**

```
Any AI produces new memory → memory source changes
        ↓
[scheduler] coordinator.py
    scan_all.py   → capture changed memories into private libs (_scanned/)
    promote.py    → global dedup + auto-classify → write to public lib
    dispatch.py   → regenerate each AI's "shared memory injection" file
    build_index   → refresh memory index
    snapshot      → daily backup of public lib
        ↓
Each AI session start → read own 02_专有库/<AI>/共享记忆注入.md
Need details        → python scripts/search.py <keyword>
Cross-AI message    → python scripts/msg.py send --to Codex --title "..." --body "..."
```

### Components

| Script | Role |
|--------|------|
| `coordinator.py` | Full pipeline orchestrator (scan→promote→dispatch→index→snapshot) |
| `scan_all.py` | Scan each AI's memory source (file-list mode or recursive `.md` mode) |
| `promote.py` | Global-hash dedup + keyword scoring classification → public library |
| `dispatch.py` | Generate per-AI "shared memory injection" files |
| `search.py` | Full-text search across public + private + exchange |
| `msg.py` | INBOX/OUTBOX cross-AI messaging (send / list / read) |
| `common.py` | Shared utilities (UTF-8/UTF-16 tolerant reading, hashing, logging) |

### Public Library Categories

| Category | Contents |
|----------|----------|
| `00_用户画像` | User profile (who is the user, preferences, working style) |
| `01_项目知识` | Project knowledge (active projects, status, collaborators) |
| `02_领域知识` | Domain knowledge (research fields, technical domains) |
| `03_技能工具` | Skills & tools (libraries, MCP servers, tool registries) |
| `04_经验教训` | Lessons learned (golden rules, pitfalls, fixes) |
| `05_决策记录` | Decision records (ADR-style, why decisions were made) |
| `06_记忆索引` | Auto-generated index |

### Adding a New AI

1. Add an entry in `CONFIG.json` under `ais` (memory source path + files)
2. Run `python scripts/coordinator.py --full`
3. Done — the new AI gets its own private lib + injection file, and starts sharing memory

### Scheduling (recommended)

```bash
# incremental: every 2 hours
python scripts/coordinator.py

# full sync + snapshot: daily at 03:00
python scripts/coordinator.py --full
```

Integrate with any cron scheduler (Windows Task Scheduler, systemd, Hermes cron, GitHub Actions).

### Use Cases

- **Multi-agent households**: Hermes + Codex + OpenClaw + Qoder + WorkBuddy + Claude Code all share one memory warehouse
- **Personal knowledge base**: user profile, project knowledge, and lessons learned survive across sessions and tools
- **Team knowledge**: one authoritative public library, every AI reads the same injected memory at session start
- **Automated memory ops**: scheduled scan/promote/dispatch keeps the warehouse clean without manual effort

### License

MIT — free for personal and commercial use. See [LICENSE](LICENSE).

---

# 🇨🇳 中文版介绍

## 🎯 这是什么？

同时运行多个 AI Agent（Hermes、Codex、OpenClaw、Qoder、WorkBuddy、Claude Code…）时，每个 AI 都只拥有自己的私有记忆，结果是：

- ❌ **知识孤岛**：一个 AI 学到的东西，其他 AI 完全看不到
- ❌ **重复劳动**：每个 AI 都要重新学习相同的用户偏好和项目事实
- ❌ **无法协作**：AI 之间没有办法传递消息、任务或经验
- ❌ **没有进化**：记忆永远不会被去重、分类或版本化

**AUM** 把散落在各 AI 的记忆整合成一套**共享、持续进化、自动维护**的记忆系统：

- ✅ **公用库** —— 权威共享记忆（用户画像、项目知识、领域知识、经验教训、决策记录），自动分类与去重
- ✅ **专有库** —— 每个 AI 的原始记忆镜像 + 自动生成的**注入文件**（AI 每次会话启动时读取）
- ✅ **交换区** —— AI 之间的 INBOX/OUTBOX 消息（任务派发、通知）
- ✅ **调度器** —— 一条命令跑完整流程：**扫描 → 提升 → 分发 → 索引 → 快照**
- ✅ **零第三方依赖** —— 纯 Python 标准库，随处可跑

## 💻 图形化客户端（傻瓜式，拿来就用）

**无需编程，下载安装包双击即用：**

| 平台 | 下载 |
|------|------|
| 🪟 Windows | `AI-Unified-Memory-Windows.exe` (下载即运行) |
| 🍎 macOS | `AI-Unified-Memory-macOS` (App) |
| 🐧 Linux | `AI-Unified-Memory-Linux.AppImage` |

**界面功能：**
- 🔄 **一键同步**：扫描→提升→分发→索引→快照 全自动
- 🔍 **搜索记忆**：跨全库关键词检索
- 📊 **记忆库状态**：各库文件统计一目了然
- ⚡ 深色专业主题，全部操作一键完成

> 复杂的同步/分类/分发逻辑全部在后台自动运行，用户只需**点一个按钮**。

### 开发者模式

```bash
python gui_app.py                # 启动图形界面
python scripts/coordinator.py --full   # 或命令行全量同步
```

## ✨ 核心特性

- 🔄 **一键同步**：扫描 → 提升 → 分发 → 索引 → 快照，全自动流水线
- 🔍 **跨库搜索**：公用库 + 专有库 + 交换区全文本关键词检索
- 📊 **记忆统计**：各库文件实时统计
- 🖥️ **图形化客户端**：无需编程，下载安装包双击即用
- 🧠 **自动维护**：全局去重、关键词评分自动分类、每日快照备份
- 💬 **AI 间消息**：通过 INBOX/OUTBOX 在 AI 之间发送/读取消息
- 📦 **零依赖**：纯 Python 标准库，无需 pip 安装任何包

## 🚀 快速开始

```bash
# 1. 复制配置模板，填写各 AI 记忆源路径
cp CONFIG.example.json CONFIG.json

# 2. 运行全量同步循环（扫描 → 提升 → 分发 → 索引 → 快照）
python scripts/coordinator.py --full

# 3. 按需搜索共享记忆
python scripts/search.py "用户画像" --limit 10

# 4. AI 间消息
python scripts/msg.py send --to Codex --title "请审阅" --body "..."
python scripts/msg.py list
python scripts/msg.py read <消息ID>
```

## 🏗 架构

```
                     ┌───────────────────────────────────┐
                     │         coordinator.py            │
                     │  scan → promote → dispatch → snap │
                     └───────┬───────────────┬───────────┘
                             │               │
              ┌──────────────▼──┐   ┌────────▼───────────┐
              │  01_公用库       │   │ 02_专有库           │
              │  Public Library │   │ Private Libraries  │
              │  (authoritative)│   │  Hermes/ Codex/    │
              │  6 categories   │   │  OpenClaw/ Qoder…  │
              └──────────────┬──┘   └────────┬───────────┘
                             │               │
              ┌──────────────▼──┐   ┌────────▼───────────┐
              │ 03_交换区        │   │ 04_快照备份         │
              │ Exchange        │   │ Daily snapshots    │
              │ INBOX/OUTBOX    │   │ (versioned)        │
              └─────────────────┘   └────────────────────┘
```

**记忆流转流程：**

```
任意 AI 产生新记忆 → 记忆源发生变化
        ↓
[调度器] coordinator.py
    scan_all.py   → 将变更记忆采集进各专有库 (_scanned/)
    promote.py    → 全局去重 + 自动分类 → 写入公用库
    dispatch.py   → 重新生成各 AI 的「共享记忆注入」文件
    build_index   → 刷新记忆索引
    snapshot      → 每日备份公用库
        ↓
各 AI 会话启动 → 读取自己的 02_专有库/<AI>/共享记忆注入.md
需要详情        → python scripts/search.py <关键词>
AI 间消息       → python scripts/msg.py send --to Codex --title "..." --body "..."
```

## 🔧 组件说明

| 脚本 | 职责 |
|------|------|
| `coordinator.py` | 全流程编排器（扫描→提升→分发→索引→快照） |
| `scan_all.py` | 扫描各 AI 记忆源（文件列表模式或递归 `.md` 模式） |
| `promote.py` | 全局哈希去重 + 关键词评分分类 → 写入公用库 |
| `dispatch.py` | 生成各 AI 的「共享记忆注入」文件 |
| `search.py` | 公用库 + 专有库 + 交换区全文本搜索 |
| `msg.py` | INBOX/OUTBOX 跨 AI 消息（发送 / 列表 / 读取） |
| `common.py` | 共享工具（UTF-8/UTF-16 容错读取、哈希、日志） |

## 📂 公用库分类

| 分类 | 内容 |
|------|------|
| `00_用户画像` | 用户是谁、偏好、工作方式 |
| `01_项目知识` | 进行中的项目、状态、协作者 |
| `02_领域知识` | 研究领域、技术方向 |
| `03_技能工具` | 代码库、MCP 服务器、工具注册表 |
| `04_经验教训` | 金规、踩坑记录、修复方案 |
| `05_决策记录` | ADR 风格决策记录（为什么这么做） |
| `06_记忆索引` | 自动生成的索引 |

## 🤝 接入新的 AI

1. 在 `CONFIG.json` 的 `ais` 下添加条目（记忆源路径 + 文件）
2. 运行 `python scripts/coordinator.py --full`
3. 完成 —— 新 AI 自动获得专属专有库 + 注入文件，开始共享记忆

## ⏰ 定时调度（推荐）

```bash
# 增量同步：每 2 小时
python scripts/coordinator.py

# 全量同步 + 快照：每天 03:00
python scripts/coordinator.py --full
```

可接入任意定时器（Windows 任务计划程序、systemd、Hermes cron、GitHub Actions）。

## 🎯 使用场景

- **多 Agent 家庭**：Hermes + Codex + OpenClaw + Qoder + WorkBuddy + Claude Code 共享同一个记忆仓库
- **个人知识库**：用户画像、项目知识、经验教训跨会话、跨工具永久留存
- **团队知识沉淀**：一个权威公用库，每个 AI 会话启动时读取同一份注入记忆
- **记忆自动化运维**：定时扫描/提升/分发，无需人工维护仓库整洁

## 📄 许可证

MIT —— 个人与商业使用均免费。详见 [LICENSE](LICENSE)。

---

*The memory of many AIs, unified. Each AI learns once — every AI benefits.*
*众多 AI 的记忆，归于一体。每个 AI 只学一次——所有 AI 共同受益。*
