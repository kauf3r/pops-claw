---
phase: 42-cli-tools-dashboard
plan: 01
subsystem: infra
tags: [bash, health-check, cron, json, ec2, cli-tools]

# Dependency graph
requires:
  - phase: 40-yolo-dashboard
    provides: Mission Control Next.js app running on EC2
provides:
  - tools-health-check.sh script writing structured JSON to ~/clawd/tools-health.json
  - 5-minute cron job keeping health data fresh
  - JSON schema with cli/plugins/scripts sections for /api/tools consumption
affects: [42-02 (API route reads tools-health.json), 42-03 (UI consumes API)]

# Tech tracking
tech-stack:
  added: []
  patterns: [bash-to-json via embedded python, cron-cached filesystem data]

key-files:
  created:
    - /home/ubuntu/scripts/tools-health-check.sh
    - /home/ubuntu/clawd/tools-health.json
  modified:
    - ubuntu user crontab (EC2)

key-decisions:
  - "Used Python True/False in bash echo for plugin dir checks (bash true/false not valid Python)"
  - "whisper version via pip show openai-whisper inside venv (--version exits 1)"
  - "bd shown as red/not-installed (Mac-only tool, intentionally absent on EC2)"
  - "5-minute cron interval with log output to tools-health-check.log"

patterns-established:
  - "Filesystem JSON cache: shell script writes JSON, API route reads it (same as /api/cron pattern)"
  - "Full binary paths in cron scripts to avoid PATH issues"

requirements-completed: [TOOLS-01]

# Metrics
duration: 4min
completed: 2026-02-26
---

# Phase 42 Plan 01: EC2 Health-Check Script Summary

**Bash health-check script writing 5-CLI/2-plugin/3-script inventory to tools-health.json every 5 minutes via cron**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-26T19:09:14Z
- **Completed:** 2026-02-26T19:13:20Z
- **Tasks:** 2
- **Files modified:** 2 (on EC2) + 1 crontab entry

## Accomplishments
- Health-check script gathers versions for openclaw, gog, node/npm, whisper, and bd (5 CLI tools)
- Plugin health (camofox-browser, secureclaw) checked via directory existence
- Script health (prune-sessions, voice-notes, clawdstrike) checked via file mtime
- JSON output validated: all expected sections, correct green/red statuses
- Cron registered at */5 interval with log output

## Task Commits

Each task was committed atomically:

1. **Task 1: Create tools-health-check.sh** - `a8be977` (feat)
2. **Task 2: Register 5-minute cron job** - EC2-only change (crontab), no local files

## Files Created/Modified
- `/home/ubuntu/scripts/tools-health-check.sh` - Health-check script gathering CLI, plugin, and script status
- `/home/ubuntu/clawd/tools-health.json` - Cached health data consumed by /api/tools (Plan 02)
- `ubuntu crontab` - */5 cron entry with log redirect to tools-health-check.log

## Decisions Made
- Used embedded Python (python3 heredoc) inside bash for JSON generation -- cleaner than jq for nested structures
- Plugin directory checks use `echo True/False` (Python-compatible) not `echo true/false` (bash-native)
- whisper version extracted via `pip show openai-whisper | grep ^Version` inside the venv, not `--version` flag which exits 1
- bd intentionally shown as red/not-installed per CONTEXT.md inventory (Mac-side tool)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed bash true/false vs Python True/False mismatch**
- **Found during:** Task 1 (script creation)
- **Issue:** Plan's script used `echo true/false` for plugin directory checks, but these are bash booleans -- Python requires `True/False`
- **Fix:** Changed `echo true || echo false` to `echo True || echo False` in CAMOFOX_DIR and SECURECLAW_DIR assignments
- **Files modified:** /home/ubuntu/scripts/tools-health-check.sh
- **Verification:** Script runs without NameError, JSON output valid
- **Committed in:** a8be977

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for script to produce valid JSON. No scope creep.

## Issues Encountered
None beyond the True/False mismatch fixed above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- tools-health.json is written and fresh at ~/clawd/tools-health.json
- Ready for Plan 02: TypeScript interfaces + GET /api/tools + POST /api/tools/refresh routes
- API route will use `readFile` to read the cached JSON (same pattern as /api/cron)

---
*Phase: 42-cli-tools-dashboard*
*Completed: 2026-02-26*
