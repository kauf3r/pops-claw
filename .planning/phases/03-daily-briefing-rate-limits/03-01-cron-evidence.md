# 03-01 Heartbeat Cron Model Routing Evidence

## Heartbeat Jobs After Update

| Job ID | Kind | Model | Agent |
|--------|------|-------|-------|
| heartbeat-main-15m | systemEvent | default (sonnet) | main |
| heartbeat-landos-15m | agentTurn | haiku | landos |
| heartbeat-rangeos-15m | agentTurn | haiku | rangeos |
| heartbeat-ops-15m | agentTurn | haiku | ops |
| heartbeat-daily-001 | agentTurn | haiku | main |

## Notes

- heartbeat-main-15m uses systemEvent kind which does not support per-job model override
  - systemEvent is inherently lightweight (no full agent turn)
  - Uses default model (sonnet) but minimal token consumption
- 4/5 heartbeat crons explicitly routed to haiku
- short-ribs-reminder (32564f8e-...) removed (stale one-time event, next run 351 days away)

## Cron List After Changes

```
heartbeat-ops-15m       heartbeat-ops     cron 6,21,36,51 * * * *     ops
heartbeat-main-15m      heartbeat-main    cron 0,15,30,45 * * * *     main
heartbeat-landos-15m    heartbeat-landos  cron 2,17,32,47 * * * *     landos
heartbeat-rangeos-15m   heartbeat-rangeos cron 4,19,34,49 * * * *     rangeos
evening-recap           evening-recap     cron 0 19 * * * @ LA        main
heartbeat-daily-001     daily-heartbeat   cron 0 15 * * *             main
morning-briefing        morning-briefing  cron 0 7 * * * @ LA         main
weekly-review           weekly-review     cron 0 8 * * 0 @ LA         main
```

Total: 8 jobs (was 9 before removing short-ribs-reminder)

*Captured: 2026-02-08*
