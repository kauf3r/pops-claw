# Task 1: Restart gateway and start background soak test

## Execution

- **Started:** 2026-03-08T19:23:38Z
- **Completed:** 2026-03-08T19:25:34Z
- **Restart time:** 19:23 UTC (minute :23, safe window outside heartbeat/briefing)

## Deviation: [Rule 1 - Bug] Removed invalid config keys

Plan 01 added `vectorWeight` and `textWeight` under `agents.defaults.memorySearch` but OpenClaw v2026.3.2 does not recognize these keys. Gateway refused to start with "Config invalid" error.

**Fix:** Removed both keys via jq. The memorySearch section now contains only `provider` and `textWeight` (the recognized keys).

**Impact:** Search weight tuning from Plan 01 (SRCH-01, SRCH-02) cannot be applied via openclaw.json -- these may be QMD-level settings instead. QMD search itself still works (verified in Plan 01).

## Results

- Gateway restart: SUCCESS (active after 15s)
- Clean startup logs: YES (no compaction loop errors, no config validation errors)
- QMD memory startup armed: YES (`qmd memory startup initialization armed for agent "main"`)
- Gmail watcher bind conflict: pre-existing (not related to our changes)
- Soak test started at /tmp/soak-test-51.log (30-minute background monitor)
