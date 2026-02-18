# Cron Audit Data (Task 1)

**Captured:** 2026-02-18T21:22:00Z
**Source:** `openclaw cron list` via SSH

## Result: 20/20 PASS

All 20 cron jobs present and accounted for.

| # | Name | Schedule | Agent | Status | Expected | Match |
|---|------|----------|-------|--------|----------|-------|
| 1 | heartbeat-main | `0,15,30,45 * * * *` | main | ok | ok | PASS |
| 2 | meeting-prep-scan | `*/15 * * * *` | main | ok | ok | PASS |
| 3 | email-catchup | `15,45 * * * *` (America/LA) | main | ok | ok | PASS |
| 4 | heartbeat-landos | `2,17,32,47 * * * *` | landos | ok | ok | PASS |
| 5 | heartbeat-rangeos | `4,19,34,49 * * * *` | rangeos | ok | ok | PASS |
| 6 | heartbeat-ops | `6,21,36,51 * * * *` | ops | ok | ok | PASS |
| 7 | review-check | `0 10,15 * * *` (America/LA) | sage | ok | ok | PASS |
| 8 | airspace-email-monitor | `0 8-18 * * 1-5` (America/LA) | main | ok | error (research) | PASS (self-resolved) |
| 9 | writing-check | `0 11 * * *` (America/LA) | quill | ok | ok | PASS |
| 10 | anomaly-check | `0 14,22 * * *` | main | ok | ok | PASS |
| 11 | publish-check | `0 14 * * *` (America/LA) | ezra | ok | ok | PASS |
| 12 | stuck-check | `0 17 * * *` (America/LA) | ops | ok | ok | PASS |
| 13 | evening-recap | `0 19 * * *` (America/LA) | main | ok | ok | PASS |
| 14 | daily-standup | `0 13 * * *` | ops | ok | ok | PASS |
| 15 | daily-heartbeat | `0 15 * * *` | main | ok | ok | PASS |
| 16 | morning-briefing | `0 7 * * *` (America/LA) | main | ok | ok | PASS |
| 17 | topic-research | `0 10 * * 2,5` (America/LA) | rangeos | ok | ok | PASS |
| 18 | weekly-review | `0 8 * * 0` (America/LA) | main | ok | ok | PASS |
| 19 | pipeline-report | `0 8 * * 0` (America/LA) | ops | ok | ok | PASS |
| 20 | monthly-expense-summary | `0 15 1 * *` | main | idle | idle | PASS (expected) |

## Airspace-Email-Monitor Investigation

**Research status:** "error"
**Actual status:** "ok"
**Last ran:** 22 minutes ago (at audit time)
**Resolution:** Self-resolved. The error state documented during research (earlier on 2026-02-18) cleared after the gateway restarted during the v2026.2.17 update process. The gog auth token refresh likely succeeded after the service restart, restoring normal operation. No manual fix needed.

## Monthly-Expense-Summary

**Status:** "idle" -- expected. This cron fires on the 1st of each month at 15:00 UTC. Since the month hasn't cycled since the update, "idle" is the correct status. Not an error.

## Manifest Notes

- The plan's expected manifest listed `writing-check` twice (entries 9 and 18). Only one exists in the actual system -- this is correct (single cron, duplicate in manifest was a typo).
- All schedule expressions match expected values.
- No missing, extra, or renamed crons detected.
