# Project State: Proactive Daily Companion

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Mission Control Dashboard as single pane of glass for the entire pops-claw system.
**Current focus:** Phase 29 - Infrastructure & Database Foundation

## Current Position

Phase: 30 (2 of 4 in v2.5) — Dashboard & Metrics
Plan: 01 of 2 in phase
Status: Ready
Milestone: v2.5 Mission Control Dashboard
Last activity: 2026-02-21 — Completed 29-02 (DB connection layer, status cards, systemd service, Tailscale bind)

Progress: [██░░░░░░░░] 22% (2/9 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 56 (across v2.0 + v2.1 + v2.2 + v2.4 + v2.5)

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- Phase 29-01: Removed Convex entirely rather than leaving dead code -- clean break for SQLite migration
- Phase 29-01: Kept date-fns for RelativeTime (already installed) rather than adding new library
- Phase 29-01: Stubbed activity-feed/global-search to placeholders for Phase 30 reimplementation
- Phase 29-02: Bound Next.js to 0.0.0.0:3001 for direct Tailscale access instead of loopback with SSH tunnel
- Phase 29-02: OOMScoreAdjust=500 on mission-control so gateway (-900) and Tailscale survive OOM events
- Phase 29-02: Database connections opened read-only with WAL check and busy_timeout=5000

### Research Flags

- Phase 29: SSH to EC2 and inspect actual schemas for all 5 databases before writing queries
- Phase 31: Verify observability.db schema (table/column names inferred, not confirmed)
- Phase 31: Verify observability.db has accumulated meaningful data since v2.4

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
*Last updated: 2026-02-21 -- Completed 29-02, Phase 29 complete. Ready for Phase 30.*
