# 05-02 Cron Evidence

## wyze_weight Table Schema

```sql
CREATE TABLE wyze_weight (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL UNIQUE,
  weight_lbs REAL NOT NULL,
  bmi REAL,
  body_fat_pct REAL,
  muscle_mass_pct REAL,
  source TEXT DEFAULT "email",
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_wyze_date ON wyze_weight(date);
```

## Morning Briefing — Section 6 Added

Cron ID: `863587f3-bb4e-409b-aee2-11fe2373e6e0`
Schedule: `0 7 * * *` @ America/Los_Angeles (unchanged)

New Section 6 appended:
```
## 6. Home Environment (GV-05)
Use the Govee skill to read current sensor data. For each sensor, call the Govee API device state endpoint.
Report: room name, temperature (F), humidity (%). Flag any anomaly per SKILL.md thresholds (temp outside 60-85F, humidity outside 30-60%).
Format:
- Living Room: 72F, 45% humidity
- Bedroom: 70F, 42% humidity
If sensors are offline, note which ones.
```

## Weekly Review — Weight Trend Section Added

Cron ID: `058f0007-935b-4399-aae1-28f6735f09ce`
Schedule: `0 8 * * 0` @ America/Los_Angeles (unchanged)

New section added after Health Trends:
```
## Weight Trend
Query /workspace/health.db: SELECT date, weight_lbs, body_fat_pct FROM wyze_weight ORDER BY date DESC LIMIT 7.
If data exists, report: current weight, 7-day change (+/- lbs), body fat % if available.
If no data, say 'No Wyze scale data recorded this week.'
```

## Verification Results

- [x] wyze_weight table exists with all columns (id, date, weight_lbs, bmi, body_fat_pct, muscle_mass_pct, source, created_at)
- [x] idx_wyze_date index exists
- [x] Morning briefing contains 6 sections (original 5 + Home Environment)
- [x] Weekly review contains Weight Trend section with wyze_weight query
- [x] Morning briefing schedule unchanged: 7 AM PT daily
- [x] Weekly review schedule unchanged: Sunday 8 AM PT
