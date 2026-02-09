# Anomaly Alerts

Check health metrics and environment data for anomalies. Alert via Slack only when thresholds are exceeded. If no anomalies, respond "No anomalies detected." and STOP.

**Execution mode:** Embedded (cron). Use HOST paths only.
- health.db: `/home/ubuntu/clawd/agents/main/health.db`
- sqlite3: `/usr/bin/sqlite3`

---

## 1. Health Metric Thresholds (Oura)

### Absolute Thresholds

Alert if ANY single day hits these:

| Metric | Threshold | Direction |
|--------|-----------|-----------|
| Sleep score | < 60 | Poor sleep |
| Readiness score | < 60 | Poor recovery |
| Resting HR | > 75 bpm | Elevated |
| HRV balance | < 15 | Very low variability |

### Trend Thresholds

Alert if 3-day moving average deviates from 7-day average:

| Metric | Deviation | Meaning |
|--------|-----------|---------|
| Sleep score | Drops > 15 points | Declining sleep quality |
| Readiness score | Drops > 15 points | Declining recovery |
| HRV balance | Drops > 20% | Stress/overtraining signal |
| Resting HR | Increases > 10 bpm | Elevated baseline HR |

### SQL Queries

```sql
-- Latest snapshot (absolute threshold check)
SELECT date, sleep_score, readiness_score, hrv_balance, resting_hr
FROM health_snapshots ORDER BY date DESC LIMIT 1;

-- 3-day average (trend check, recent window)
SELECT AVG(sleep_score) as avg_sleep, AVG(readiness_score) as avg_readiness,
       AVG(hrv_balance) as avg_hrv, AVG(resting_hr) as avg_hr
FROM (SELECT * FROM health_snapshots ORDER BY date DESC LIMIT 3);

-- 7-day average (trend baseline)
SELECT AVG(sleep_score) as avg_sleep, AVG(readiness_score) as avg_readiness,
       AVG(hrv_balance) as avg_hrv, AVG(resting_hr) as avg_hr
FROM (SELECT * FROM health_snapshots ORDER BY date DESC LIMIT 7);
```

**Trend comparison logic:**
- Calculate: `delta = baseline_7day - recent_3day`
- Sleep/Readiness: alert if delta > 15
- HRV: alert if `(baseline_7day - recent_3day) / baseline_7day > 0.20`
- Resting HR: alert if `recent_3day - baseline_7day > 10`

If fewer than 3 days of data exist, skip trend checks (not enough data). Still check absolute thresholds on the latest day.

---

## 2. Environment Thresholds (Govee)

**Note:** Currently no sensors are bound to the Govee account (all 11 devices are lights). When sensors are added, these thresholds apply.

### Comfort Range

| Metric | Low | High | Alert |
|--------|-----|------|-------|
| Temperature | < 60F | > 85F | Out of comfort range |
| Humidity | < 30% | > 60% | Out of comfort range |

### Rapid Change

- Temperature drop > 10F in 1 hour (possible HVAC issue)

### SQL Queries

```sql
-- Latest Govee readings (when sensors exist)
SELECT device_name, temperature_f, humidity_pct, reading_time
FROM govee_readings ORDER BY reading_time DESC LIMIT 10;

-- Rapid temp change detection (last 2 hours)
SELECT g1.device_name, g1.temperature_f as current_temp,
       g2.temperature_f as prev_temp,
       g1.reading_time as current_time, g2.reading_time as prev_time
FROM govee_readings g1
JOIN govee_readings g2 ON g1.device_id = g2.device_id
  AND g2.reading_time < g1.reading_time
  AND g2.reading_time > datetime(g1.reading_time, '-1 hour')
WHERE g1.reading_time > datetime('now', '-2 hours')
ORDER BY g1.reading_time DESC;
```

**If govee_readings table is empty or has no recent data, skip Govee checks silently.** Do not alert about missing sensor data.

---

## 3. Alert Logic

Execute in this order:

1. **Run health queries** using sqlite3 against `/home/ubuntu/clawd/agents/main/health.db`
2. **Check absolute thresholds** on the latest day first
3. **Check trend thresholds** (3-day vs 7-day) if 3+ days of data exist
4. **Run Govee queries** -- only if govee_readings has recent data (check count first)
5. **Evaluate results:**
   - If NO anomalies detected across all checks: respond "No anomalies detected." and **STOP** (do NOT send a Slack message)
   - If anomalies found: compose alert and proceed to Section 4

---

## 4. Slack Delivery

Send anomaly alerts to Andy's Slack DM: **D0AARQR0Y4V**

### Message Format

**Subject line:** "Health/Environment Alert"

For each anomaly include:
- What metric is anomalous
- Current value vs threshold or baseline
- Brief trend context (e.g., "3-day avg: 52 vs 7-day avg: 71")
- One actionable recommendation

**Example:**

> **Health/Environment Alert**
>
> **Sleep Score: 48** (threshold: 60)
> Last night's sleep score is well below the alert threshold. 3-day trend is also declining (avg 55 vs 7-day avg 72).
> Consider prioritizing sleep tonight -- earlier bedtime, limit screens after 9 PM.
>
> **Resting HR: 78 bpm** (threshold: 75)
> Slightly elevated resting heart rate. This can indicate stress, dehydration, or onset of illness.
> Stay hydrated and consider a lighter workout today.

Keep it **actionable** -- 2-3 sentences per anomaly, not a data dump.

---

## 5. Important Notes

- This runs in **embedded mode** (cron trigger). All file paths must be HOST paths.
- Do NOT use `/workspace/` paths.
- Do NOT alert about missing data or empty tables. Only alert on actual threshold violations.
- If health.db is locked or inaccessible, log the error but do not alert.
