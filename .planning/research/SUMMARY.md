# Project Research Summary

**Project:** pops-claw v2.9 — Memory System Overhaul
**Domain:** OpenClaw QMD memory backend repair on live EC2 deployment
**Researched:** 2026-03-08
**Confidence:** HIGH (based on direct SSH inspection of live system)

## Executive Summary

This is a targeted repair milestone, not a greenfield build. Bob's memory system is partially functional but broken in three specific ways that prevent useful long-term recall: (1) MEMORY.md lives at the wrong path and is invisible to QMD's memory-root-main collection, (2) the compaction flush threshold is misconfigured (softThresholdTokens=1500 vs. an appropriate 8000), causing session summaries to rarely fire, and (3) there is no retrieval protocol in AGENTS.md — Bob never searches memory before acting, making the indexed data behaviorally irrelevant even when search technically works. Research confirmed via direct SSH inspection that memory-dir-main is working (21 daily logs indexed, BM25 search returns results), but the higher-value collections (memory-root, memory-alt) are empty because no MEMORY.md exists at the expected path.

The recommended approach is fix-order-driven: compaction threshold first (requires the only gateway restart), then MEMORY.md creation and content seeding, then retrieval protocol, then flush prompt quality improvements, then health monitoring. This order batches the gateway disruption, avoids adding a retrieval protocol that references empty collections, and defers monitoring until there is something worth monitoring. No new infrastructure is required — zero new packages, no new databases, no Docker changes, no new agents.

The primary risk is QMD collection bootstrapping, which has documented systemic issues (Issues #11308, #23613). Bootstrap must be verified via live query after each step rather than assuming "gateway started = QMD working." Secondary risk is OOM during any future context window expansion — if contextTokens is raised toward 200K, it must be incremented carefully and monitored against t3.small RAM (2GB + 2GB swap) during morning briefing windows when gateway, QMD embedding model, and Mission Control all compete for resources.

---

## Key Findings

### Recommended Stack

No new stack additions. The full tech stack exists on EC2 and is working. The work is config edits, file writes, and CLI commands.

**Core technologies in play:**
- **QMD v1.1.0** (`~/.bun/bin/qmd`): indexing and storage backend, BM25+vector search — confirmed working for memory-dir-main; do not upgrade
- **Bun v1.3.10**: QMD runtime dependency — working, do not modify
- **embeddinggemma-300M**: local embedding model in `~/.cache/qmd/models/` — already downloaded, powers `searchMode: "search"` (BM25+vectors). Keep this; never switch to `"query"` mode on t3.small (LLM reranker is too slow, adds 500MB RAM)
- **OpenClaw v2026.3.2**: gateway, compaction orchestration, memoryFlush trigger — has collection-conflict recovery fix from Issue #23613
- **Gemini embedding API** (`memorySearch.provider: gemini`): retrieval enhancement layer on top of QMD storage — complementary, not competing; do NOT remove; QMD BM25 still works if Gemini is unavailable
- **Next.js 14.2.15** (Mission Control): optional health panel target — zero new npm packages needed; pattern matches existing pages

**Critical version note:** v2026.3.1 had a compaction loop regression with memoryFlush (Issue #32106). v2026.3.2 should have fixed it, but monitor `journalctl` after raising softThresholdTokens.

### Expected Features

Research confirmed via SSH — diagnosis-driven, not speculative.

**Must have (broken without these):**
- **MEMORY.md at correct path** (`~/clawd/agents/main/MEMORY.md`) — QMD memory-root-main collection searches this exact path; file currently at wrong location (`~/clawd/MEMORY.md`), giving 0 files in the collection
- **Updated MEMORY.md content** — existing file is 4+ weeks stale (last updated 2026-02-23); missing QMD backend switch, v2.8 features, all 6 databases, content pipeline status, resend outage, memory/ directory pattern and daily log behavior
- **Compaction threshold tuned** — softThresholdTokens raised 1500 → 8000; at 1500, flush fires only when 22,500 tokens of reserved context are consumed, which almost never happens in heartbeat or briefing sessions
- **Retrieval protocol in AGENTS.md** — without explicit instruction to run `qmd search` before acting, Bob has the tool but never uses it systematically; this is the highest-behavioral-impact fix
- **Improved memoryFlush prompt** — current prompt is shallow; should instruct DB queries (content.db, coordination.db, email.db) even on quiet days to produce 10-15 line minimum logs vs. current 1-3 line "quiet day" entries

**Should have (reliability and observability):**
- **Memory health monitoring cron** — daily check: yesterday's log was written, QMD indexed it, test search returns results; alert to Slack if any check fails; prevents silent memory death
- **Daily cron rescheduled from 7 AM UTC to 23 UTC** — captures the day's activity rather than the previous night's sparse data
- **QMD embed cleanup** — `qmd status` shows 1 pending file; run `qmd embed` to clear backlog; low priority but eliminates warning

**Defer to v3.0+:**
- Per-agent MEMORY.md files for interactive sub-agents (landos, rangeos, ops) — high maintenance, not blocking v2.9
- Monthly memory compaction / archive of old daily logs — not a problem at 21 files; revisit at 100+
- Cross-agent memory sharing — not in QMD architecture, requires custom implementation
- Mission Control memory browser page — nice to have once retrieval protocol is functional

### Architecture Approach

Three clearly separated layers: write (compaction flush + daily cron), index (QMD), and read (agent retrieval). All three layers are partially functional. The fixes target the write layer (compaction threshold, flush prompt quality, MEMORY.md file presence) and read layer (retrieval protocol). The index layer (QMD) is already working correctly for memory-dir-main — the 15-minute update interval, BM25 search, and embedding pipeline are all functional.

**Major components:**
1. **compaction.memoryFlush** (in-session flush): fires when session context nears limit; currently broken — softThresholdTokens=1500 is too low to trigger in any normal session; fix: raise to 8000
2. **daily-memory-flush cron** (daily baseline flush): reliable, writing 21 files since Feb 2; thin content (1-3 lines on quiet days) because in-session flush never primes it; fix: better prompt + reschedule from 7 AM UTC to 23 UTC
3. **QMD memory-dir-main collection**: working, indexes daily logs every 15m, BM25 search returns results; no changes needed
4. **QMD memory-root-main collection**: broken (0 files); fix is simple — create MEMORY.md at `~/clawd/agents/main/MEMORY.md` and QMD auto-indexes it within 15 minutes
5. **AGENTS.md retrieval protocol**: missing; fix: add explicit section with specific trigger categories, query templates, and consequence clause
6. **Memory health monitoring**: missing; fix: new cron that verifies file writes, QMD indexing, and search results

**Key confirmed fact from SSH inspection:** The effective agent workspace for "main" is `~/clawd/agents/main/` (not `~/clawd/`). Docker /workspace/ maps to this per-agent directory. All file operations must target this path.

### Critical Pitfalls

1. **QMD appears configured but was never bootstrapped** — `memory.backend: "qmd"` in config and a clean gateway start do NOT guarantee QMD is indexing. Always verify with a live query (`qmd search "Andy"`) that returns non-empty results before declaring bootstrap complete. Silent fallback to Gemini/builtin means memory appears to work while returning nothing relevant.

2. **Memory flush misconfigured — produces no files** — softThresholdTokens=1500 with reserveTokensFloor=24000 means flush fires only when 22,500 tokens of reserved window are consumed. Heartbeat sessions (Haiku, ~200-400 tokens) and most briefings never reach this. Fix: raise to 8000. After change, verify by triggering a session long enough to accumulate context and confirming a new `.md` file appears in `~/clawd/agents/main/memory/`.

3. **Gateway restart breaks cron DM delivery until Bob receives a message first** — every gateway restart clears sessions, breaking cron `sessions_send` to DM channels silently. After every restart: DM Bob from Slack immediately, wait for response, only then validate subsequent cron behavior. Schedule restarts outside of briefing windows (avoid 5:50-6:10 AM PT and heartbeat :00/:02/:04/:06 windows).

4. **MEMORY.md seeded at wrong path** — host path confusion between `~/clawd/MEMORY.md` (legacy) and `~/clawd/agents/main/MEMORY.md` (QMD target) is easy when editing over SSH. Always write to `~/clawd/agents/main/MEMORY.md` and verify with `ls -la` before triggering QMD re-index.

5. **Retrieval protocol too vague to change Bob's behavior** — "search memory before acting" is insufficient. Must specify: which categories trigger a search, what query template to use, and what consequence applies if search is skipped. Without specificity, the protocol becomes a suggestion that loses to task momentum.

6. **QMD embedding saturates CPU during heartbeat cron windows** — embeddinggemma-300M runs on CPU; re-indexing after a memory flush can take 30-120s. If this overlaps with heartbeat crons (:00/:02/:04/:06), cron latency spikes. Mitigation: increase QMD update interval from 15m to 30-60m after enabling flush; monitor heartbeat `lastDurationMs` for 48 hours.

---

## Implications for Roadmap

Based on combined research, the dependency chain is clear and dictates a specific 4-phase structure:

### Phase 1: Compaction Config and QMD Bootstrap Verification
**Rationale:** Requires the only mandatory gateway restart. Batching this disruption first means all subsequent phases can be completed without another restart. Also the highest-impact fix — without the threshold change, the flush never fires regardless of how good the prompt is. QMD bootstrap must be explicitly verified, not assumed.
**Delivers:** softThresholdTokens raised (1500 → 8000); memoryFlush prompt optionally improved; gateway restarted; QMD collections verified via live query (`qmd search "Andy"` returns results); Bob's DM session re-established post-restart.
**Addresses:** Table stakes features — compaction threshold, QMD bootstrap verification
**Avoids:** Pitfall #2 (flush misconfigured), Pitfall #4 (gateway restart session loss), Pitfall #1 (QMD configured but not bootstrapped)
**Research flag:** SKIP — all config values confirmed via SSH inspection; QMD CLI commands verified against v1.1.0 docs.

### Phase 2: MEMORY.md Fix and Content Seeding
**Rationale:** QMD memory-root-main collection is empty because the file is at the wrong path. This must be fixed before adding a retrieval protocol — no point instructing Bob to search memory if the primary collection has 0 files. Content must be current before retrieval goes live, or Bob acts on 4-week-stale data.
**Delivers:** `~/clawd/agents/main/MEMORY.md` created with curated, current facts (Andy profile, system state, all 6 DBs, content pipeline status, resend outage, v2.8 features, memory/ directory behavior). Legacy `~/clawd/MEMORY.md` decommissioned or symlinked. QMD auto-indexes within 15 minutes; verify with test query.
**Avoids:** Pitfall #5 (MEMORY.md at wrong path), anti-feature of copying stale content without curation
**Research flag:** SKIP for mechanics (file write + QMD auto-indexes). Content curation is judgment based on project state, not research.

### Phase 3: Retrieval Protocol and Flush Quality
**Rationale:** Now that QMD has something worth retrieving (Phase 2), add the behavioral instruction that makes Bob use it. Simultaneously improve the daily flush prompt to produce richer daily logs (DB state queries on quiet days, consistent section structure). These two changes are coupled — better logs make retrieval more valuable, and both depend on Phase 2's collections being populated.
**Delivers:** AGENTS.md retrieval protocol (specific trigger categories, query templates, consequence clause). Improved `compaction.memoryFlush.prompt` that queries coordination.db and content.db. Daily cron rescheduled from 7 AM UTC to 23 UTC to capture day's activity. `~/clawd/agents/main/DAILY_FLUSH.md` updated with richer content instructions.
**Avoids:** Pitfall #6 (retrieval protocol too vague)
**Research flag:** SKIP — AGENTS.md patterns are established; flush prompt is a config edit; cron reschedule is a one-field JSON change.

### Phase 4: Memory Health Monitoring
**Rationale:** After Phases 1-3, the memory system should be functional. Phase 4 adds observability to detect if it silently degrades. Monitoring is last because there must be something worth monitoring (populated collections, regular flush output) before a health check is meaningful. Also lowest risk — read-only diagnostic operations.
**Delivers:** Daily health monitoring cron — verifies yesterday's log was written, QMD indexed it, test search returns results, alerts to Slack on failure. QMD embed cleanup (1 pending file). Optionally: Mission Control memory health panel (line count per agent, 7-day flush sparkline using `fs.statSync`, warning badges at 80% and 95% of 200-line budget).
**Avoids:** Pitfall #1 (QMD silently not working), Pitfall #7 (CPU saturation — detect before it degrades crons)
**Research flag:** SKIP for health cron (established cron pattern from 24 existing crons). CONSIDER research during planning for the Mission Control panel if the sparkline implementation is unclear — but the established page pattern (API route + SWR) is well-documented internally.

### Phase Ordering Rationale

- **Gateway restart is the only disruptive operation** — Phase 1 owns it; subsequent phases avoid it
- **Empty collections precede retrieval protocol** — adding retrieval before fixing MEMORY.md path would train Bob to search a broken system and retrieve nothing
- **Compaction threshold precedes flush prompt** — a perfectly worded prompt at softThresholdTokens=1500 still rarely fires; fix the trigger before improving the output
- **Monitoring is last** — cannot validate monitoring against a broken baseline; validate the system first, then verify it stays working

### Research Flags

All phases can skip `/gsd:research-phase` — this milestone is repair work on a known, fully-inspected system:

- **Phase 1:** All config values confirmed via SSH (openclaw.json, QMD v1.1.0 CLI). No unknowns.
- **Phase 2:** File write mechanics straightforward. Content curation is judgment (project state), not research.
- **Phase 3:** Established AGENTS.md and reference doc patterns. Config edit only for prompt. No external dependencies.
- **Phase 4 (cron):** Health check cron follows established pattern from 24 existing crons. No new tooling.
- **Phase 4 (Mission Control panel):** File-stat-based sparkline (`fs.statSync`) is novel but matches existing Next.js patterns. If time-constrained, skip the MC panel and deliver cron health check only — the cron delivers all functional value.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All components confirmed via direct SSH inspection on 2026-03-08; versions verified; zero new dependencies needed |
| Features | HIGH | Diagnosis performed against live system via SSH; broken/working status confirmed per component, not inferred |
| Architecture | HIGH (current state) / MEDIUM (internals) | File paths, collection counts, config values all confirmed via SSH. QMD+Gemini interaction and exact compaction trigger math are partially inferred from behavior |
| Pitfalls | HIGH | Derived from production system history (MEMORY.md), prior milestone pitfall docs (v2.6, v2.7), and direct evidence of current failure modes |

**Overall confidence:** HIGH

### Gaps to Address

- **Exact nesting path for compaction config in openclaw.json** — needs `python3 -m json.tool ~/.openclaw/openclaw.json` to confirm the path is `agents.defaults.compaction.memoryFlush.softThresholdTokens` or a variant. LOW risk; verification is the first step of Phase 1.
- **Whether v2026.3.1 compaction regression persists in v2026.3.2** — Issue #32106 (aggressive compaction loop with memoryFlush). Needs monitoring after gateway restart. Mitigation: watch `journalctl --user -u openclaw-gateway.service` for the first 24 hours.
- **Whether daily-memory-flush cron has `workspaceAccess: "ro"` set** — if so, memoryFlush writes would be silently skipped in isolated cron sessions. Needs SSH inspection before Phase 3. Low probability (file evidence confirms cron IS writing files), but should be verified explicitly.
- **QMD+Gemini retrieval routing** — whether Gemini generates query embeddings for QMD BM25 or operates as a separate retrieval path. Not publicly documented. Does not block any phase; affects expected retrieval quality ceiling only.
- **contextTokens expansion safety** — current contextTokens=100000; model max is 200K. Any expansion must be incremented (not jumped), monitored via `free -m` during briefing windows. Explicitly out of scope for v2.9.

---

## Sources

### Primary (HIGH confidence)
- Live EC2 SSH inspection (2026-03-08) — openclaw.json full config, QMD status, collection listing, index.yml, daily log contents, `qmd search "Andy"` verified working
- OpenClaw Memory Docs (`docs.openclaw.ai/concepts/memory`) — QMD backend config keys, memoryFlush behavior, workspaceAccess constraint, default collection names
- OpenClaw Session Management Docs (`docs.openclaw.ai/reference/session-management-compaction`) — reserveTokensFloor, softThresholdTokens, flush threshold formula
- QMD GitHub (`github.com/tobi/qmd`) — `qmd collection add`, `qmd update`, `qmd embed` CLI commands verified for v1.1.0
- Project MEMORY.md — QMD v1.1.0 install, Bun v1.3.10, searchMode=search, update interval=15m, collection counts, agent workspace structure
- Project memory/ directory listing — 21 files, Feb 2 through Mar 7, confirmed file existence and content sizing

### Secondary (MEDIUM confidence)
- OpenClaw Issue #11308 — QMD systemic issues, collection management bugs
- OpenClaw Issue #23613 — "Collection not found: memory-root-main" bug and workaround (fixed in v2026.3.2)
- OpenClaw Issue #17034 — softThresholdTokens doesn't scale with context window; community-recommended values for 200K window
- OpenClaw Issue #32106 — v2026.3.1 aggressive compaction loop regression with memoryFlush
- OpenClaw Issue #37634 — workspaceAccess: "none" skips memoryFlush writes silently
- VelvetShark OpenClaw Memory Masterclass — softThresholdTokens=8000 for 200K window, community validated
- Jose Casanova: Fix OpenClaw Memory Search with QMD — bootstrap command sequence verified against v1.1.0

### Tertiary (LOW confidence, needs EC2 verification during execution)
- Exact openclaw.json nesting path for compaction.softThresholdTokens — confirm via direct file read in Phase 1
- Whether v2026.3.1 compaction regression persists in v2026.3.2 — confirm via post-restart monitoring
- daily-memory-flush cron workspaceAccess setting — confirm via SSH inspection before Phase 3

---

*Research completed: 2026-03-08*
*Ready for roadmap: yes*
