---
phase: 58-gbrain-infrastructure
plan: 01
subsystem: infra
tags: [gbrain, bun, pglite, ec2, knowledge-brain]

requires: []
provides:
  - "Bun 1.3.12 runtime on EC2 host"
  - "gbrain 0.10.1 CLI on EC2 host (via bun link)"
  - "PGLite database at ~/clawd/db/gbrain/brain.pglite/"
  - "gbrain config at ~/.gbrain/config.json"
  - "Path A/B determination: compiled binary fails PGLite WASM, Path B required"
affects: [58-02-sandbox-bind-mount]

tech-stack:
  added: [bun-1.3.12, gbrain-0.10.1, pglite-0.4.4]
  patterns: [bun-link-for-cli, pglite-embedded-postgres]

key-files:
  created:
    - "EC2: ~/.bun/bin/bun (Bun runtime)"
    - "EC2: ~/gbrain/ (gbrain repo clone)"
    - "EC2: ~/.bun/bin/gbrain (symlink)"
    - "EC2: ~/clawd/db/gbrain/brain.pglite/ (PGLite database)"
    - "EC2: ~/.gbrain/config.json (gbrain configuration)"
    - "EC2: ~/gbrain/bin/gbrain-linux-x64 (compiled binary - unusable for PGLite)"
  modified: []

key-decisions:
  - "Path A (compiled binary) fails with PGLite WASM bug -- Plan 02 must use Path B (Bun runtime bind-mount)"
  - "Moved PGLite data from default ~/.gbrain/brain.pglite to canonical ~/clawd/db/gbrain/brain.pglite"
  - "OpenAI API key already exists in openclaw.json (sk-proj-...) -- reused for gbrain embeddings"

patterns-established:
  - "Bun runtime install: curl installer + bun link for CLI tools (new pattern alongside npm global)"
  - "gbrain data at ~/clawd/db/gbrain/ follows established ~/clawd/db/ convention"

requirements-completed: [INFRA-01]

duration: 5min
completed: 2026-04-15
---

# Phase 58 Plan 01: Host Installation Summary

**Bun 1.3.12 + gbrain 0.10.1 installed on EC2 with PGLite database at canonical path, compiled binary confirmed broken (Path B needed for sandbox)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-15T20:52:21Z
- **Completed:** 2026-04-15T20:58:20Z
- **Tasks:** 2
- **Files modified:** 6 (all on EC2)

## Accomplishments
- Bun 1.3.12 installed on EC2 with PATH configured in .bashrc
- gbrain 0.10.1 installed via git clone + bun install + bun link (233 packages)
- PGLite database initialized at ~/clawd/db/gbrain/brain.pglite/ (Postgres 17, schema v4)
- gbrain doctor passes with 85/100 health score (DB connection, schema, embeddings, link integrity all OK)
- Test page created and searchable with 0.9970 relevance score
- Compiled binary (Path A) confirmed broken: `ENOENT: /$bunfs/root/pglite.data` -- Plan 02 must use Path B

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Bun and gbrain on EC2 host** - `f845b6a` (feat)
2. **Task 2: Initialize PGLite database and configure gbrain** - `f535297` (feat)

## Files Created/Modified
- `EC2: ~/.bun/bin/bun` - Bun 1.3.12 runtime
- `EC2: ~/gbrain/` - gbrain repo clone with 233 deps
- `EC2: ~/.bun/bin/gbrain` - Symlink to gbrain CLI entry point
- `EC2: ~/clawd/db/gbrain/brain.pglite/` - PGLite database directory (Postgres 17)
- `EC2: ~/.gbrain/config.json` - gbrain config (engine=pglite, database_path to canonical location)
- `EC2: ~/gbrain/bin/gbrain-linux-x64` - Compiled binary (99MB, version works but PGLite fails)

## Decisions Made
1. **Path A fails, Path B required for sandbox** -- Compiled binary (`bun build --compile`) reports version correctly but fails on any PGLite operation with `ENOENT: /$bunfs/root/pglite.data`. This confirms the known bug (electric-sql/pglite#414, oven-sh/bun#15032) persists even with PGLite 0.4.4. Plan 02 must bind-mount Bun binary + gbrain repo + wrapper script.
2. **Reuse existing OpenAI key** -- The `sk-proj-...` key already in openclaw.json (for openai-image-gen and openai-whisper-api) works for gbrain embeddings. No new key needed.
3. **Moved PGLite data to canonical path** -- gbrain init created the database at default `~/.gbrain/brain.pglite`. Moved to `~/clawd/db/gbrain/brain.pglite` and updated config.json to follow the established `~/clawd/db/` convention.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] gbrain init ran without --path flag**
- **Found during:** Task 2
- **Issue:** Running `gbrain init --help` actually triggered init (no separate help output), creating the database at the default `~/.gbrain/brain.pglite` instead of the planned `~/clawd/db/gbrain/brain.pglite`
- **Fix:** Moved the database directory to the canonical path and updated config.json
- **Files modified:** EC2: ~/.gbrain/config.json, ~/clawd/db/gbrain/brain.pglite/
- **Verification:** `gbrain doctor` passes, search works with the new path
- **Committed in:** f535297

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor path correction. No scope creep.

## Issues Encountered
- gbrain `init --help` flag does not work as expected -- it triggers actual initialization. The `--pglite` and `--path` flags may not exist as documented in research. The tool auto-detects the environment and initializes.
- gbrain doctor shows WARN for resolver_health, pgvector, and rls -- all expected for PGLite mode without skills directory. Health score 85/100 is well above the 60 threshold.

## User Setup Required
None - OpenAI API key already available in openclaw.json.

## Next Phase Readiness
- gbrain CLI fully functional on EC2 host
- PGLite database initialized and searchable at canonical path
- **CRITICAL for Plan 02:** Path A (compiled binary) does NOT work. Must use Path B:
  - Bind-mount `~/.bun/bin/bun` -> `/usr/local/bin/bun` (ro)
  - Bind-mount `~/gbrain` -> `/opt/gbrain` (ro)
  - Create wrapper script: `#!/bin/sh\nexec /usr/local/bin/bun /opt/gbrain/src/cli.ts "$@"`
  - Bind-mount `~/.gbrain` -> `/home/node/.gbrain` (rw)
  - `~/clawd/db/` -> `/workspace/db/` already mounted
  - Need sandbox-specific config.json with `/workspace/db/gbrain/brain.pglite` path
- OpenAI API key needs to be added as `OPENAI_API_KEY` in `agents.defaults.sandbox.docker.env`

## Self-Check: PASSED

- [x] Commit f845b6a (Task 1) exists in git log
- [x] Commit f535297 (Task 2) exists in git log
- [x] 58-01-SUMMARY.md exists on disk
- [x] 58-01-task1-results.md exists on disk
- [x] EC2: bun 1.3.12 accessible
- [x] EC2: gbrain 0.10.1 accessible
- [x] EC2: ~/clawd/db/gbrain/brain.pglite/ exists
- [x] EC2: ~/.gbrain/config.json exists

---
*Phase: 58-gbrain-infrastructure*
*Completed: 2026-04-15*
