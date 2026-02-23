# Project Research Summary

**Project:** pops-claw -- Agent Memory Improvements + Dashboard Polish
**Domain:** Memory system reliability, retrieval discipline, memory health monitoring, and dashboard polish for an existing OpenClaw multi-agent deployment on EC2
**Researched:** 2026-02-23
**Confidence:** HIGH

## Executive Summary

This milestone focuses on two interrelated concerns: hardening the agent memory system (MEMORY.md curation, flush threshold tuning, retrieval instructions, LEARNINGS.md activation) and polishing the Mission Control dashboard (memory health panel, context usage indicators, agent board refinements). The underlying infrastructure -- a Next.js 14 dashboard reading from 5 SQLite databases on a Tailscale-private EC2 t3.small -- was built in v2.5 and is proven. The stack stays unchanged. The work is configuration, curation, and presentation -- not new infrastructure.

The recommended approach is to start with MEMORY.md curation (the highest-risk single operation) because every subsequent phase depends on a healthy, right-sized memory footprint. Curation must happen before adding retrieval instructions (which consume bootstrap budget) or activating LEARNINGS.md (which generates new memory entries). The dashboard polish phases (memory health panel, context usage indicators, agent board polish) depend on the memory system being stable and well-understood. The architecture research from v2.5 (STACK.md, ARCHITECTURE.md) provides the proven data layer patterns -- singleton better-sqlite3 connections, WAL mode, SWR polling -- that the new dashboard panels will reuse.

The dominant risk is operational context loss. MEMORY.md is 304 lines of hard-won knowledge, and curation means condensing it without destroying the entries that prevent production failures. Five of the ten identified pitfalls trace back to "removing or changing something that looked safe but was load-bearing." The second risk is the gateway restart problem: any `openclaw.json` changes require a restart that kills all 20 cron job DM sessions. All config changes must be batched into a single restart at a low-activity window. The third risk is bootstrap budget exhaustion -- adding retrieval instructions to boot files that are already near the truncation threshold causes silent instruction loss.

---

## Key Findings

### Recommended Stack

No new stack additions. The v2.5 stack (Next.js 14.2.15, Tailwind CSS, better-sqlite3 12.6.2, shadcn/ui, Recharts 3.7.0, date-fns 4.1, SWR, cron-parser v5) is proven and stays unchanged. The memory health dashboard panel reuses the existing database singleton pattern. Context usage indicators reuse the existing observability.db queries. The only "new" integration is opening per-agent memory databases (sqlite-vec + FTS5 backed), which uses the same better-sqlite3 readonly + WAL pattern.

**Core technologies (unchanged from v2.5):**
- `better-sqlite3` v12.6.2: SQLite read-only access -- extended to per-agent memory databases for health monitoring
- `shadcn/ui`: Dashboard components -- new panels use existing card, badge, and table primitives
- `recharts` v3.7.0: Charting -- token usage sparklines, context usage progress bars
- `swr`: Client polling -- 30-60s refresh intervals for new dashboard panels

**Key extension point:**
- `lib/db/index.ts` singleton factory must be extended to support per-agent memory databases (`memory-main`, `memory-landos`, etc.) using the same WAL + readonly pattern. Do NOT load the sqlite-vec extension in the dashboard -- it is not needed for health metrics (chunk count, last indexed, file size).

### Expected Features

Features are split between memory system improvements (agent-side, no UI) and dashboard polish (UI presentation of memory health).

**Must have (table stakes):**
- MEMORY.md curated to under 150 lines with backup, critical entries preserved, archive created
- Gateway restart strategy defined and documented (batch changes, low-activity window, DM re-establishment checklist)
- Memory health visibility in Mission Control -- at minimum, MEMORY.md line count indicator and per-agent chunk counts
- Context usage indicators on the agent board -- using the correct 3-field token formula from 31.1-RESEARCH.md

**Should have (differentiators):**
- Retrieval instructions in AGENTS.md improving memory search discipline
- LEARNINGS.md activation with explicit criteria, size limits, and 48-hour trial period
- Flush threshold tuning based on actual session token profiles (not guesswork)
- Agent board visual polish (colored borders, hover tooltips, responsive layout verification)

**Defer:**
- Memory search quality analytics (query log, relevance scoring) -- requires deeper memory system instrumentation
- Automated MEMORY.md curation by cron -- too risky to automate; manual curation with monitoring is the right approach
- sqlite-vec vector queries from dashboard -- not needed for health monitoring and adds extension complexity

### Architecture Approach

The architecture is additive to the v2.5 foundation. The database layer (`lib/db/`) gains per-agent memory database connections via an extended `DB_PATHS` map and `DbName` type. New API routes (`/api/memory/health`, `/api/agents/[id]/context`) follow the same thin-route-handler pattern: call a query function, return JSON, zero business logic. SWR polling on the client side refreshes memory health data at lower frequency (60s) since memory changes slowly. The cross-database activity feed, status cards, and agent board from v2.5 are untouched.

**Major components:**
1. `lib/db/index.ts` -- Extended with per-agent memory database connections (4 agents with memory data, not all 7)
2. `lib/db/queries/memory.ts` -- NEW: chunk count, last indexed timestamp, file sizes per agent memory DB
3. `lib/db/queries/agents.ts` -- EXTENDED: context usage calculation using `input_tokens + cache_read_tokens + cache_write_tokens`
4. Memory health dashboard panel -- Card showing per-agent memory stats, MEMORY.md line count, curation warnings
5. Context usage indicators -- Progress bar on agent cards using 3-field token formula with model-specific limits

### Critical Pitfalls

1. **MEMORY.md curation deletes critical operational context** -- Before removing ANY entry, ask "if this fact were unknown, what breaks?" Tag entries as CRITICAL/REFERENCE/STALE. Condense, do not delete. Create MEMORY-ARCHIVE.md for full-text versions. Always `cp MEMORY.md MEMORY.md.bak` before editing.

2. **Gateway restart kills 20 cron DM sessions** -- Batch ALL `openclaw.json` changes into a single restart at 3-4 AM UTC. Check cron schedule beforehand. DM Bob immediately after restart to re-establish sessions. Create a post-restart checklist.

3. **Retrieval instructions silently truncated by bootstrap** -- OpenClaw only auto-loads 7 specific files. A file named RETRIEVAL.md will NOT be loaded. Check `openclaw context list` for total bootstrap size before adding. Keep instructions under 500 characters in AGENTS.md.

4. **Flush threshold tuning triggers premature compaction** -- Profile actual session token usage BEFORE changing `softThresholdTokens`. The morning briefing uses ~150K tokens; triggering compaction at 160K breaks it. Change by 2-4K increments, monitor 48 hours.

5. **LEARNINGS.md noise feedback loop pollutes memory search** -- Define explicit criteria (only write what contradicts current understanding or is undocumented elsewhere). Set 50-line/2000-char max. Do NOT index in memory search until after a 48-hour quality review.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Memory Curation and Restart Strategy
**Rationale:** This is the prerequisite for everything. MEMORY.md curation frees bootstrap budget needed for retrieval instructions (Phase 3). The restart strategy must be defined before any `openclaw.json` changes (Phase 2). Curation is also the highest-risk single operation -- doing it first with full attention prevents cascading failures.
**Delivers:** MEMORY.md curated to <150 lines with CRITICAL/REFERENCE/STALE classification; MEMORY-ARCHIVE.md created with full-text versions of condensed entries; backup workflow documented; gateway restart checklist documented; visual baseline screenshots of current dashboard taken (needed before Phase 5 polish).
**Addresses:** Table-stakes memory curation, restart strategy
**Avoids:** Pitfall 1 (context loss from curation), Pitfall 3 (gateway restart killing sessions), Pitfall 9 (re-growth past truncation)

### Phase 2: Flush Threshold Tuning
**Rationale:** Must happen after curation (Phase 1 reduces bootstrap size, changing the token math) but before retrieval instructions (Phase 3 adds to bootstrap, further changing the math). Requires profiling actual session token usage first -- no guesswork.
**Delivers:** Documented session token profiles for key cron jobs (morning briefing, weekly review, evening recap); `softThresholdTokens` tuned with 20K+ buffer above typical session peak; 48-hour monitoring period confirming no quality degradation; changes batched into a single gateway restart per the Phase 1 checklist.
**Uses:** `openclaw sessions` for token profiling; restart checklist from Phase 1
**Avoids:** Pitfall 2 (premature compaction), Pitfall 3 (restart impact)

### Phase 3: Retrieval Instructions and LEARNINGS.md
**Rationale:** Depends on Phase 1 (bootstrap budget freed by curation) and Phase 2 (flush thresholds stable). These two features are grouped because they both modify agent behavior -- retrieval instructions change how the agent searches memory, LEARNINGS.md changes how it writes memory. Testing them together reveals interaction effects.
**Delivers:** Retrieval instructions added to AGENTS.md (under 500 chars); `openclaw context list` confirming no truncation; LEARNINGS.md activated with explicit criteria and 50-line cap; 48-hour trial period with quality review; decision on whether to index LEARNINGS.md in memory search.
**Uses:** AGENTS.md (existing auto-loaded file); `openclaw context list` for verification
**Avoids:** Pitfall 4 (bootstrap truncation), Pitfall 5 (LEARNINGS.md noise loop)

### Phase 4: Memory Health Dashboard Panel
**Rationale:** By now the memory system is stable (Phases 1-3). This phase surfaces memory health metrics in Mission Control so ongoing monitoring replaces manual SSH checks. Depends on the v2.5 dashboard being deployed with the db singleton pattern.
**Delivers:** Memory health panel in Mission Control showing per-agent chunk count, last indexed timestamp, MEMORY.md line count with threshold warning (180/200 lines), cron-only agents showing "N/A" not errors; `lib/db/queries/memory.ts` with per-agent memory DB queries; results cached for 5 minutes (memory changes slowly).
**Uses:** better-sqlite3 singleton pattern extended for per-agent memory DBs; shadcn/ui cards and badges; SWR polling at 60s
**Avoids:** Pitfall 6 (querying non-existent DBs for cron-only agents), Pitfall 10 (breaking db.ts when extending it)

### Phase 5: Context Usage Indicators
**Rationale:** The 31.1-RESEARCH.md already provides verified formulas and production data. This phase implements the UI. Must use the 3-field token formula (`input_tokens + cache_read_tokens + cache_write_tokens`) with per-model context limits (Sonnet 4.5 = 1M, Haiku 4.5 = 200K). Depends on Phase 4 only for dashboard stability confirmation -- the data is already in observability.db from v2.5.
**Delivers:** Context usage progress bar on each agent card; percentage text showing actual value (may exceed 100%); progress bar width capped at 100%; tooltip explaining extended context for >100% cases; handles zero-data agents gracefully.
**Uses:** observability.db `llm_usage` with all 3 token fields; Recharts or CSS progress bar; existing 31.1-RESEARCH.md formulas
**Avoids:** Pitfall 7 (misleading percentages from using input_tokens alone)

### Phase 6: Agent Board Polish
**Rationale:** Last because it is cosmetic and highest-risk for regressions to existing working components. Visual baseline from Phase 1 screenshots enables before/after comparison. Must NOT change the API route contract or SWR hook configuration -- data layer changes are separate from presentation changes.
**Delivers:** Colored left borders on agent cards; hover tooltips for status details; responsive layout verified at desktop and mobile widths; all 7 agents rendering correctly; SWR polling confirmed still working after changes.
**Uses:** Tailwind CSS; shadcn/ui component styling; visual baseline screenshots from Phase 1
**Avoids:** Pitfall 8 (polish breaking working components)

### Phase Ordering Rationale

- Phases 1-3 are strictly sequential: curation frees budget, threshold tuning requires stable budget, retrieval/LEARNINGS depends on both.
- Phase 4 (dashboard panel) can technically start after Phase 1 but benefits from waiting until Phase 3 completes so the memory system it monitors is in its final state.
- Phase 5 (context indicators) is independent of Phases 2-4 but grouped after Phase 4 for dashboard stability.
- Phase 6 (polish) MUST be last because it is the only phase that touches existing working UI components.
- All phases that modify `openclaw.json` (Phase 2, possibly Phase 3) must use the restart strategy from Phase 1.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Memory Curation):** Needs manual inspection of all 304 MEMORY.md lines to classify CRITICAL vs REFERENCE vs STALE. This is judgment work, not pattern work -- research cannot substitute for reading each entry.
- **Phase 2 (Flush Thresholds):** Needs session token profiling data from production. Run `openclaw sessions` and gather actual numbers before planning changes.
- **Phase 4 (Memory Health Panel):** Needs to enumerate which agents have memory databases. SSH to EC2: `ls ~/clawd/agents/*/memory/`. Also verify better-sqlite3 can open sqlite-vec databases without the extension loaded.

Phases with standard patterns (skip research-phase):
- **Phase 3 (Retrieval + LEARNINGS):** Adding instructions to AGENTS.md and creating LEARNINGS.md are well-documented OpenClaw patterns. Verification via `openclaw context list` is straightforward.
- **Phase 5 (Context Indicators):** 31.1-RESEARCH.md already provides verified formulas, SQL queries, and production data. No additional research needed.
- **Phase 6 (Agent Board Polish):** CSS and component styling. Visual baseline + one-change-at-a-time discipline is sufficient.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies. v2.5 stack proven in production. Per-agent memory DB access follows the same better-sqlite3 pattern. |
| Features | HIGH | Features derived from v2.5 milestone audit (deferred phases 31.1, 31.2), MEMORY.md known constraints, and OpenClaw documentation on memory architecture. |
| Architecture | HIGH | Extends v2.5 architecture with same patterns (singletons, WAL, SWR polling). Cross-cutting concerns (db.ts extension, new query files) are well-understood. |
| Pitfalls | HIGH | Grounded in OpenClaw official docs, project MEMORY.md production history, and the v2.5 milestone audit. Gateway restart and MEMORY.md truncation are confirmed production behaviors, not theoretical. |

**Overall confidence:** HIGH

### Gaps to Address

- **Which agents have memory databases:** Must verify on EC2 before Phase 4. Assumed 4 of 7 based on agent types, but actual filesystem state is authoritative.
- **better-sqlite3 opening sqlite-vec databases:** The memory backend uses sqlite-vec for vector search. Verify that better-sqlite3 can open these files and read non-vector tables without loading the sqlite-vec extension. If it cannot, the memory health panel must read metadata differently.
- **MEMORY.md entry criticality:** No automated way to determine which entries are CRITICAL. Phase 1 requires human judgment to classify each of the 304 lines. The pitfalls research provides heuristics ("if this were unknown, what breaks?") but the actual classification is a manual task.
- **Session token profiles:** Flush threshold tuning (Phase 2) requires production data that does not exist yet. The data must be gathered as Phase 2's first step, not during research.
- **`openclaw context list` output format:** Used in Phase 3 for bootstrap budget verification. Assumed to show per-file sizes and total, but actual output format should be confirmed on EC2.

---

## Sources

### Primary (HIGH confidence)
- [OpenClaw Memory Documentation](https://docs.openclaw.ai/concepts/memory) -- memory architecture, daily logs, MEMORY.md curation, memory search
- [OpenClaw System Prompt Documentation](https://docs.openclaw.ai/concepts/system-prompt) -- bootstrap files, auto-loaded files, bootstrapMaxChars, truncation behavior (70/20/10 split)
- [OpenClaw Agent Workspace Documentation](https://docs.openclaw.ai/concepts/agent-workspace) -- workspace structure, writable paths, sandbox constraints
- [OpenClaw Troubleshooting](https://docs.openclaw.ai/gateway/troubleshooting) -- gateway restart behavior, session management
- [better-sqlite3 GitHub](https://github.com/WiseLibs/better-sqlite3) -- API, readonly flag, WAL mode, prepared statements
- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html) -- concurrent access model, checkpoint behavior
- Phase 31.1 RESEARCH.md (project internal) -- context usage indicator formulas, token field semantics, MODEL_CONTEXT_LIMITS, production data
- Phase 31 RESEARCH.md (project internal) -- agent board architecture, query patterns
- v2.5 MILESTONE-AUDIT.md (project internal) -- deferred phases 31.1/31.2, tech debt items, pending human verification
- Project MEMORY.md (project internal) -- EC2 constraints, gateway restart behavior, DM session loss, all known workarounds

### Secondary (MEDIUM confidence)
- [OpenClaw Memory Configuration Guide](https://moltfounders.com/openclaw-runbook/memory-configuration) -- flush thresholds, compaction settings, softThresholdTokens math
- [OpenClaw Memory Explained](https://lumadock.com/tutorials/openclaw-memory-explained) -- bootstrapMaxChars 70/20/10 split, daily log vs MEMORY.md distinction
- [OpenClaw Production Gotchas](https://kaxo.io/insights/openclaw-production-gotchas/) -- config drift, cron stale models, gateway restart issues
- [Pre-compaction memory flush bug #5457](https://github.com/openclaw/openclaw/issues/5457) -- flush uses stale token counts
- [Context overflow error #5771](https://github.com/openclaw/openclaw/issues/5771) -- bootstrap size management

### Tertiary (LOW confidence, needs verification)
- Which agents have memory databases (4 of 7 assumed, not verified on EC2 filesystem)
- better-sqlite3 compatibility with sqlite-vec database files (assumed compatible for non-vector tables, not tested)
- `openclaw context list` output format (assumed from documentation, not run locally)

---

*Research completed: 2026-02-23*
*Ready for roadmap: yes*
