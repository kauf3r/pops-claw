# Deployed: Morning Briefing Section 10 (Agent Observability)

**Deployed to:** Morning briefing cron payload (ID: 863587f3-bb4e-409b-aee2-11fe2373e6e0)
**Modified:** 2026-02-19

## What Changed
Added Section 10 to the morning briefing cron message (jobs.json payload.message and payload.text fields).
Message length: 7,070 -> 7,665 characters.

## Section 10 Content
```
## 10. Agent Observability
Read /workspace/OBSERVABILITY.md for SQL queries and formatting.
Query /workspace/observability.db using sqlite3 to generate:
1. 24h per-agent summary table (turns, tokens, cost, models used)
2. Anomaly flags (warning at 2x 7-day avg, critical at 4x or repeated errors, zero-activity warning)
3. Error summary (count + most recent error per agent, last 24h)
4. Average latency per agent (last 24h)
5. Rate limit proximity estimate (daily tokens vs tier limits)
Format per OBSERVABILITY.md. If < 7 days of data exist, show cold-start message instead of anomaly flags.
```

## Verification
- Section 10 present in jobs.json: YES
- Gateway restarted and active: YES
- Cron test run status: ok
- Files accessible inside sandbox: YES (/workspace/observability.db, /workspace/OBSERVABILITY.md)
- sqlite3 queries work in container: YES (1,040 rows in llm_calls)
