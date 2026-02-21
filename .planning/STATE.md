# Project State: Proactive Daily Companion

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Mission Control Dashboard as single pane of glass for the entire pops-claw system.
**Current focus:** Phase 32 - Memory, Office & Visualization

## Current Position

Phase: 32 (4 of 4 in v2.5) — Memory, Office & Visualization
Plan: 03 of 3 in phase
Status: Ready
Milestone: v2.5 Mission Control Dashboard
Last activity: 2026-02-21 — Completed 32-02 (office view, /office page with 7 agent avatars and animated status)

Progress: [████████░░] 89% (8/9 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 61 (across v2.0 + v2.1 + v2.2 + v2.4 + v2.5)

**By Milestone:**

| Milestone | Phases | Plans | Timeline |
|-----------|--------|-------|----------|
| v2.0 | 11 | 22 | 10 days |
| v2.1 | 7 | 14 | 1 day |
| v2.2 | 5 | 8 | 2 days |
| v2.3 | 0 | 0 | Merged into v2.4 |
| v2.4 | 5 | 9 | 4 days |
| v2.5 | 4 | 9 | In progress |

**v2.5 Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| 29-01 | 6min | 2 | 15 |
| 29-02 | 12min | 3 | 9 |
| 30-01 | 4min | 2 | 11 |
| 30-02 | 8min | 3 | 5 |
| 31-01 | 5min | 2 | 4 |
| 31-02 | 3min | 2 | 2 |
| 32-02 | 13min | 2 | 5 |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- Phase 29-01: Removed Convex entirely rather than leaving dead code -- clean break for SQLite migration
- Phase 29-01: Kept date-fns for RelativeTime (already installed) rather than adding new library
- Phase 29-01: Stubbed activity-feed/global-search to placeholders for Phase 30 reimplementation
- Phase 29-02: Bound Next.js to 0.0.0.0:3001 for direct Tailscale access instead of loopback with SSH tunnel
- Phase 29-02: OOMScoreAdjust=500 on mission-control so gateway (-900) and Tailscale survive OOM events
- Phase 29-02: Database connections opened read-only with WAL check and busy_timeout=5000
- Phase 30-01: Query modules per subsystem (not one mega route) for independent error handling
- Phase 30-01: Activity feed merges coordination + observability + email DBs in JS (no ATTACH in read-only)
- Phase 30-01: Agents with no data show as idle (not down) to avoid false alarms for sage/ezra
- Phase 30-02: Kept Phase 29 DB status section at bottom of dashboard for infrastructure visibility
- Phase 30-02: Freshness indicator uses color transitions (amber at 60s, rose at 120s) with no manual refresh
- Phase 30-02: Activity feed is flat chronological list with type-based color coding (no grouping)
- Phase 31-01: Use input+output tokens only (not cache) for headline counts -- cache is 100x larger and not actionable
- Phase 31-01: Query both 'main' and 'bob' agent_ids for main agent across all DB queries
- Phase 31-01: Separate /api/agents route rather than extending /api/dashboard/agents to keep Phase 30 stable
- Phase 31-02: Used variant='error' instead of variant='destructive' for Badge -- matching project's actual shadcn config
- Phase 32-02: Simple SVG avatars with unique per-agent accessory shapes as placeholders for future illustrated assets
- Phase 32-02: 5-minute idle threshold matches existing agent board pattern for consistency
- Phase 32-02: Added Office link to NavBar between Agents and Calendar

### Research Flags

- Phase 29: SSH to EC2 and inspect actual schemas for all 5 databases before writing queries
- Phase 31: observability.db schema VERIFIED -- llm_calls and agent_runs tables confirmed with exact column names
- Phase 31: observability.db has meaningful data -- 8,912 agent_runs, 2,208 llm_calls, 1,023 calls in last 24h

### Roadmap Evolution

- Phase 31.1 inserted after Phase 31: Context Usage Indicators (URGENT)
- Phase 31.2 inserted after Phase 31: Agent Board Polish (URGENT)

### Open Items

- DMARC rua at theandykaufman@gmail.com: aggregate reports expected (Phase 27-01 checkpoint)
- Email-catchup cron delivery target error: "Action send requires a target" -- deferred

### Blockers

(None)

## Notes

- EC2 access via Tailscale: 100.72.143.9
- Mission Control codebase: ~/clawd/mission-control/ on EC2
- Existing stack: Next.js 14.2.15 + Tailwind + better-sqlite3 + cron-parser v5
- 5 databases: health.db, coordination.db, content.db, email.db, observability.db
- Current access: Direct Tailscale at http://100.72.143.9:3001 (SSH tunnel no longer needed)
- systemd service: mission-control.service (auto-starts, OOMScoreAdjust=500)
- UFW: port 3001 allowed from 100.64.0.0/10 (Tailscale CGNAT only)

---
*Last updated: 2026-02-21 -- Completed 32-02 (office view with SVG agent avatars). Ready for 32-03 (analytics charts).*
