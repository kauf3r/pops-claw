# Pitfalls Research

**Domain:** OpenClaw memory system repair — QMD bootstrapping, compaction tuning, retrieval enforcement, and memory health monitoring on an existing resource-constrained deployment
**Researched:** 2026-03-08
**Confidence:** HIGH (derived from production history documented in MEMORY.md, known system state documented in PROJECT.md and MEMORY.md, prior milestone PITFALLS.md covering v2.6-era memory work, and direct evidence of current failure modes including zero memory flush files, QMD never bootstrapped, and broken compaction thresholds)

> This file supersedes the v2.7-era PITFALLS.md which covered YOLO Dev overnight builds.
> The v2.6-era pitfalls (MEMORY.md curation, flush thresholds, gateway restart session loss,
> bootstrap truncation, LEARNINGS.md noise) are incorporated and updated here for the v2.9
> memory system overhaul context.

---

## Critical Pitfalls

### Pitfall 1: QMD Appears Configured But Collections Were Never Bootstrapped

**What goes wrong:**
`openclaw.json` has `memory.backend = "qmd"` and all the right config keys. The gateway starts without errors. `openclaw doctor` shows no issues. But when Bob does memory-intensive tasks, nothing is retrieved — because QMD's collections directory is either empty or contains only the 3 auto-created but never-indexed directories. The `memory-dir-main` collection shows 19 files counted but zero embeddings because the initial indexing run that creates embeddings from existing files never completed or never ran. QMD silently falls back to the builtin backend without alerting.

**Why it happens:**
QMD requires two distinct steps: (1) configure the backend in openclaw.json, and (2) trigger the initial embedding run that scans workspace files and populates the vector store. The configuration step alone does not bootstrap collections. The auto-create behavior creates directories and schema but not vectors. If the first embedding run was killed (OOM, timeout, etc.) or never triggered, the collections exist structurally but contain no searchable content.

**How to avoid:**
After any QMD config change or fresh install: (1) verify QMD is actually running with `qmd status`, (2) explicitly trigger a full re-index run, (3) query for known content (e.g., a phrase from MEMORY.md) and confirm the query returns results. Do NOT assume "gateway started = QMD is working."

**Warning signs:**
- `qmd status` returns "idle" with `lastIndexedAt: null` or a timestamp from many months ago
- Query for known MEMORY.md content returns 0 results
- `memory-dir-main` collection shows file count > 0 but queries return nothing
- Bob says "I don't have context about X" when MEMORY.md explicitly contains X

**Phase to address:** Compaction & QMD Bootstrap phase. Must verify via live query before declaring success.

---

### Pitfall 2: Memory Flush Produces No Files Because compaction.memoryFlush Is Misconfigured

**What goes wrong:**
`compaction.memoryFlush` is enabled in openclaw.json, but Bob's sessions end without creating any memory files in the workspace. The `memory-dir-main` collection stays at 19 files indefinitely. The daily memory log intended to accumulate facts about user patterns never appears.

**Why it happens:**
There are three common misconfiguration points that all look correct but silently fail:
1. `softThresholdTokens` is set higher than typical session token usage — flush never triggers because the session always stays under the threshold.
2. The `memoryFlush` prompt in `compaction.memoryFlush` is malformed or uses the wrong key name — OpenClaw ignores unrecognized keys silently.
3. The output path for flushed memories points to a location not bind-mounted into the sandbox, so the file write succeeds inside Docker but disappears when the container stops.

The current state (contextTokens=100000, softThresholdTokens=1500) means every Haiku heartbeat session (which stays well under 1500 tokens) never triggers compaction. Opus sessions for morning briefings (easily 10,000-50,000 tokens) would trigger it, but only if the session actually reaches softThresholdTokens before ending — brief cron-triggered sessions may terminate before accumulating enough context.

**How to avoid:**
Set `softThresholdTokens` to a value that matches real session patterns: 8000-15000 for primary sessions, keep 1500 only if you want nearly every session to flush. Explicitly test by running a session that accumulates context, then checking whether a memory file was written. Verify the output path is bind-mounted.

**Warning signs:**
- Memory file count in `memory-dir-main` never increases day over day
- No files matching `YYYY-MM-DD-*.md` pattern appear in `~/clawd/agents/main/`
- Bob cannot recall information from sessions more than 24 hours ago
- Dashboard memory browser shows the same files for days

**Phase to address:** Compaction config tuning phase. Set threshold based on measured session token usage, not a guess.

---

### Pitfall 3: contextTokens Increase Causes OOM on t3.small During Long Briefing Sessions

**What goes wrong:**
contextTokens is bumped from 100,000 to 200,000 (matching the model's actual maximum). Morning briefing sessions now include all 6 database query results + 7 agent states + email content + calendar events. With QMD retrieval now working, relevant memory chunks are also injected into context. The combined context window pushes memory usage on the t3.small (2GB RAM + 2GB swap) past the ceiling during peak usage. The gateway OOMs, which also kills all 24 cron jobs. The session-prune cron (4 AM UTC) may collide with the morning briefing (6 AM PT = 14:00 UTC), doubling memory pressure.

**Why it happens:**
200K token context windows require large KV cache allocations on the Anthropic API side, but more immediately, the local OpenClaw gateway must buffer the full conversation in memory to manage session state, tool calls, and the compaction decision logic. On a resource-constrained instance, the combination of: large context buffer + Docker container memory + QMD embedding model (~300MB) + gateway process + Mission Control Next.js process exceeds available RAM + swap.

**How to avoid:**
Do NOT jump from 100,000 to 200,000 in one step. Increase incrementally: 100,000 → 130,000, then monitor gateway memory usage for 48 hours with `free -m` in a cron-logged health check. Only increase further if stable. Consider session-specific context overrides (set higher only for main/morning-briefing, leave Haiku heartbeats at 50,000). Alternatively, keep 200,000 as the theoretical maximum but set `reserveTokensFloor` to prevent actual utilization that high.

**Warning signs:**
- `free -m` shows available < 200MB during briefing windows (6-8 AM PT)
- Gateway crashes coincide with morning briefing + other cron overlap windows
- `journalctl --user -u openclaw-gateway.service` shows OOM kills
- Bob's responses truncate or sessions end abruptly during long briefings

**Phase to address:** Compaction + context token tuning phase. Increase incrementally with monitoring, not in one jump.

---

### Pitfall 4: Gateway Restart Breaks All Cron-to-DM Delivery Until Bob Sends a Message First

**What goes wrong:**
Config changes (compaction thresholds, contextTokens, memory backend) require a gateway restart. After restart, cron jobs that target Bob's DM channel via `sessions_send` fail silently — no Slack message, no error logged, job shows `status: ok` in the cron state. The morning briefing fires at 6 AM PT but nothing arrives. This is an existing documented issue but is especially dangerous during v2.9 because the milestone requires multiple gateway restarts (one per config phase).

**Why it happens:**
OpenClaw sessions are tied to the gateway process. When the gateway restarts, all active sessions are cleared (including the DM-linked session Bob uses to deliver cron outputs to Slack). The cron job runs successfully (fires, agent responds), but the response targets the now-dead session's channel binding. Bob must send or receive a direct Slack message to re-establish the session link before cron DM delivery works again.

**How to avoid:**
After every gateway restart during v2.9: immediately send Bob a DM from Slack ("hey, gateway restarted"). Wait for a response. Only then schedule or verify subsequent cron behavior. Do gateway restarts at times that don't overlap with cron windows — avoid 5:50-6:10 AM PT (morning briefing window) and :00/:02/:04/:06 heartbeat windows.

**Warning signs:**
- Gateway restarted AND no morning briefing arrived AND it's past 6:30 AM PT
- `openclaw cron list` shows jobs ran (`lastStatus: ok`) but Slack shows no messages
- Bob doesn't respond to DMs immediately after a restart (session not yet established)

**Phase to address:** Every phase that includes a gateway restart. This is a workflow prerequisite, not a code fix.

---

### Pitfall 5: MEMORY.md Seeding Bootstraps the Wrong Agent's Collection

**What goes wrong:**
MEMORY.md is written to `~/clawd/agents/main/MEMORY.md` (bind-mounted to `/workspace/MEMORY.md`). QMD collections are per-agent. The `memory-dir-main` collection indexes `~/clawd/agents/main/`. If MEMORY.md is mistakenly placed in `~/clawd/` (the parent workspace) or in another agent's directory (e.g., `~/clawd/agents/ops/`), QMD indexes it for the wrong agent. Bob queries the main collection and finds nothing. Sentinel or other agents may unexpectedly find Bob's memory context.

**Why it happens:**
The bind-mount structure is: host `~/clawd/agents/main/` = sandbox `/workspace/`. Bob sees `/workspace/MEMORY.md`. But when writing the file over SSH (not from inside the sandbox), the host path must be used. Confusion between `~/clawd/MEMORY.md` and `~/clawd/agents/main/MEMORY.md` is easy when making manual edits.

**How to avoid:**
Always write workspace files for Bob to `~/clawd/agents/main/` on the host (not `~/clawd/`). Verify placement: `ls -la ~/clawd/agents/main/MEMORY.md`. Check that QMD's memory-dir-main source path matches.

**Warning signs:**
- MEMORY.md exists but `qmd query "Bob's memory"` returns 0 results from main
- `ls ~/clawd/agents/main/` does not show MEMORY.md
- Other agents' collections show unexpectedly large file counts

**Phase to address:** MEMORY.md seeding phase. Verify path before triggering QMD re-index.

---

### Pitfall 6: Retrieval Protocol in AGENTS.md Is Ignored Because It's Too Vague

**What goes wrong:**
A line is added to AGENTS.md (or the session instruction file) that says "search memory before acting." Bob reads it but interprets it loosely — he searches memory for some tasks but skips it for quick responses, cron-triggered briefings, or when the system prompt already feels long. Over time, the retrieval protocol becomes a suggestion rather than a rule. Memory is written to but never actually improves Bob's behavior.

**Why it happens:**
Agent behavior is shaped by specificity. "Search memory before acting" is ambiguous — search for what? When? Using which tool? With what query pattern? Without specific trigger conditions and specific query templates, the agent defaults to its prior behavior pattern. Instructions that compete with "move fast to complete the task" lose.

**How to avoid:**
Make the protocol specific and conditional. Example: "Before answering any question about [Andy's health, preferences, calendar history, project decisions], run: `qmd query '[topic] [context]'` and incorporate results into your response." List the specific categories that require memory lookup. Provide example queries. Add a consequence clause: "If you skip memory search for personal questions, flag it explicitly in your response."

**Warning signs:**
- Bob consistently fails to reference information that exists in MEMORY.md
- Bob answers personal preference questions without checking memory
- Briefings don't show evidence of cross-session continuity (same intro phrasing every day)

**Phase to address:** Retrieval protocol enforcement phase. Must be specific, not aspirational.

---

### Pitfall 7: QMD Embedding Model Saturates CPU, Degrading Heartbeat Crons

**What goes wrong:**
QMD's embedding model (embeddinggemma-300M + query-expansion-1.7B) runs on CPU on the t3.small. When a memory flush produces a new file and triggers re-indexing, QMD begins embedding computation. This is a CPU-intensive operation that can run 30-120 seconds. If a heartbeat cron fires during this window (staggered at :00/:02/:04/:06), Bob's response latency spikes. In worst case, the heartbeat times out or the Slack delivery window closes before the response arrives.

**Why it happens:**
t3.small has 2 vCPUs. The gateway process, QMD embedding process, and Docker container all compete for the same 2 cores. Memory flush → re-index is triggered automatically after files are written. The update interval is 15 minutes, meaning re-indexing can overlap with any cron job that fires in that 15-minute window.

**How to avoid:**
Set QMD's update interval to 30-60 minutes instead of 15 minutes. Schedule QMD's update window (if configurable) to avoid the heartbeat cron windows (the :00-:10 and :30-:40 minute marks). If QMD supports nice/ionice settings, apply them. Monitor: after enabling flush, check whether heartbeat cron latency increases.

**Warning signs:**
- Heartbeat cron `lastDurationMs` increases from ~5 seconds to 30+ seconds after memory flush is enabled
- QMD re-indexing shown in `qmd status` during heartbeat windows
- Slack shows delayed or missing heartbeat messages during QMD activity

**Phase to address:** Memory health monitoring phase — after enabling flush, measure impact on cron latency before declaring success.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy last MEMORY.md to new one without pruning | Fast seeding | Stale/false memories degrade QMD retrieval precision as vector store grows with contradictory chunks | Never — always curate before seeding |
| Set softThresholdTokens=1500 for all agents | Every session flushes | Haiku heartbeats (200-400 tokens) never flush; Opus sessions flush too aggressively, creating noise | Only acceptable as a temporary test value |
| Skip QMD query verification after bootstrap | Saves 5 minutes | Silent zero-result retrieval means the entire memory system is non-functional without anyone knowing | Never — always run at least one test query |
| Keep contextTokens at 200K permanently | Maximizes context | OOM risk on peak-load days when briefing + heartbeats + QMD re-index all overlap | Acceptable only after 48-hour stability validation |
| Use the same memory flush path for all 7 agents | Simpler config | Content agents (Quill, Sage, Ezra) that are cron-only produce flush files that confuse QMD's main collection | Never for cron-only agents — disable flush on agents with no continuous sessions |

---

## Integration Gotchas

Common mistakes when connecting memory components.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| QMD + Docker sandbox | Assuming QMD CLI is available inside sandbox | QMD runs on HOST, not in Docker. Bob queries via OpenClaw's memory tool abstraction. Do not try to run `qmd query` inside the sandbox directly |
| QMD + openclaw.json | Setting `memory.backend = "qmd"` without verifying QMD binary path | Check `qmd --version` first; QMD wrapper must be at `~/.bun/bin/qmd` and Bun must be in PATH for the systemd user service |
| compaction + cron sessions | Expecting memory flush to run in isolated cron sessions | Isolated cron sessions (separate Docker container) may not trigger compaction — compaction typically fires at session end in the primary session context |
| AGENTS.md + session instructions | Adding retrieval protocol to AGENTS.md but not to cron system prompts | AGENTS.md updates the standing instructions for interactive sessions. Cron jobs use their own payload/reference docs. Update CRON instruction files separately if retrieval should happen during cron sessions |
| QMD + Gemini fallback | Assuming QMD failure silently returns empty results | QMD failure triggers Gemini embeddings fallback, which has different result quality. Monitor which backend is actually being used: `qmd status` should show "active", not "fallback" |
| Memory flush + bind-mount | Writing flush output to `/workspace/memory/` inside sandbox | `/workspace/` = `~/clawd/agents/main/` on host. Memory flush files must land in this directory to be indexed by QMD's `memory-dir-main` collection |

---

## Performance Traps

Patterns that work initially but degrade over time.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| QMD vector store grows unbounded | Query latency increases, memory usage grows | Prune/compact memory files periodically; archive old daily logs beyond 90 days | After 500+ memory files, query latency on CPU-only t3.small noticeably increases |
| sessions.json grows to 1.7MB+ | Prune cron takes longer, gateway startup slower | `prune-sessions.sh` at 4 AM is already in place — verify it's clearing old sessions | Already at 1.7MB/74 sessions per MEMORY.md — prune is critical to maintain |
| MEMORY.md becomes authoritative instead of curated | Bob repeats stale facts, outdated preferences override new behavior | Treat MEMORY.md as living document; review monthly | From first day if seeded with unvalidated content |
| softThresholdTokens too low triggers every session | Explosion of memory flush files, QMD re-indexes constantly, CPU saturated | Set threshold above median session token usage | Immediate — any threshold below typical Opus session size (10K+ tokens) |
| contextTokens at 200K with QMD injection | Memory chunks + tool outputs + session history fills context, compaction triggers too early | Cap QMD retrieval results (top-3 to top-5 chunks, not top-20), keep retrieved context under 5K tokens | From first QMD-enabled session if retrieval limits are not set |

---

## Security Mistakes

Domain-specific security issues for this memory system.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Seeding MEMORY.md with API keys or credentials | QMD embeds credentials into vector store; retrievable by Bob in any session including compromised ones | Never put credentials in MEMORY.md — use `~/.openclaw/.env` and openclaw.json only |
| Retrieval protocol queries personal health data broadly | Bob retrieves sensitive Oura Ring / weight data in sessions not requiring it | Scope retrieval queries narrowly; don't do "search all memory" queries in briefing sessions |
| Memory flush output readable by other agents | If flush path overlaps with multi-agent bind-mount, content agents can read main agent memory | Verify memory flush path is `~/clawd/agents/main/` not `~/clawd/` (parent is bind-mounted by multiple agents) |
| MEMORY.md committed to git without scrubbing | Git history exposes health metrics, financial data, personal preferences permanently | MEMORY.md is already gitignored (in `~/clawd/`), but verify before any git operations |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **QMD bootstrap:** Config is set and gateway starts cleanly — verify by running `qmd query "Andy morning briefing preferences"` and confirming non-empty results before declaring bootstrap complete
- [ ] **Memory flush enabled:** `compaction.memoryFlush` is set in openclaw.json — verify by triggering a session long enough to hit softThresholdTokens, then checking `ls -la ~/clawd/agents/main/*.md` for new files with today's date
- [ ] **contextTokens increased:** Value updated in openclaw.json and gateway restarted — verify by checking `free -m` during morning briefing window for 2 consecutive days, confirming no OOM events in journalctl
- [ ] **MEMORY.md seeded:** File written to EC2 — verify via `ls -la ~/clawd/agents/main/MEMORY.md` AND `qmd query "Andy" | head` confirms it's indexed
- [ ] **Retrieval protocol in AGENTS.md:** Text added to standing instructions — verify by asking Bob to recall something from MEMORY.md cold (fresh session), confirming he cites it without being prompted
- [ ] **Memory health monitoring:** Cron or mission control page added — verify it actually catches the zero-file case (mock a failure, confirm alert fires)
- [ ] **QMD using correct backend:** `qmd status` shows "active" (not "fallback" to Gemini), collection counts are non-zero, last-indexed timestamp is recent

---

## Recovery Strategies

When pitfalls occur despite prevention.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| QMD bootstrap never ran / collections empty | LOW | Run `qmd index --collection memory-dir-main --force`; wait for completion; verify with test query |
| Memory flush writing files but QMD not indexing them | LOW | Check `qmd status` for errors; restart QMD daemon if needed; manually trigger re-index |
| Gateway OOM after contextTokens increase | MEDIUM | SSH via Tailscale → `systemctl --user restart openclaw-gateway.service` → DM Bob to re-establish session → reduce contextTokens → restart again |
| Stale MEMORY.md degrading QMD retrieval quality | LOW | Edit MEMORY.md on host to remove contradictions → trigger re-index → verify queries return correct results |
| Cron DM delivery broken after gateway restart | LOW | DM Bob from Slack immediately → wait for response → verify next cron fires correctly |
| Memory flush creates noise (too many files) | LOW | Raise softThresholdTokens to reduce flush frequency; add QMD ignore pattern for noise files; prune oldest flush files |
| CPU saturation from QMD re-indexing during crons | MEDIUM | Increase QMD update interval to 30-60 min; stagger config to avoid heartbeat windows; monitor for 48h |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| QMD not bootstrapped (#1) | Compaction & QMD Bootstrap phase | `qmd query "Andy preferences"` returns results before phase closes |
| Memory flush misconfigured (#2) | Compaction config tuning phase | New memory file appears in `~/clawd/agents/main/` after a qualifying session |
| contextTokens OOM (#3) | Compaction config tuning phase | `free -m` stable during briefing window for 48h |
| Gateway restart breaks cron delivery (#4) | Every phase with gateway restart | Send DM immediately post-restart; verify next scheduled cron delivers |
| MEMORY.md wrong path (#5) | MEMORY.md seeding phase | `ls ~/clawd/agents/main/MEMORY.md` succeeds; QMD query returns hits |
| Retrieval protocol too vague (#6) | Retrieval protocol enforcement phase | Bob cites MEMORY.md content unprompted in a cold session |
| QMD CPU saturation (#7) | Memory health monitoring phase | Heartbeat latency unchanged after enabling flush (measure delta) |

---

## Sources

- MEMORY.md (project internal) — Current system state: QMD v1.1.0, Bun v1.3.10, searchMode=search, updateInterval=15m, 19 files in memory-dir-main, contextTokens=100000, softThresholdTokens=1500
- PROJECT.md (project internal) — v2.9 milestone goals, infrastructure constraints (t3.small, 2GB RAM + 2GB swap, Docker sandbox), 24 cron jobs, 7 agents, gateway restart session-loss behavior
- v2.7 PITFALLS.md (project internal) — Prior gateway restart / OOM patterns, YOLO Dev memory implications
- v2.6-era note in v2.7 PITFALLS.md — Prior memory pitfalls: MEMORY.md curation, flush thresholds, bootstrap truncation
- Known Issues from MEMORY.md: "Gateway restart clears DM sessions", "SKILL.md YAML frontmatter" (unquoted colons), "Resend Receiving API stale"
- OpenClaw compaction documentation pattern derived from `compaction.memoryFlush`, `softThresholdTokens`, `reserveTokensFloor` field names observed in PROJECT.md key decisions
- QMD behavior: "searchMode: search (BM25+vectors, avoids slow LLM reranker on t3.small CPU)" — MEMORY.md confirms QMD home, model locations, collection structure

---

*Pitfalls research for: OpenClaw memory system repair (v2.9)*
*Researched: 2026-03-08*
*Supersedes: v2.7 YOLO Dev PITFALLS.md*
