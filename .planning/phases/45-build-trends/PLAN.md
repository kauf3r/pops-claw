# Phase 45: Build Trends — Plan

## Plan 1: API + Query Layer

**Files:** `src/lib/queries/yolo.ts`, `src/app/api/yolo/trends/route.ts`

### Steps

1. Add `getYoloTrends()` to `src/lib/queries/yolo.ts`:
   - SQL: `SELECT date, COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successes, AVG(CASE WHEN self_score IS NOT NULL THEN self_score END) as avg_score FROM builds WHERE status IN ('success','partial','failed') GROUP BY date ORDER BY date ASC`
   - Returns `{ trends: Array<{ date: string; total: number; successes: number; successRate: number; avgScore: number | null }> }`
   - `successRate` = `Math.round((successes / total) * 100)`

2. Create `src/app/api/yolo/trends/route.ts`:
   - `GET` → `NextResponse.json(getYoloTrends())`
   - `export const dynamic = "force-dynamic"`
   - Error fallback returns `{ trends: [] }`

### Verify
- `curl localhost:3001/api/yolo/trends` returns JSON with trend data
- Each entry has date, total, successes, successRate (0-100), avgScore (1-5)

---

## Plan 2: Chart Components

**Files:** `src/components/yolo/success-rate-chart.tsx`, `src/components/yolo/score-trend-chart.tsx`

### Steps

1. Create `src/components/yolo/success-rate-chart.tsx`:
   - BarChart with single `successRate` bar (emerald green like success status)
   - X-axis: date formatted "MMM d" (date-fns)
   - Y-axis: 0-100% domain
   - Follow `ChartContainer`/`ChartTooltip`/`ChartConfig` pattern from analytics charts
   - Tooltip shows "X% (Y/Z builds)"
   - Height: 200px (smaller than analytics 300px — these are secondary to the build list)
   - Empty state: "No completed builds yet"

2. Create `src/components/yolo/score-trend-chart.tsx`:
   - LineChart with `avgScore` line (blue, like existing line chart pattern)
   - X-axis: date "MMM d"
   - Y-axis: domain [0, 5], ticks [1, 2, 3, 4, 5]
   - Dots visible (r=4) — important for sparse data
   - Tooltip shows "X.X / 5"
   - Height: 200px
   - Empty state: "No scored builds yet"

### Verify
- Components render with mock data, match analytics page styling
- Both handle empty arrays gracefully

---

## Plan 3: Page Integration

**Files:** `src/app/yolo/page.tsx`

### Steps

1. Add SWR fetch for `/api/yolo/trends` in YoloPage
2. Add chart section between filter bar and build grid:
   ```
   <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
     <Card> Success Rate chart </Card>
     <Card> Score Trend chart </Card>
   </div>
   ```
3. Use Card/CardHeader/CardTitle wrappers matching analytics page pattern
4. Loading skeleton: `h-[200px] animate-pulse bg-muted/30` (same pattern as analytics)
5. Charts auto-refresh via SWR (inherits default 30s from SWR config)

### Verify
- /yolo page shows two charts above the build card grid
- Charts render current data (8 builds, all success, all 4/5)
- Charts update when SWR refreshes
- Page still looks good on mobile (charts stack to single column)

---

## Success Criteria
- [x] /yolo shows success rate chart (builds completed vs failed per day)
- [x] /yolo shows avg self-score chart over time
- [x] Charts update automatically via SWR refresh
- [x] Visually consistent with analytics page chart styling

## Unresolved Questions
None — straightforward extension of existing patterns.
