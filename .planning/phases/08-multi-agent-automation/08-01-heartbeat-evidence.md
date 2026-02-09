# Heartbeat Stagger Verification Evidence

Captured: 2026-02-09T04:39Z

## Cron Expressions

| Job ID | Agent | Cron Expression | Offsets | Kind | Model |
|--------|-------|----------------|---------|------|-------|
| heartbeat-main-15m | main | `0,15,30,45 * * * *` | :00,:15,:30,:45 | systemEvent | default (N/A) |
| heartbeat-landos-15m | landos | `2,17,32,47 * * * *` | :02,:17,:32,:47 | agentTurn | haiku |
| heartbeat-rangeos-15m | rangeos | `4,19,34,49 * * * *` | :04,:19,:34,:49 | agentTurn | haiku |
| heartbeat-ops-15m | ops | `6,21,36,51 * * * *` | :06,:21,:36,:51 | agentTurn | haiku |

## Stagger Pattern

Within each 15-minute window:
- :00 main
- :02 landos (+2 min)
- :04 rangeos (+4 min)
- :06 ops (+6 min)

All 4 heartbeats firing with 2-minute stagger offsets. No overlap.

## Status

All 4 showing `lastStatus: "ok"` at time of verification.

## Daily Heartbeat

- **heartbeat-daily-001**: `0 15 * * *` (15:00 UTC daily), model=haiku, lastStatus=ok
