# Architecture: Memory System Overhaul (v2.9)

**Domain:** OpenClaw QMD memory backend — compaction, indexing, retrieval, and daily log system
**Researched:** 2026-03-08
**Confidence:** HIGH (live system introspection via SSH), MEDIUM (OpenClaw internals)

---

## Current System State (Verified via SSH)

Before designing fixes, the actual system state was measured. Every finding below is from direct EC2 observation.

```
EC2 (100.72.143.9) — t3.small, 2GB RAM + 2GB swap
|
+-- OpenClaw v2026.3.2 (gateway on loopback :18789)
|   +-- Config: ~/.openclaw/openclaw.json
|   +-- memory.backend: "qmd"
|   +-- memorySearch.provider: "gemini" (Gemini embeddings as fallback)
|   +-- compaction.mode: "safeguard"
|   +-- compaction.reserveTokensFloor: 24000
|   +-- compaction.memoryFlush.softThresholdTokens: 1500   <-- BROKEN
|   +-- agents.defaults.contextTokens: 100000
|
+-- QMD v1.1.0 (at ~/.bun/bin/qmd)
|   +-- Index: ~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite (3.2MB)
|   +-- Models: embeddinggemma-300M + qmd-query-expansion-1.7B
|   +-- Config: ~/.openclaw/agents/main/qmd/xdg-config/index.yml
|   +-- searchMode: "search" (BM25, avoids slow LLM reranker)
|   +-- Update interval: 15m
|
+-- QMD Collections (3 auto-created per agent)
|   +-- memory-root-main: path ~/clawd/agents/main, pattern MEMORY.md  [0 files]
|   +-- memory-alt-main:  path ~/clawd/agents/main, pattern memory.md  [0 files]
|   +-- memory-dir-main:  path ~/clawd/agents/main/memory, **/*.md     [21 files]
|   NOTE: memory-root-main and memory-alt-main match NOTHING (no files fit patterns)
|   NOTE: memory-dir-main IS indexed but points to WRONG location (see below)
|
+-- Workspace Mounts
|   +-- agents.defaults.workspace: /home/ubuntu/clawd
|   +-- Docker maps workspace root to /workspace/ inside container
|   +-- So /workspace/memory/ inside container = ~/clawd/memory/ on host
|
+-- CRITICAL DISCREPANCY: Two memory directories exist
|   +-- ~/clawd/memory/             (3 files, Jan 25-29 — old format, PRE-YOLO)
|   +-- ~/clawd/agents/main/memory/ (21 files, Feb 2 - Mar 7 — CURRENT, all recent)
|   QMD indexes ~/clawd/agents/main/memory/ (matches what agents actually write to)
|   But the Docker workspace maps to ~/clawd/memory/ (which agents DON'T write to)
|
+-- Daily Memory Flush (cron: daily-memory-flush, 7 AM UTC, isolated session)
|   +-- Writes to: memory/YYYY-MM-DD.md (relative to /workspace/)
|   +-- Resolved host path: ~/clawd/agents/main/memory/ (confirmed by file evidence)
|   +-- Status: WORKING — writes thin files (3-65 lines) since compaction rarely fires
|   +-- Files are thin because: built-in compaction flush almost never triggers
|   +-- The cron flush IS reliable: 20 of 21 memory files are from cron
|
+-- MEMORY.md (long-term seed file)
|   +-- ~/clawd/MEMORY.md (3057 bytes, Feb 23) — exists but NOT indexed
|   +-- QMD memory-root-main looks for MEMORY.md in ~/clawd/agents/main/ — wrong path
|   +-- MEMORY.md needs to exist in ~/clawd/agents/main/ to be found
|
+-- compaction.memoryFlush (built-in session flush — BROKEN)
|   +-- mode: "safeguard" with reserveTokensFloor: 24000
|   +-- softThresholdTokens: 1500 = fires when < 1500 tokens remain after pruning
|   +-- Math: 24000 (reserve floor) - 1500 (threshold) = 22500 tokens used before flush
|   +-- In practice: most sessions never reach 22500 tokens of reserved context
|   +-- Result: built-in flush almost never fires; memory-flush prompt is effectively dead
```

---

## System Architecture: Memory Data Flow (Current State)

```
                    WRITE PATH (how memories enter the system)

User interacts -> Bob (main agent) -> session context accumulates
                                           |
                            compaction fires at contextTokens=100000
                                           |
                            safeguard mode: prune to reserveTokensFloor=24000
                                           |
                            IF remaining < softThresholdTokens (1500):
                              fire memoryFlush prompt -> write memory/*.md
                              [THIS ALMOST NEVER HAPPENS: threshold is too low]
                                           |
                                           v
                            daily-memory-flush cron (7 AM UTC, isolated)
                              reads DAILY_FLUSH.md from /workspace/
                              queries coordination.db, email.db, content.db
                              writes memory/YYYY-MM-DD.md to /workspace/memory/
                              [THIS IS THE ACTUAL WORKING PATH]

                    INDEX PATH (how memories get into QMD)

~/clawd/agents/main/memory/*.md
          |
          | QMD update every 15m (onBoot: true)
          v
memory-dir-main collection (21 files indexed, 3.2MB index)
          |
          | BM25 search (qmd search mode)
          v
    search results (scored, ranked)

                    READ PATH (how Bob retrieves memories)

Agent session starts
          |
          | OpenClaw injects QMD search results into context
          | (memorySearch.provider: gemini triggers fallback search path)
          | QMD is primary backend, Gemini embeddings as secondary
          v
Bob's context includes memory snippets at session start
```

---

## Recommended Architecture

### System Overview

```
+------------------------------------------------------------------------+
|                        MEMORY SYSTEM (Target State)                    |
+------------------------------------------------------------------------+
|                                                                        |
|  WRITE LAYER                  INDEX LAYER         READ LAYER          |
|                                                                        |
|  +------------------+         +----------+      +------------------+  |
|  | Built-in Flush   |         |          |      |                  |  |
|  | (fixed threshold)|-------> |   QMD    |----> | Agent context    |  |
|  +------------------+         | v1.1.0   |      | at session start |  |
|                               |          |      |                  |  |
|  +------------------+         | Index:   |      | Bob reads mem    |  |
|  | daily-memory-    |-------> | memory/  |      | via tool call    |  |
|  | flush cron       |         | *.md     |      | (protocol doc)   |  |
|  +------------------+         |          |      +------------------+  |
|                               | MEMORY.md|                            |
|  +------------------+         | (seeded) |      +------------------+  |
|  | MEMORY.md        |-------> |          |      | Memory health    |  |
|  | (long-term seed) |         +----------+      | monitoring cron  |  |
|  +------------------+              |            | (daily report)   |  |
|                                    |            +------------------+  |
|  Per-agent:                        | Update                           |
|  ~/clawd/agents/main/memory/  <----+ every 15m                        |
|  ~/clawd/agents/main/MEMORY.md                                        |
+------------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `compaction.memoryFlush` | In-session flush when context fills — write session summary to memory/ | BROKEN (threshold too low) |
| `daily-memory-flush` cron | Daily isolated cron — writes structured YYYY-MM-DD.md from DB queries | WORKING (thin files only) |
| QMD memory-dir-main | Indexes memory/*.md every 15m, provides BM25 search | WORKING |
| QMD memory-root-main | Should index MEMORY.md — currently indexes 0 files (wrong path) | BROKEN |
| MEMORY.md seed | Long-term curated knowledge base about Andy and the system | EXISTS but not indexed |
| Retrieval protocol | AGENTS.md instruction to search memory before acting | MISSING |
| Memory health monitoring | Verify memory files are being written with adequate content | MISSING |

---

## Integration Points: QMD + Gemini + memorySearch

This is the most complex part of the system — two memory backends with overlapping roles.

### How QMD and Gemini Interact

```
openclaw.json:
  memory.backend: "qmd"           <- PRIMARY backend: QMD handles storage + indexing
  agents.defaults.memorySearch:
    provider: "gemini"            <- SEARCH overlay: Gemini embeddings for retrieval
    model: "gemini-embedding-001"

config.yaml (user-level override):
  memorySearch:
    experimental:
      sessionMemory:
        enabled: true
        sources: [memory, sessions]
```

**What this means:**
- QMD is the indexing and storage system (21 files indexed, BM25 working)
- Gemini embeddings are configured as the retrieval provider — this may mean Gemini generates the embeddings used DURING search, even though QMD indexes the files
- The `experimental.sessionMemory.enabled: true` in config.yaml activates session-history search alongside file-based memory search
- These two layers are complementary, not conflicting. QMD indexes the files; Gemini (optionally) enhances retrieval quality

**Confidence: MEDIUM** — OpenClaw's internal routing between QMD and Gemini memorySearch is not publicly documented. The observed behavior (QMD search returns results) suggests QMD is functioning as primary.

### Correct Config Structure for Both

```json
// memory block: configures QMD storage backend
"memory": {
  "backend": "qmd",
  "citations": "auto",
  "qmd": {
    "command": "/home/ubuntu/.bun/bin/qmd",
    "searchMode": "search",          // BM25 only (avoids slow LLM reranker on t3.small)
    "includeDefaultMemory": true,
    "update": {
      "interval": "15m",
      "debounceMs": 15000,
      "onBoot": true
    },
    "limits": {
      "maxResults": 6,
      "timeoutMs": 8000
    }
  }
}

// memorySearch block: configures HOW retrieval queries are formed/ranked
// Gemini generates embedding vectors for similarity matching
// Keep this — removing it risks degrading retrieval quality
"agents": {
  "defaults": {
    "memorySearch": {
      "provider": "gemini",
      "model": "gemini-embedding-001"
    }
  }
}
```

**Rule:** Do NOT remove the Gemini memorySearch config. It is a retrieval enhancement on top of QMD storage. If Gemini API is unavailable, QMD BM25 still works (degraded but functional).

---

## Critical Path Analysis: What's Broken and Why

### Issue 1: Built-in compaction flush never fires (HIGH IMPACT)

**Root cause:** `softThresholdTokens: 1500` is the number of tokens remaining in the reserved floor before flush triggers. With `reserveTokensFloor: 24000`, the flush fires only when 22,500+ tokens of the reserved window are consumed. In normal sessions (heartbeats, briefings), this threshold is never reached.

**Math:**
```
contextTokens = 100,000
reserveTokensFloor = 24,000
softThresholdTokens = 1,500

Compaction triggers at: 100,000 - 24,000 = 76,000 tokens used
Flush triggers at: reserveFloor (24,000) - softThreshold (1,500) = 22,500 tokens used in resumed context

=> Flush fires only in extremely long sessions (rare heartbeats or user conversations)
```

**Fix:** Raise `softThresholdTokens` to 6,000-10,000. This makes the flush trigger when 14,000-18,000 tokens remain in the reserved window — much more frequent. Previous config used 6,000 (visible in .bak files).

```json
"compaction": {
  "mode": "safeguard",
  "reserveTokensFloor": 24000,
  "memoryFlush": {
    "enabled": true,
    "softThresholdTokens": 8000,   // was 1500; fires at ~16000 tokens consumed in resume
    ...
  }
}
```

### Issue 2: MEMORY.md not indexed by QMD (MEDIUM IMPACT)

**Root cause:** QMD `memory-root-main` collection looks for `MEMORY.md` in `~/clawd/agents/main/`. The file exists at `~/clawd/MEMORY.md` (the workspace root). No MEMORY.md exists at the path QMD searches.

**Fix (two options):**
- Option A: Copy/move MEMORY.md to `~/clawd/agents/main/MEMORY.md` — QMD picks it up automatically
- Option B: Update QMD collection path in `~/.openclaw/agents/main/qmd/xdg-config/index.yml` to point to `~/clawd/` instead of `~/clawd/agents/main/`

**Recommendation: Option A.** The agent workspace is `~/clawd/agents/main/` (where all reference docs live — AGENTS.md, SOUL.md, HEARTBEAT.md). MEMORY.md should live there too. The file at `~/clawd/MEMORY.md` is a legacy location from before per-agent workspaces were established.

### Issue 3: Daily flush writes thin files (LOW-MEDIUM IMPACT)

**Root cause:** The `daily-memory-flush` cron fires at 7 AM UTC (before morning session activity). It only captures what happened "yesterday" — but most substantive interactions happen DURING the day, not before 7 AM.

**Observed evidence:** March 3, 4, 5, 6 files are 3-5 lines ("Quiet day — routine cron operations only."). March 7 is 23 lines (had real activity). The flush IS working, but captures minimal content on low-activity days.

**Fix:** The flush works correctly. The content quality problem is the compaction flush not firing during sessions. Once the built-in flush fires more frequently, the daily cron captures substantive session summaries written during the day.

### Issue 4: No retrieval protocol in AGENTS.md (MEDIUM IMPACT)

**Root cause:** Bob has no explicit instruction to search memory before answering questions or taking actions. QMD search is available and working, but without a protocol, Bob uses memory opportunistically rather than systematically.

**Fix:** Add a "Memory Retrieval Protocol" section to `~/clawd/AGENTS.md` with explicit instructions to run a memory search at session start and before major actions.

---

## File Path Architecture

### Host Paths (on EC2)

```
/home/ubuntu/
+-- .openclaw/
|   +-- openclaw.json          <- Main config (compaction, QMD backend)
|   +-- config.yaml            <- User-level config (sessionMemory experimental)
|   +-- agents/
|       +-- main/
|           +-- qmd/
|               +-- xdg-config/
|               |   +-- index.yml    <- QMD collection definitions
|               |   +-- qmd/
|               +-- xdg-cache/
|                   +-- qmd/
|                       +-- index.sqlite  <- 3.2MB, 21 files indexed
+-- clawd/                     <- agents.defaults.workspace
|   +-- MEMORY.md              <- EXISTS but not indexed (wrong location)
|   +-- agents/
|   |   +-- main/
|   |       +-- MEMORY.md      <- NEEDS TO EXIST (QMD indexes this)
|   |       +-- AGENTS.md      <- Needs memory protocol section
|   |       +-- memory/        <- QMD-indexed daily log files (21 files, working)
|   |       |   +-- 2026-02-02.md
|   |       |   +-- ...
|   |       |   +-- 2026-03-07.md
|   |       +-- DAILY_FLUSH.md <- Reference doc for daily-memory-flush cron
|   +-- memory/                <- OLD location (3 files, Jan 2026) — stale
```

### Container Paths (inside Docker sandbox)

```
/workspace/                    <- maps to /home/ubuntu/clawd/
                                  (agents.defaults.workspace = /home/ubuntu/clawd)
+-- [all ~/clawd/ contents available]
+-- memory/                    <- maps to ~/clawd/memory/ (OLD dir, stale)
                                  CAUTION: daily-memory-flush writes to memory/YYYY-MM-DD.md
                                  which resolves to /workspace/memory/ = ~/clawd/memory/ ???
```

**CRITICAL DISCREPANCY INVESTIGATION:**
The cron runs as an isolated session for agent `main`. Despite `agents.defaults.workspace: /home/ubuntu/clawd`, the cron log confirms files land in `~/clawd/agents/main/memory/` not `~/clawd/memory/`. This means OpenClaw resolves the workspace per-agent, and `main` agent's effective workspace is `~/clawd/agents/main/`.

**Confirmed architecture (from file evidence):**
```
Agent "main" effective workspace = ~/clawd/agents/main/
Docker /workspace/ = ~/clawd/agents/main/
memory/ inside container = ~/clawd/agents/main/memory/   [QMD indexes this — CORRECT]
DAILY_FLUSH.md in container = ~/clawd/agents/main/DAILY_FLUSH.md  [confirmed: file exists there]
MEMORY.md needs to be at = ~/clawd/agents/main/MEMORY.md  [currently missing]
```

### QMD Collection Path Mapping

```
index.yml:
  memory-root-main:
    path: /home/ubuntu/clawd/agents/main    <- workspace root
    pattern: MEMORY.md                       <- matches MEMORY.md in root
    files: 0                                 <- MISSING: need ~/clawd/agents/main/MEMORY.md

  memory-alt-main:
    path: /home/ubuntu/clawd/agents/main    <- workspace root
    pattern: memory.md                       <- matches lowercase memory.md
    files: 0                                 <- lowercase variant unused

  memory-dir-main:
    path: /home/ubuntu/clawd/agents/main/memory  <- memory/ subdirectory
    pattern: **/*.md                         <- all .md files recursively
    files: 21                                <- WORKING — daily logs indexed
```

### Docker Bind-Mounts (Current)

The memory directory is NOT explicitly bind-mounted (confirmed: no memory-related binds in openclaw.json). It is accessible because the entire agent workspace is the Docker container's /workspace/ mount. This means:
- No bind-mount needed for memory/ reads or writes
- memory/ files are persistent (host filesystem, not container ephemeral layer)
- Permissions: `rw-rw-r--` (664) — ubuntu user can write, world-readable

---

## What Is New vs Modified

| Component | Action | Why |
|-----------|--------|-----|
| `compaction.softThresholdTokens` in openclaw.json | **MODIFY**: 1500 → 8000 | Fix built-in flush so it fires in real sessions |
| `compaction.memoryFlush.prompt` in openclaw.json | **MODIFY**: improve prompt | Current prompt good but can be sharper |
| `~/clawd/agents/main/MEMORY.md` | **CREATE**: seed with curated knowledge | Enables memory-root-main collection to index it |
| `~/clawd/MEMORY.md` | **DECOMMISSION**: move content to agent workspace | Consolidate to indexed location |
| `~/clawd/agents/main/AGENTS.md` | **MODIFY**: add retrieval protocol | Tell Bob to search memory before acting |
| `~/.openclaw/cron/jobs.json` | **MODIFY**: daily-memory-flush timing | Move from 7 AM UTC to end-of-day (e.g. 23:00 UTC) |
| `~/clawd/agents/main/DAILY_FLUSH.md` | **MODIFY**: update to capture richer content | Include voice notes, user interactions, not just DB queries |
| Memory health monitoring cron | **CREATE**: new cron job | Verify memory files are being written with content |
| `~/clawd/agents/main/BOOTSTRAP.md` | **MODIFY**: add memory verification steps | Ensure QMD index is healthy at boot |

**No gateway restart needed for most changes.** Compaction config in openclaw.json requires a gateway restart. Everything else (MEMORY.md content, AGENTS.md additions, DAILY_FLUSH.md edits) takes effect in the next session.

---

## Data Flow: Memory Write → Index → Search

```
SESSION FLUSH PATH (in-session compaction):

Bob's context accumulates during conversation
          |
          v [when contextTokens - usedTokens < reserveTokensFloor]
OpenClaw compaction fires (mode: safeguard)
          |
          v [when remaining_in_reserve < softThresholdTokens]
memoryFlush.prompt injected as system message:
  "Session nearing compaction. Store durable memories now."
          |
          v
Bob executes memoryFlush.prompt:
  "Write a structured session summary to memory/$(date +%Y-%m-%d).md"
          |
          v [Bob writes file via bash/tool calls]
~/clawd/agents/main/memory/YYYY-MM-DD.md (appended if exists)

DAILY CRON FLUSH PATH:

Cron fires: daily-memory-flush (7 AM UTC, isolated session)
          |
          v
Bob reads /workspace/DAILY_FLUSH.md for instructions
          |
          v [Bob queries coordination.db, email.db, content.db]
Bob writes /workspace/memory/YYYY-MM-DD.md
   = ~/clawd/agents/main/memory/YYYY-MM-DD.md

QMD INDEX UPDATE PATH:

~/clawd/agents/main/memory/YYYY-MM-DD.md (new or updated)
          |
          | QMD update every 15m (debounce 15s after file change)
          v
memory-dir-main collection re-indexed
index.sqlite updated (BM25 + embeddings)
          |
~/clawd/agents/main/MEMORY.md
          |
          | QMD update picks up (after file created)
          v
memory-root-main collection: 1 file indexed

RETRIEVAL PATH:

Agent session starts (heartbeat or user DM)
          |
          v [OpenClaw injects memory context]
QMD search fires (BM25 via qmd search)
Gemini embeddings enhance query vectors
          |
          v
Top-6 memory snippets injected into Bob's context
          |
Bob follows retrieval protocol (from AGENTS.md):
  "Search memory before answering questions about preferences,
   history, or past decisions"
          |
          v
Relevant memory surfaced in response
```

---

## Build Order: Dependencies Between Fixes

```
STEP 1: Fix compaction threshold (gateway restart required)
  - Edit openclaw.json: softThresholdTokens 1500 → 8000
  - Optionally improve memoryFlush.prompt
  - Restart gateway: systemctl --user restart openclaw-gateway.service
  DEPENDS ON: Nothing
  RISK: Gateway restart clears DM sessions (known pitfall)
  MITIGATION: Do this at low-activity time; DM Bob after restart

STEP 2: Create MEMORY.md in agent workspace (no restart needed)
  - Write ~/clawd/agents/main/MEMORY.md with curated long-term knowledge
  - Source content from ~/clawd/MEMORY.md (move, don't duplicate)
  - QMD auto-indexes within 15m (onBoot not needed)
  DEPENDS ON: Nothing (can run parallel with Step 1)
  RISK: None

STEP 3: Update AGENTS.md with retrieval protocol (no restart needed)
  - Add "Memory Retrieval Protocol" section
  - Fires in next Bob session automatically
  DEPENDS ON: Step 2 (MEMORY.md should exist before protocol references it)
  RISK: Low — AGENTS.md changes take effect immediately

STEP 4: Reschedule daily-memory-flush to end-of-day (no restart needed)
  - Change cron schedule from "0 7 * * *" to "0 23 * * *" (3 PM PT / 11 PM UTC)
  - This captures the day's activity rather than the previous day's sparse data
  DEPENDS ON: Nothing
  RISK: One day of overlap/gap during transition

STEP 5: Add memory health monitoring cron (no restart needed)
  - Create a weekly cron that verifies: file count, file sizes, QMD index freshness
  - Reports to #popsclaw: "Memory health: 7 files this week, avg 15 lines, QMD fresh"
  DEPENDS ON: Steps 1-4 (monitoring is only useful after fixes are in place)
  RISK: None — read-only diagnostic cron
```

**Why this order:** Step 1 (compaction fix) is the most impactful and requires the only gateway restart — do it first to batch the disruption. Steps 2-3 build the indexed knowledge base Bob can retrieve. Step 4 improves the quality of what gets indexed. Step 5 validates the entire system.

---

## Architectural Patterns to Follow

### Pattern 1: QMD Collection Targeting (Established v2.9 research)

QMD auto-creates three collections per agent on first boot. The collection paths and patterns are controlled by `~/.openclaw/agents/{id}/qmd/xdg-config/index.yml`. Do NOT manually edit index.yml — it is managed by OpenClaw. Instead, ensure files exist at the paths QMD expects:

```
memory-root-main: ~/clawd/agents/{id}/MEMORY.md      <- create this file
memory-dir-main:  ~/clawd/agents/{id}/memory/*.md    <- daily-memory-flush writes here
```

### Pattern 2: Compaction Flush Prompt as Tool Call Instructions

The `memoryFlush.prompt` is executed as an agent instruction when compaction fires. Bob treats it as a task: he must write a file to disk. The prompt must be specific about the path (`memory/$(date +%Y-%m-%d).md`) and format. The existing prompt is well-structured; increase `softThresholdTokens` to make it fire.

### Pattern 3: Reference Doc Pattern for Cron Instructions

`DAILY_FLUSH.md` follows the established reference doc pattern (same as MEETING_PREP.md, HEARTBEAT.md, PUBLISH_SESSION.md). The cron payload message is concise ("Follow DAILY_FLUSH.md"); the detailed instructions live in the workspace doc. Do not put long SQL queries in the cron payload.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Adding MEMORY.md to ~/clawd/ Root (Wrong Layer)

**What happens:** MEMORY.md at `~/clawd/MEMORY.md` is in the workspace root that ALL agents share. QMD creates per-agent collections that look in `~/clawd/agents/{id}/`. A file in the root is not indexed.

**Do this instead:** `~/clawd/agents/main/MEMORY.md` is the correct location. Per-agent MEMORY.md files allow different agents to have different long-term context.

### Anti-Pattern 2: Setting softThresholdTokens Too High

**What happens:** If `softThresholdTokens` is set too close to `reserveTokensFloor` (e.g., 20,000 of 24,000), the flush fires at nearly every context turn — excessive, wastes tokens writing session summaries every few messages.

**Sweet spot:** 6,000-10,000. Fires when a session is substantive (1,500-18,000 tokens consumed in the resumed context window).

### Anti-Pattern 3: Bind-Mounting memory/ Explicitly

**What happens:** Adding `~/clawd/agents/main/memory:/workspace/memory:rw` to docker binds creates a conflict — the workspace mount already covers this path. Nested bind-mounts in isolated cron sessions are unreliable (documented pitfall from YOLO Dev work).

**Do this instead:** Leave memory/ without an explicit bind-mount. It inherits read-write access from the agent workspace mount.

### Anti-Pattern 4: Removing Gemini memorySearch Config

**What happens:** The `memorySearch.provider: gemini` and `experimental.sessionMemory.enabled: true` are retrieval enhancements. Removing them does not "simplify" the system — it may degrade retrieval quality or break session-history search.

**Do this instead:** Keep both QMD (storage/indexing) and Gemini (retrieval enhancement) configured. They are complementary. If Gemini is unavailable, QMD BM25 still works.

### Anti-Pattern 5: Relying Solely on the Built-in Flush for Memory

**What happens:** The built-in compaction flush is designed for in-session memory — it only fires during active long conversations. Heartbeat crons (haiku model, short turns) rarely accumulate enough context to trigger it.

**Do this instead:** Keep BOTH the daily cron flush AND the in-session compaction flush. The cron flush is the reliable daily baseline; the compaction flush captures rich session summaries during intensive work sessions.

---

## Scalability Considerations

This is a personal single-agent memory system. "Scaling" means: what happens at 1 year of daily logs?

| Concern | Now (21 files) | At 6 months (180 files) | At 1 year (365 files) |
|---------|----------------|------------------------|----------------------|
| QMD index size | 3.2 MB | ~25 MB | ~50 MB |
| Index query time | <1s | <2s | <3s |
| Memory file discovery | Instant | Instant | Fast |
| maxResults relevance | High | High | May need increase to 8 |
| t3.small RAM | No issue | No issue | Monitor if QMD reranker enabled |

**First bottleneck:** If QMD's LLM reranker is ever enabled (`searchMode: "query"` instead of `"search"`), the Qwen3-Reranker-0.6B model adds ~500MB RAM and 3-5s latency per search. Keep `searchMode: "search"` on t3.small indefinitely.

**When to worry:** If `qmd status` shows Pending > 0 for more than 30 minutes, the background indexer is slow. This hasn't been observed yet.

---

## Sources

### HIGH confidence (direct EC2 observation, 2026-03-08)
- SSH session output: openclaw.json full config, QMD status, collection listing, index.yml
- `qmd status`: 21 files indexed, 3 collections, update timestamps
- `qmd search "morning briefing"`: verified BM25 search returns results
- `ls ~/clawd/agents/main/memory/`: 21 files, Mar 7 most recent (yesterday)
- `cron/runs/d7041540-*.jsonl`: daily-memory-flush cron confirms writes to memory/
- File timestamps confirm effective agent workspace is `~/clawd/agents/main/`

### MEDIUM confidence (inferred from OpenClaw behavior)
- Relationship between `memory.backend: qmd` and `memorySearch.provider: gemini`
- Exact trigger conditions for compaction.memoryFlush in safeguard mode
- How `experimental.sessionMemory.enabled: true` interacts with QMD retrieval

### LOW confidence (needs verification)
- Whether softThresholdTokens refers to tokens remaining in reserveFloor or absolute context
- Whether Gemini embeddings are used alongside QMD BM25 or as alternative
- Per-agent workspace isolation mechanism (inferred from file evidence, not docs)

---

*Architecture research for: pops-claw v2.9 Memory System Overhaul*
*Researched: 2026-03-08*
*Replaces: previous ARCHITECTURE.md covering v2.7 YOLO Dev*
