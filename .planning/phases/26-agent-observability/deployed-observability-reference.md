# Deployed: OBSERVABILITY.md Reference Doc

**Deployed to:** ~/clawd/agents/main/OBSERVABILITY.md (bind-mounted as /workspace/OBSERVABILITY.md)
**Created:** 2026-02-19

## Purpose
Reference document for Bob's morning briefing (Section 10: Agent Observability).
Contains SQL queries for reporting per-agent LLM usage, anomaly detection, errors, latency, and rate limit proximity.

## Sections
1. **24-Hour Summary Per Agent** - Token usage, cost, models per agent
2. **Anomaly Detection** - 7-day rolling average with 2x warning / 4x critical thresholds
3. **Error Summary** - Error count + last error per agent (24h)
4. **Average Latency Per Agent** - Response time averages (24h)
5. **Rate Limit Proximity** - Estimated daily token usage vs tier limits
6. **Data Retention** - Weekly cleanup of rows older than 90 days

## Backfill Results
- **llm_calls backfilled:** 543 rows (from cron JSONL with usage data)
- **agent_runs backfilled:** 7,247 rows (from all finished cron entries)
- **Date range:** 2026-01-25 to 2026-02-19
- **Agents represented:** main, landos, ops, rangeos
- **Source:** ~/.openclaw/cron/runs/*.jsonl (parsed by one-time Python script, then deleted)

## Key SQL: Anomaly Detection CTE
```sql
WITH daily AS (
  SELECT agent_id, DATE(created_at) as day,
    SUM(input_tokens + output_tokens) as daily_tokens,
    COUNT(*) as daily_turns
  FROM llm_calls
  WHERE created_at >= datetime('now', '-8 days')
  GROUP BY agent_id, DATE(created_at)
),
rolling AS (
  SELECT agent_id,
    AVG(daily_tokens) as avg_tokens_7d,
    COUNT(*) as days_with_data
  FROM daily WHERE day < DATE('now')
  GROUP BY agent_id
),
today AS (
  SELECT agent_id,
    SUM(input_tokens + output_tokens) as today_tokens
  FROM llm_calls
  WHERE created_at >= datetime('now', '-24 hours')
  GROUP BY agent_id
)
SELECT COALESCE(t.agent_id, r.agent_id) as agent_id,
  CASE
    WHEN r.days_with_data < 7 THEN 'collecting'
    WHEN t.today_tokens IS NULL AND r.avg_turns_7d > 0 THEN 'zero_activity'
    WHEN t.today_tokens > r.avg_tokens_7d * 4 THEN 'critical'
    WHEN t.today_tokens > r.avg_tokens_7d * 2 THEN 'warning'
    ELSE 'ok'
  END as status
FROM rolling r LEFT JOIN today t ON t.agent_id = r.agent_id;
```
