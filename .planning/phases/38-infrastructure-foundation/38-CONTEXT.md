# Phase 38: Infrastructure Foundation - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Storage layer and sandbox access so Bob can write builds and log metadata. Creates yolo.db, the yolo-dev/ directory with bind-mount, and validates end-to-end from inside the sandbox. No cron jobs, no build logic, no dashboard — those are later phases.

</domain>

<decisions>
## Implementation Decisions

### Database schema
- Auto-increment integer primary key (id maps directly to build number 001, 002...)
- Status stored as TEXT with CHECK constraint: idea, building, testing, success, partial, failed
- self_score as INTEGER with CHECK(self_score BETWEEN 1 AND 5)
- created_at column with DEFAULT CURRENT_TIMESTAMP
- Composite index on (status, date) for dashboard filtering/sorting
- All columns per INFRA-01: id, date, slug, name, description, status, tech_stack, lines_of_code, files_created, self_score, self_evaluation, build_log, error_log, started_at, completed_at, duration_seconds

### Build numbering
- 3-digit zero-padded (001, 002, ..., 999) — ~2.7 years at nightly builds
- Slug format: lowercase, hyphens, max 30 characters, strip special chars
- Example: 001-weather-dashboard-app/
- Next number determined by querying yolo.db MAX(id) + 1 (DB is single source of truth, no directory scanning)
- Minimum files per build directory: README.md + ideas.md (POSTMORTEM.md only on failure, added in Phase 39)

### Sandbox bind-mount
- Single new mount: ~/clawd/yolo-dev/ → /workspace/yolo-dev/ (read-write)
- yolo.db lives inside yolo-dev/ at ~/clawd/yolo-dev/yolo.db — one mount covers DB and build dirs
- Standard rw permissions matching existing sandbox mounts, same UID mapping
- Phase 38 only adds yolo-dev/ mount — protocol docs (YOLO_BUILD.md, YOLO_INTERESTS.md) mounted in Phase 39
- Verification: Bob creates 000-test/ with README.md from inside sandbox as smoke test (keep as marker)

### Config batching
- Batch into single gateway restart: openclaw.json bind-mount config + yolo.db creation + directory setup
- Phase 39's cron job is a separate config change and restart in that phase
- Backup openclaw.json to openclaw.json.bak-20260224 before editing
- Validation order after restart: service status → mount check → DB write test → sandbox test (Bob creates 000-test/)

### Claude's Discretion
- Exact column types for text fields (TEXT vs VARCHAR — SQLite is flexible)
- Index naming conventions
- Backup file naming format details
- Any additional SQLite pragmas (WAL mode, etc.)

</decisions>

<specifics>
## Specific Ideas

- Build number = DB id — keep them 1:1 so there's never ambiguity about which directory maps to which row
- 000-test/ serves double duty: validates the infrastructure AND acts as a permanent smoke test marker
- Fail-fast validation: check each layer independently so debugging is targeted, not guesswork

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 38-infrastructure-foundation*
*Context gathered: 2026-02-24*
