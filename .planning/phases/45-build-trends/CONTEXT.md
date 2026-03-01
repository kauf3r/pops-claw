# Phase 45: Build Trends — Context

## Goal
Add success rate and self-score trend charts to the /yolo page so users can see YOLO build performance at a glance.

## Current State
- 8 builds in yolo.db, all `status=success`, all `self_score=4`
- /yolo page has filter bar + build card grid, no charts
- Analytics page has 4 Recharts charts (token area, pipeline bar, email line, cron pie) — established patterns
- Uses `ChartContainer` + `ChartTooltip` from shadcn/ui chart primitives
- Recharts v2.15.4, date-fns for formatting
- SWR for data fetching with 30s refresh
- DB is read-only via better-sqlite3 WAL mode

## Schema (builds table)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| date | TEXT | YYYY-MM-DD |
| status | TEXT | idea/building/testing/success/partial/failed |
| self_score | INTEGER | 1-5 scale |
| started_at | TEXT | ISO timestamp |
| completed_at | TEXT | ISO timestamp |
| duration_seconds | INTEGER | nullable |

## Key Files
- `src/app/yolo/page.tsx` — YOLO list page (add charts here)
- `src/lib/queries/yolo.ts` — DB queries (add trend query)
- `src/app/api/yolo/builds/route.ts` — API route (add trends endpoint or extend)
- `src/components/analytics/email-chart.tsx` — LineChart pattern to follow
- `src/components/analytics/token-chart.tsx` — AreaChart pattern
- `src/components/ui/chart.tsx` — ChartContainer/ChartTooltip/ChartConfig primitives
- `src/lib/db-paths.ts` — yolo DB at `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db`

## Design Decisions
- Two charts: success rate (bar) + avg self-score (line) — matches analytics page 2-chart wide pattern
- Group by date (daily) since builds are nightly
- Success rate = success builds / total builds per day (percentage)
- Self-score = average per day
- Small dataset (8 builds) — charts must look good with sparse data (dots visible, no empty stretches)
- Place charts BETWEEN header/filter bar and the build card grid
- Single API endpoint returning both trend datasets to minimize requests
