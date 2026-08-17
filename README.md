# AI Unified Memory (AUM) — Shared Memory Across Multiple AI Agents

> **One memory warehouse, many AI agents. Public library + private libraries + cross-AI messaging + fully automated scheduler.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
![Zero dependencies](https://img.shields.io/badge/deps-0-brightgreen)

## 🎯 Why AUM?

When you run multiple AI agents (Hermes, Codex, OpenClaw, Qoder, WorkBuddy, Claude Code…), each keeps its own private memory. The result:

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

## 🏗 Architecture

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

## 🚀 Quick Start

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

## 🔧 Components

| Script | Role |
|--------|------|
| `coordinator.py` | Full pipeline orchestrator (scan→promote→dispatch→index→snapshot) |
| `scan_all.py` | Scan each AI's memory source (file-list mode or recursive `.md` mode) |
| `promote.py` | Global-hash dedup + keyword scoring classification → public library |
| `dispatch.py` | Generate per-AI "shared memory injection" files |
| `search.py` | Full-text search across public + private + exchange |
| `msg.py` | INBOX/OUTBOX cross-AI messaging (send / list / read) |
| `common.py` | Shared utilities (UTF-8/UTF-16 tolerant reading, hashing, logging) |

## 📂 Public Library Categories

| Category | Contents |
|----------|----------|
| `00_用户画像` | User profile (who is the user, preferences, working style) |
| `01_项目知识` | Project knowledge (active projects, status, collaborators) |
| `02_领域知识` | Domain knowledge (research fields, technical domains) |
| `03_技能工具` | Skills & tools (libraries, MCP servers, tool registries) |
| `04_经验教训` | Lessons learned (golden rules, pitfalls, fixes) |
| `05_决策记录` | Decision records (ADR-style, why decisions were made) |
| `06_记忆索引` | Auto-generated index |

## 🤝 Adding a New AI

1. Add an entry in `CONFIG.json` under `ais` (memory source path + files)
2. Run `python scripts/coordinator.py --full`
3. Done — the new AI gets its own private lib + injection file, and starts sharing memory

## ⏰ Scheduling (recommended)

```bash
# incremental: every 2 hours
python scripts/coordinator.py

# full sync + snapshot: daily at 03:00
python scripts/coordinator.py --full
```

Integrate with any cron scheduler (Windows Task Scheduler, systemd, Hermes cron, GitHub Actions).

## 📄 License

MIT — free for personal and commercial use. See [LICENSE](LICENSE).

---

*The memory of many AIs, unified. Each AI learns once — every AI benefits.*
