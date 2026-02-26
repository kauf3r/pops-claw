# Project State: Proactive Daily Companion

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Proactive AI companion with Mission Control Dashboard as single pane of glass.
**Current focus:** v2.7 YOLO Dev -- Phase 42 complete (CLI Tools Dashboard)

## Current Position

Phase: 42 of 42 (CLI Tools Dashboard) -- COMPLETE
Plan: 3 of 3 in current phase
Status: Phase complete
Milestone: v2.7 YOLO Dev
Last activity: 2026-02-26 -- Completed 42-03 (/tools page UI, human-verified)

Progress: [██████████] 100% (10/10 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 66 (across v2.0 + v2.1 + v2.2 + v2.4 + v2.5 + v2.6)

**By Milestone:**

| Milestone | Phases | Plans | Timeline |
|-----------|--------|-------|----------|
| v2.0 | 11 | 22 | 10 days |
| v2.1 | 7 | 14 | 1 day |
| v2.2 | 5 | 8 | 2 days |
| v2.3 | 0 | 0 | Merged into v2.4 |
| v2.4 | 5 | 9 | 4 days |
| v2.5 | 4 | 9 | 2 days |
| v2.6 | 1 | 4 | 2 days |
| Phase 38 P01 | 2min | 2 tasks | 3 files |
| Phase 38 P02 | 3min | 2 tasks | 1 file |
| Phase 39 P01 | 4min | 2 tasks | 3 files |
| Phase 39 P02 | 45min | 2 tasks | 4 files |
| Phase 39 P03 | 30min | 2 tasks | 4 files |
| Phase 40 P01 | 3min | 2 tasks | 3 files |
| Phase 40 P02 | 5min | 3 tasks | 3 files |
| Phase 42 P01 | 4min | 2 tasks | 2 files + crontab |
| Phase 42 P02 | 5min | 2 tasks | 3 files |
| Phase 42 P03 | 2min | 3 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- Phase 38-02: Sandbox DB access uses Python sqlite3 module (not CLI sqlite3 or better-sqlite3 due to sandbox constraints)
- Phase 38-02: 000-test/ kept as permanent smoke test marker
- Phase 39-01: 001-chronicle got id=4 (AUTOINCREMENT gap from Phase 38 test inserts) -- next build gets id=5, no collision
- Phase 39-01: SCP used for deploying protocol docs to EC2 (cleaner than tee for 284-line files)
- Phase 39-02: Docker nested bind-mounts unreliable -- use workspace subdirectories instead of explicit bind-mounts
- Phase 39-02: yolo-dev canonical path is ~/clawd/agents/main/yolo-dev/ (served via main workspace mount)
- Phase 39-03: Isolated cron sessions use virtual sandbox with only explicit binds -- NOT the main workspace mount
- Phase 39-03: Added explicit bind mount for yolo-dev in openclaw.json (fixed cron-triggered builds)
- Phase 40-01: Excluded build_log/error_log/self_evaluation from API response (verbose, per CONTEXT.md)
- Phase 40-01: tech_stack parsed via comma-split (not JSON), matching yolo.db storage format
- Phase 40-01: Client-side filtering chosen over server-side query params (< 100 builds)
- Phase 40-02: Status border colors: emerald=success, amber=partial, rose=failed, blue=building/testing, zinc=idea
- Phase 40-02: NavBar.tsx (PascalCase) not nav-bar.tsx -- adapted to existing codebase convention
- Phase 42-01: Python True/False (not bash true/false) in embedded heredoc for JSON generation
- Phase 42-01: whisper version via pip show openai-whisper (--version exits 1)
- Phase 42-01: bd shown as red/not-installed (Mac-only tool, intentional on EC2)
- Phase 42-02: Fixed jobs.json parsing for { version, jobs } wrapper (plan assumed plain array)
- Phase 42-02: Cron health uses state.lastRunAtMs (not empty lastRun field)
- Phase 42-02: Shared types in src/lib/types/tools.ts for API + future UI
- Phase 42-03: NavBar.tsx (PascalCase) convention maintained from Phase 40
- Phase 42-03: Health dots (inline circles) over Badge pills for compact table density
- Phase 42-03: All sections expanded by default, clipboard copy with 2s checkmark feedback

### Open Items

- DMARC rua at theandykaufman@gmail.com: aggregate reports expected (Phase 27-01 checkpoint)
- Email-catchup cron delivery target error: "Action send requires a target" -- deferred
- Dead code: global-search.tsx returns null (Convex removal stub from Phase 29)

### Blockers

(None)

## Notes

- EC2 access via Tailscale: 100.72.143.9
- Mission Control codebase: ~/clawd/mission-control/ on EC2
- Stack: Next.js 14.2.15 + Tailwind + better-sqlite3 + SWR + Recharts + cron-parser v5
- 6 databases: health.db, coordination.db, content.db, email.db, observability.db, yolo.db
- Mission Control: http://100.72.143.9:3001 (direct Tailscale, no SSH tunnel)
- systemd service: mission-control.service (auto-starts, OOMScoreAdjust=500)
- YOLO Dev builds: ~/clawd/yolo-dev/ on EC2
- YOLO metadata: yolo.db at ~/clawd/yolo-dev/yolo.db (new SQLite database)

---
*Last updated: 2026-02-26 -- Completed 42-03 (/tools page UI). Phase 42 complete. All 10 v2.7 plans shipped. Phase 41 (Briefing & Notifications) still pending.*
