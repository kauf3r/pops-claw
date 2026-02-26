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

### Top Lessons (Verified Across Milestones)

1. **Protocol docs > skill triggers** for complex autonomous behavior (verified v2.6 CONTENT_TRIGGERS.md + v2.7 YOLO_BUILD.md)
2. **Explicit bind-mounts in openclaw.json** required for any sandbox file access (verified v2.0 gh/sqlite3 + v2.6 content.db + v2.7 yolo-dev)
3. **Pattern reuse compounds** — each milestone is faster because conventions carry forward (SWR, API routes, db-paths, channel:ID format)
4. **Milestone audits catch real gaps** — v2.7 audit surfaced Phase 41 verification debt before ship
