---
title: "AI Unified Memory: Shared Persistent Memory Across Multiple AI Agents"
authors: "Yao Wanxiang"
affiliation: "Qingdao University of Technology"
date: 2026-08-18
---

# AI Unified Memory (AUM): Shared Persistent Memory Across Multiple AI Agents

**Yao Wanxiang** · Qingdao University of Technology

---

## Abstract

Modern users increasingly operate multiple AI agents (coding assistants, research
orchestrators, skill ecosystems) that each maintain private, siloed memory. Knowledge
learned by one agent is invisible to others, forcing users to repeat preferences,
project facts, and lessons across tools. This paper presents **AI Unified Memory (AUM)**,
a filesystem-native framework that unifies per-agent memory into one shared,
self-maintaining warehouse. AUM separates an **authoritative public library** (categorized,
deduplicated shared memory) from **per-AI private libraries** (raw memory mirrors plus
auto-generated injection files read at session start), connects agents through an
**exchange area** for cross-AI messaging, and automates the full lifecycle with a
single-command scheduler that runs *scan → promote → dispatch → index → snapshot*.
The implementation is pure Python standard library (zero third-party dependencies),
making it portable across Windows/macOS/Linux and any agent that can read files. We
describe the architecture, the deduplication and classification pipeline, the injection
mechanism, and provide a fully open-source reference implementation.

---

## 1. Introduction

AI agents have become multi-tool ecosystems: coding assistants (Codex, Claude Code,
Qoder), research orchestrators (Hermes), and skill libraries (OpenClaw). Each tool
persists memory in its own format and location — markdown files, SQLite, or structured
directories. This fragmentation creates three problems:

- **Knowledge silos**: a pitfall learned in one agent never reaches others.
- **Redundant learning**: every agent independently re-learns the same user profile,
  project facts, and golden rules.
- **No coordination channel**: there is no standard way to pass a task, a notification,
  or a lesson from one agent to another.

AUM addresses these with a simple, dependency-free, file-based architecture that any
agent can adopt by reading one markdown file at session start and writing memory to a
well-known directory.

## 2. Architecture

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

### 2.1 Public Library (authoritative)

Shared memory is organized into six categories — user profile, project knowledge,
domain knowledge, skills & tools, lessons learned, decision records — plus an
auto-generated index. Each entry is a markdown file with YAML frontmatter
(`source_ai`, `category`, `tags`, `summary`, timestamps).

### 2.2 Private Libraries (per-AI mirrors)

Each AI keeps: (a) `_scanned/` — raw snapshots of its memory source captured by the
scanner, and (b) an auto-generated **shared-memory injection file** listing the current
public library highlights. An agent joins the system by reading its own injection file
at session start; no code modification to the agent is required.

### 2.3 Exchange Area (cross-AI messaging)

INBOX/OUTBOX directories plus a message index enable task dispatch and notification
between agents: `send --to <AI> --title <t> --body <b>`, `list`, `read`.

### 2.4 Scheduler (full automation)

`coordinator.py` runs the complete lifecycle:

1. **scan** — capture changed memory files from each AI's source (fixed-file or
   recursive `.md` mode);
2. **promote** — global content-hash deduplication, keyword-scoring auto-classification,
   write into the public library;
3. **dispatch** — regenerate every AI's injection file;
4. **index** — rebuild the memory index;
5. **snapshot** — versioned daily backup of the public library.

## 3. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Filesystem-native (no database) | Portable, diffable, greppable, version-controllable; agents read/write files natively |
| Public library as authority | Single source of truth; private libs are disposable mirrors |
| Content-hash dedup | Idempotent scans; timestamps excluded from hashes to avoid duplicates |
| Keyword-scoring classification | Deterministic, zero-dependency, transparent |
| Injection file per AI | Zero-integration adoption: read one markdown file, done |

## 4. Adoption

Adding a new AI is a two-step process: register its memory source in `CONFIG.json`,
then run `coordinator.py --full`. The system automatically creates the private library
and injection file. Recommended scheduling: incremental sync every two hours plus a
full sync with snapshot daily — each is a single command, suitable for any cron
scheduler (Windows Task Scheduler, systemd, GitHub Actions, agent-native cron).

## 5. Related Work

Existing agent-memory systems (e.g., per-agent markdown memory, SQLite-backed memory,
vector stores) optimize single-agent recall. AUM targets the **multi-agent** setting:
cross-agent sharing, deduplication across sources, and a coordination channel are its
primary contributions, achieved with zero dependencies and a full automation loop.

## 6. Conclusion

AUM demonstrates that multi-agent shared memory does not require infrastructure. A
discipline of public/private separation, content-hash dedup, injection files, and an
automated coordinator delivers cross-agent learning, unified recall, and full
automation in ~500 lines of pure-standard-library Python.

## Availability

- Code: https://github.com/yaowanxiang/ai-unified-memory (MIT License)
- Companion framework: https://github.com/yaowanxiang/model-router
  (cost-aware multi-LLM routing with free-first fallback chains)
