# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v2.7 — YOLO Dev

**Shipped:** 2026-02-26
**Phases:** 5 | **Plans:** 12

### What Was Built
- Autonomous overnight build pipeline (nightly cron → idea generation → prototype → yolo.db → self-evaluation)
- Mission Control /yolo page (build history cards, status filtering, SWR auto-refresh)
- Mission Control /tools page (CLI tool versions, health indicators, cron job status, clipboard actions)
- Morning briefing Section 11 + weekly YOLO digest + Slack DM build notifications
- Infrastructure: yolo.db (6th database), explicit sandbox bind-mounts, tools-health-check cron

### What Worked
- **3-day milestone delivery** — cleanest milestone yet (v2.0 took 10 days for 22 plans, v2.7 did 12 plans in 3 days)
- **Established patterns from v2.5 carried forward** — SWR, API routes, NavBar conventions, db-paths pattern all reused without re-learning
- **Real build validation during development** — builds #005 and #006 provided immediate proof the pipeline works
- **Phase 42 added mid-milestone** — scope expansion (/tools page) worked smoothly because infrastructure patterns were already set
- **Protocol docs over skills** — YOLO_BUILD.md as workspace reference doc continues to be more reliable than skill triggers for complex autonomous behavior

### What Was Inefficient
- **Phase 41 never formally verified** — summaries written but VERIFICATION.md skipped; should have been caught earlier
- **Phase numbering gap (34-37)** — phases jump from 33 to 38 due to earlier milestone scope changes; cosmetic but confusing
- **GSD tools broken** — `gsd-tools.cjs` module error (`Cannot find module './lib/test.cjs'`) prevented CLI-based milestone completion; all archival done manually
- **Nested Docker bind-mount debugging** — Phase 39-03 gap closure was needed because isolated cron sessions don't inherit main workspace mounts; this pattern should have been documented earlier

### Patterns Established
- **Explicit bind-mount pattern** — add mounts to `openclaw.json` sandbox config rather than relying on workspace inheritance for isolated sessions
- **Health-check cron → JSON → API → SWR** — pattern for any new observability page: EC2 script writes JSON, API route reads it, SWR refreshes
- **Protocol docs for autonomous behavior** — YOLO_BUILD.md (284 lines, 8 steps) as the canonical pattern for complex agent workflows
- **Phase addition mid-milestone** — scope can grow if patterns are established; Phase 42 was added after Phase 40 proved the dashboard pattern

### Key Lessons
1. **Isolated cron sessions need explicit binds** — they use a virtual sandbox, not the main workspace mount. Always add bind-mounts in openclaw.json when a cron needs file access.
2. **Formal verification should happen even for "obvious" phases** — Phase 41 was working but the missing VERIFICATION.md became tech debt that complicated the milestone audit.
3. **GSD tooling needs a health check** — the `gsd-tools.cjs` module error is blocking all CLI-based milestone operations. Should be fixed or documented as known issue.
4. **Pattern reuse accelerates delivery** — v2.7's 3-day delivery (12 plans) was possible because v2.5's dashboard patterns (SWR, API routes, db-paths) were directly reusable.

### Cost Observations
- Model mix: ~40% opus (planning/verification), ~50% sonnet (execution), ~10% haiku (cron builds)
- Sessions: ~8 sessions across 3 days
- Notable: Phase 42 was the fastest phase (3 plans in <30 min each) because all patterns were established

---

## Milestone: v2.8 — Bug Fixes & Dashboard Polish

**Shipped:** 2026-03-03
**Phases:** 6 | **Plans:** 14

### What Was Built
- Content pipeline fix — ghost content.db deleted, bind-mount fixed, SQL query patched for NULL/empty-string wp_post_id
- YOLO detail page — /yolo/{slug} with 12 features beyond MVP (syntax highlighting, ScoreRing, status timeline, iframe preview, prev/next nav, copy-to-clipboard)
- Build trend charts — success rate BarChart + avg score LineChart on /yolo page
- Agent board polish — token usage bars, cache hit rate %, 24h cost, uniform card height
- Build cleanup automation — 30-day retention with score >= 4 protection
- Verification backfill — VERIFICATION.md + SUMMARY.md for 3 phases with live EC2 SSH evidence

### What Worked
- **Audit-driven gap closure** — first milestone to run audit mid-stream, find gaps, create closure phases (47+48), and re-audit to PASSED
- **Deferred items from v2.5+v2.7 naturally fit** — context usage indicators, agent board polish, build artifacts, trend charts all landed in a single cohesive milestone
- **Live SSH evidence for verification** — gathering evidence from running EC2 rather than plan docs produces audit-quality proof
- **Phase 43 bug fix cascaded** — fixing the content pipeline ghost file exposed the SQL query gap, which Phase 48 closed

### What Was Inefficient
- **Phases 43-45 shipped without VERIFICATION.md or SUMMARY.md** — required Phase 48 backfill; should have written artifacts during execution
- **Two audit passes needed** — first audit found 4 unsatisfied requirements and 3 unverified phases; could have caught earlier if verification was part of each phase
- **BUG-02 re-scoping** — AeroVironment fly_status was in wrong repo (Supabase, not content.db); investigation time wasted before re-scope
- **Phase 46 plans listed as "TBD"** — planning was informal; worked fine for a 1-plan phase but inconsistent with other phases

### Patterns Established
- **Defensive SQL for nullable text columns** — `(col IS NULL OR col = '')` pattern avoids silent data misses in SQLite
- **Verification backfill pattern** — SSH evidence gathering batch → write all docs locally; viable catch-up for missed artifacts
- **Audit → gap closure → re-audit cycle** — milestone audit as a first-class workflow gate, not just documentation
- **Inline page for single-use views** — 837-line monolithic page.tsx is pragmatic when there's only one consumer

### Key Lessons
1. **Write VERIFICATION.md during phase execution, not after** — backfilling 3 phases in Phase 48 worked but was avoidable overhead
2. **Run milestone audit before the last phase, not after** — catching gaps earlier reduces closure phase count
3. **Deferred items cluster well** — v2.5/v2.7 deferrals created a natural "polish" milestone; this is a good pattern for debt paydown
4. **Re-scoping is a valid outcome** — BUG-02 moved to correct repo cleanly; don't force-fit requirements that belong elsewhere

### Cost Observations
- Model mix: ~35% opus (planning/audit), ~55% sonnet (execution), ~10% haiku (cron)
- Sessions: ~6 sessions across 5 days
- Notable: Phase 48 was the most efficient (4 plans worth of work in 2 plans, 7 min total execution)

---

## Milestone: v2.9 — Memory System Overhaul

**Shipped:** 2026-03-08
**Phases:** 4 | **Plans:** 8

### What Was Built
- Compaction config tuning (softThreshold 8K, reserve 40K) with QMD collection bootstrapping (21 files indexed)
- MEMORY.md (80 lines curated knowledge) deployed to Bob's workspace, indexed by QMD memory-root-main
- Redesigned flush prompt with structured sections + embedded sqlite3 queries for all 6 databases
- Retrieval protocol in AGENTS.md (4 trigger categories, example queries, consequence clause)
- Daily memory flush rescheduled from 07:00 UTC to 23:00 UTC (end-of-day capture)
- Automated health check script + dual alerting (system crontab + openclaw DM)

### What Worked
- **Single-day milestone delivery** — fastest milestone yet (8 plans in 1 day), because all EC2 operations followed established SSH+jq patterns
- **Fix-order dependency chain** — config → content → behavior → monitoring structure meant each phase naturally built on the previous one
- **Hot-loadable changes** — only Phase 51 required a gateway restart; Phases 52-54 were all hot-deployable (SCP files, edit cron, add script)
- **Commit-verified audit** — requirements verified inline during execution, no separate audit pass needed

### What Was Inefficient
- **Phases 52-54 missing SUMMARY.md** — work was done and committed but summaries not written during execution; had to backfill during milestone completion
- **SRCH-02 scope mismatch** — requirement specified hybrid search weights at openclaw.json level, but OpenClaw v2026.3.2 doesn't expose this config; marked N/A instead of revising requirement earlier
- **HLTH-02 SC3 pending** — 24h no-false-positive verification couldn't complete same day; accepted as known gap

### Patterns Established
- **QMD CLI env var pattern** — `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` must point to agent-specific paths for correct index access
- **Structured flush prompt** — embedded SQL queries in compaction prompt template for concrete daily summaries
- **Protocol doc for agent behavior** — retrieval protocol in AGENTS.md follows same pattern as CONTENT_TRIGGERS.md and YOLO_BUILD.md
- **Dual alerting** — system crontab for reliability + openclaw cron for user notification (5-min stagger)

### Key Lessons
1. **Write SUMMARY.md during execution** — this is the third consecutive milestone (v2.7, v2.8, v2.9) where summaries were backfilled; must become habit
2. **Hot-loadable design saves time** — batching the single restart into Phase 51 and making everything else hot-deployable was a significant efficiency win
3. **Config-focused milestones are fast** — no new code written, just config tuning and file deployment; 1-day delivery vs typical 2-5 days
4. **Requirement scope should match platform capabilities** — SRCH-02's hybrid weights couldn't be configured at the level specified; requirements should be validated against platform docs before committing

### Cost Observations
- Model mix: ~60% opus (planning/verification), ~40% sonnet (execution)
- Sessions: 2 sessions in 1 day
- Notable: Zero new code written — entirely config, scripts, and protocol docs

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Timeline | Key Change |
|-----------|--------|-------|----------|------------|
| v2.0 | 11 | 22 | 10 days | Initial setup, everything new |
| v2.1 | 7 | 14 | 1 day | Content pipeline, pattern reuse |
| v2.2 | 5 | 8 | 2 days | Email integration, external services |
| v2.4 | 5 | 9 | 4 days | Security hardening, careful validation |
| v2.5 | 4 | 9 | 2 days | Dashboard foundation, new stack |
| v2.6 | 1 | 4 | 2 days | Pipeline hardening, debugging |
| v2.7 | 5 | 12 | 3 days | Autonomous features, pattern reuse |
| v2.8 | 6 | 14 | 5 days | Bug fixes, dashboard polish, audit gap closure |
| v2.9 | 4 | 8 | 1 day | Memory system overhaul, config-only milestone |

### Top Lessons (Verified Across Milestones)

1. **Protocol docs > skill triggers** for complex autonomous behavior (verified v2.6 CONTENT_TRIGGERS.md + v2.7 YOLO_BUILD.md)
2. **Explicit bind-mounts in openclaw.json** required for any sandbox file access (verified v2.0 gh/sqlite3 + v2.6 content.db + v2.7 yolo-dev)
3. **Pattern reuse compounds** — each milestone is faster because conventions carry forward (SWR, API routes, db-paths, channel:ID format)
4. **Milestone audits catch real gaps** — v2.7 surfaced Phase 41 verification debt; v2.8 surfaced 4 unsatisfied reqs + 3 missing verification docs
5. **Write verification artifacts during execution** — backfilling is possible but wasteful (verified v2.8 Phase 48 backfill, v2.9 summary backfill)
6. **Config-only milestones are fast** — no new code = single-day delivery (verified v2.9: 8 plans in 1 day)
7. **Hot-loadable design reduces restart risk** — batch restarts into one phase, make everything else deployable without disruption (verified v2.9 Phase 51)
