# Phase 58: Insights & Dashboard - Research

**Researched:** 2026-04-12
**Domain:** Cross-repo data sync (EC2 SQLite -> Vercel PostgreSQL), correlation engine, Next.js 16 dashboard page
**Confidence:** HIGH

## Summary

Phase 58 spans two repositories: pops-claw (EC2, Bob's cron infrastructure) and andyos-dashboard (Vercel, Next.js 16). The EC2 side requires a new hourly sync cron that pushes growth.db and health.db data to andyOS API endpoints, an extension of the existing weekly review cron to include Oura-habit correlations and LLM journal theme extraction, and storage of results in growth.db weekly_reviews. The andyOS side requires new PostgreSQL tables for synced data (habits, habit_logs, oura_snapshots, commute_prompts, weekly_reviews), new API sync endpoints with GROWTH_API_KEY auth, new data fetching functions, and a /growth page following the established hub-card pattern with Recharts sparklines.

The codebase investigation reveals strong, consistent patterns across both repos. The andyOS dashboard uses server-component data fetching with Suspense boundaries, Drizzle ORM for PostgreSQL, and a well-defined hub card component pattern (async inner component + Suspense + HubCardSkeleton). The EC2 side has established cron-to-SQLite patterns and the weekly review cron is already enhanced with growth data sections from Phase 57. All building blocks exist -- this phase wires them together.

**Primary recommendation:** Split into 3 plans: (1) andyOS schema + sync API endpoints, (2) EC2 sync cron + weekly review correlation/theme extension, (3) andyOS /growth page + nav integration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: /growth page built on andyOS Dashboard (Vercel/PostgreSQL at dashboard.andykaufman.net), NOT Mission Control
- D-02: Goals and journal data already in andyOS PostgreSQL -- no migration needed for those
- D-03: Mission Control pages (agents, yolo, tools) stay on EC2 for now -- migration deferred to future phase/milestone
- D-04: This phase establishes the EC2->andyOS sync pattern that future MC migration will reuse
- D-05: Hourly sync cron on EC2 pushes data to andyOS API endpoints
- D-06: Sync targets: habits + habit_logs (growth.db), Oura snapshots (health.db), commute_prompts (growth.db), weekly_reviews (growth.db)
- D-07: andyOS stores synced data in PostgreSQL tables (mirrored schema)
- D-08: All /growth queries hit local PostgreSQL -- no cross-network calls at page load
- D-09: Sync API endpoints on andyOS authenticated via API key (same pattern as /api/growth/summary)
- D-10: SQL date-matching joins -- avg sleep score on habit-complete days vs not, mood vs HRV/readiness, etc.
- D-11: No stats libraries or LLM analysis for correlations -- keep it simple, understandable
- D-12: Correlation insights generated weekly via existing Sunday 8am weekly review cron
- D-13: Bob includes correlations in weekly review Slack DM (extends Phase 57 weekly review)
- D-14: LLM summarization -- Bob sends last 4 weeks of journal entries to Claude for theme extraction
- D-15: Themes categorized as: recurring, emerging, declining
- D-16: Theme analysis bundled into weekly review cron (not separate cron)
- D-17: Theme results stored in weekly_reviews record for dashboard display
- D-18: Hub-style card grid layout -- each domain as a card (Habits, Goals, Journal, Oura, Insights)
- D-19: Each card shows key metric + sparkline/mini chart (Recharts)
- D-20: Cards link to existing detail pages (/goals, /journal) -- /growth is the overview hub
- D-21: Habits card shows summary only (streaks, consistency, today's status) -- no separate /habits page
- D-22: Full-width "Weekly Insights" card at bottom with latest correlation and theme data
- D-23: Chart library: Recharts (already in andyOS stack)
- D-24: Follow existing andyOS patterns: shadcn cards, Suspense loading, SWR auto-refresh
- D-25: Extend Phase 57 weekly review cron to include: Oura-habit correlations (SQL), journal themes (LLM), and store results in growth.db weekly_reviews
- D-26: Sync cron pushes weekly_reviews to andyOS for dashboard display

### Claude's Discretion
- Exact PostgreSQL schema for synced tables (mirror SQLite structure)
- Sync cron implementation details (Python script vs shell script)
- API endpoint design for sync (batch vs per-table)
- Sparkline chart config and card sizing
- Error/loading/empty states for /growth cards
- SWR refresh interval for /growth page
- Exact correlation query SQL

### Deferred Ideas (OUT OF SCOPE)
- Mission Control -> andyOS migration (agents, yolo, tools pages) -- capture as Phase 59 or new milestone
- /habits detail page with calendar heatmap and per-habit history -- future phase
- Real-time sync (webhook-based instead of polling) -- future optimization
- Monthly/quarterly personal retrospective report (ADV-03) -- v2 requirements
- Adaptive prompt difficulty (ADV-01) -- v2 requirements
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INSG-01 | Bob correlates Oura health data with habit completion and mood patterns (requires 4+ weeks data) | SQL date-matching joins between health_snapshots and habit_logs. Weekly review cron already queries both databases. Extend with correlation SQL per D-10. |
| INSG-02 | Bob surfaces recurring journal themes across entries (requires 4+ weeks data) | LLM summarization via Claude in weekly review cron. Journal entries available from andyOS API or growth.db. Theme categories: recurring/emerging/declining per D-15. |
| INSG-03 | Mission Control /growth page displays habit charts, journal entries, goal progress, and Oura correlations | andyOS /growth page with 5 hub cards. Goals/journal cards already exist. New: Habits card, Oura card, Weekly Insights card. Data from local PostgreSQL after sync. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

### pops-claw CLAUDE.md
- Not a code repository -- contains planning docs for EC2 infrastructure
- EC2 access via SSH: `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9`
- Binary: `/home/ubuntu/.npm-global/bin/openclaw`
- Config: `~/.openclaw/openclaw.json` (JSON5, hot-reload)
- Service: `openclaw-gateway.service` (systemd user, loopback 127.0.0.1:18789)
- Workspace: `~/clawd/` on EC2

### andyOS CLAUDE.md
- **Framework**: Next.js 16 (App Router), React 19, TypeScript
- **DB**: PostgreSQL + Drizzle ORM -- schema in `@/lib/schema`, run `pnpm db:generate && pnpm db:migrate` after changes
- **ALWAYS run `pnpm lint && pnpm typecheck`** after completing changes
- **NEVER start dev server yourself** -- ask user
- **Use OpenRouter, NOT OpenAI directly** for any AI features
- **Package manager**: pnpm
- **API routes**: Next.js 16 Route Handlers (`route.ts`), export HTTP method handlers, return `Response` objects

## Standard Stack

### Core (andyOS Dashboard)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 (installed) / 16.2.3 (latest) | App Router, RSC, API routes | Already in project |
| React | 19.2.4 | UI framework | Already in project |
| Drizzle ORM | 0.45.1 (installed) / 0.45.2 (latest) | PostgreSQL queries + schema | Already in project |
| drizzle-kit | 0.31.9 | Schema migration generation | Already in project |
| Recharts | 3.7.0 (installed) / 3.8.1 (latest) | Sparkline charts | Already in project, used for Oura/financial charts |
| shadcn/ui | new-york preset | Card, Badge, Skeleton, Button, Separator | Already in project, all needed components installed |
| Lucide React | (installed) | Icons: Activity, Target, BookOpen, Heart, Lightbulb, Sprout | Already in project |
| BetterAuth | 1.4.18+ | Session-based auth on dashboard pages | Already in project |

### Core (EC2 / pops-claw)
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python 3 | (EC2 system) | Sync cron script, SQLite queries | Established pattern (habit-manager.py, process-voice-notes.py) |
| sqlite3 | (EC2 system) | growth.db and health.db queries | Bob's sandbox has sqlite3 CLI and python3 sqlite3 module |
| curl | (EC2 system) | HTTP requests to andyOS sync API | Available in sandbox, used by existing crons |
| openclaw CLI | v2026.4.1 | Cron management (`openclaw cron edit`) | Installed at /home/ubuntu/.npm-global/bin/openclaw |

### No new dependencies needed
Both repos already have everything required. No `npm install` or `pip install` needed.

## Architecture Patterns

### andyOS: Existing Drizzle Schema Pattern (CRITICAL)
All tables follow this exact pattern -- new sync tables MUST match:

```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/lib/schema.ts
export const someTable = pgTable(
  "some_table",
  {
    id: uuid("id")
      .primaryKey()
      .default(sql`gen_random_uuid()`),
    userId: text("user_id")
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    // ... domain columns ...
    createdAt: timestamp("created_at").defaultNow().notNull(),
  },
  (table) => [
    index("some_table_user_idx").on(table.userId),
    // ... additional indexes ...
  ]
);
```

**Key conventions:**
- PK: `uuid("id").primaryKey().default(sql\`gen_random_uuid()\`)` (NOT text, NOT integer)
- userId: `text("user_id")` FK to user.id with `onDelete: "cascade"`
- Timestamps: `timestamp("created_at").defaultNow().notNull()`
- Column naming: snake_case in DB, camelCase in Drizzle
- JSONB for arrays: `jsonb("column").$type<Type[]>().default([])`
- Indexes: always include userId index, plus domain-specific
- Upsert safety: `uniqueIndex` on natural keys for idempotent sync

### andyOS: Hub Card Component Pattern (CRITICAL)
Every hub card follows this exact structure. **New cards MUST replicate this pattern.**

```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/components/hub/goals-card.tsx
import { Suspense } from "react";
import Link from "next/link";
import { Icon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HubCardSkeleton } from "./card-skeleton";

interface XxxCardProps { userId: string; }

// Async inner component -- fetches data directly
async function XxxCardInner({ userId }: XxxCardProps) {
  const data = await getXxxData(userId);
  // Empty state or populated state
  return (
    <Card className="h-full hover:bg-accent/50 transition-colors cursor-pointer">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
          <Icon className="h-4 w-4" />
          Title
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-2xl font-bold tabular-nums">{value}</p>
        <p className="text-sm text-muted-foreground">{secondary}</p>
      </CardContent>
    </Card>
  );
}

// Outer component -- wraps with Link + Suspense
export function XxxCard({ userId }: XxxCardProps) {
  return (
    <Link href="/xxx" className="block h-full">
      <Suspense fallback={<HubCardSkeleton />}>
        <XxxCardInner userId={userId} />
      </Suspense>
    </Link>
  );
}
```

**Habits card variation:** No Link wrapper (no /habits detail page per D-21). No hover effect -- use `cursor-default` instead.
**Insights card variation:** No Link wrapper (self-contained). Uses `col-span-full` for full-width layout.

### andyOS: Server Component Page Pattern
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/app/(dashboard)/overview/page.tsx
import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";

export default async function GrowthPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");
  const userId = session.user.id;

  return (
    <div className="space-y-6">
      {/* Header */}
      {/* Card grids */}
    </div>
  );
}
```

### andyOS: API Key Auth Pattern (for sync endpoints)
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/app/api/growth/summary/route.ts
async function resolveUserId(): Promise<string | null> {
  // Try session-based auth first
  const session = await auth.api.getSession({ headers: await headers() });
  if (session) return session.user.id;

  // Fall back to API key auth for Bob's cron integration
  const headersList = await headers();
  const authHeader = headersList.get("authorization");
  if (!authHeader?.startsWith("Bearer ")) return null;

  const token = authHeader.slice(7);
  const expectedKey = process.env.GROWTH_API_KEY;
  if (!expectedKey || token !== expectedKey) return null;

  return process.env.GROWTH_DEFAULT_USER_ID ?? null;
}
```

### andyOS: OuraSparkline Pattern (for new sparklines)
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/components/health/oura-sparkline.tsx
"use client";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

interface SparklineProps {
  label: string;
  data: Array<{ v: number }>;
}

export function Sparkline({ label, data }: SparklineProps) {
  if (data.length === 0) return <div className="h-10 w-full" />;
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`spark-${label}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--chart-N))" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(var(--chart-N))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="v" stroke="hsl(var(--chart-N))"
            strokeWidth={1.5} fill={`url(#spark-${label})`}
            dot={false} isAnimationActive={false} connectNulls />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

**Chart color mapping per UI-SPEC:** --chart-1 (habits), --chart-2 (journal mood), --chart-3 (Oura readiness), --chart-4 (goals progress), --chart-5 (energy trend).

### andyOS: Dashboard Shell Navigation Pattern
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/components/dashboard-shell.tsx
// navSections array, LIFE section:
{
  label: "LIFE",
  items: [
    { label: "Calendar", href: "/calendar", icon: CalendarDays },
    { label: "Tasks", href: "/tasks", icon: CheckSquare },
    { label: "Projects", href: "/projects", icon: KanbanSquare },
    { label: "Chat", href: "/chat", icon: MessageSquare },
    { label: "Goals", href: "/goals", icon: Target },
    { label: "Journal", href: "/journal", icon: BookOpen },
    // ADD: { label: "Growth", href: "/growth", icon: Sprout },
  ],
},
```
Must also add to `moreSheetSections` LIFE array for mobile "More" sheet.

### EC2: Sync Cron Pattern (recommended)
```python
#!/usr/bin/env python3
"""Hourly sync: growth.db + health.db -> andyOS PostgreSQL"""
import sqlite3, json, os, urllib.request, sys

API_BASE = "https://dashboard.andykaufman.net/api/sync"
API_KEY = os.environ.get("GROWTH_API_KEY", "")

def sync_table(table_name, db_path, query, since_col="created_at"):
    """Read rows from SQLite, POST to andyOS sync endpoint."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # ... fetch rows, batch POST to API_BASE/table_name
    conn.close()

# Sync each table
sync_table("habits", "/workspace/db/growth.db", "SELECT * FROM habits")
sync_table("habit_logs", "/workspace/db/growth.db", "SELECT * FROM habit_logs")
# ... etc
```

### EC2: Weekly Review Cron Enhancement Pattern
The existing weekly-review cron (ID `058f0007-935b-4399-aae1-28f6735f09ce`) already has growth sections (Phase 57-02). For Phase 58, TWO new sections get appended to the cron payload:

1. **Oura-Habit Correlation** (D-10): SQL comparing avg sleep/readiness on habit-complete days vs non-complete days
2. **Journal Theme Extraction** (D-14): LLM summarization of last 4 weeks of journal entries, categorized as recurring/emerging/declining

Both results stored in growth.db `weekly_reviews` table (which already exists and is populated by the cron).

### Recommended Project Structure (andyOS changes)

```
src/
  app/(dashboard)/
    growth/
      page.tsx           # Server component, auth check, card grid
      loading.tsx         # Skeleton loading state
      error.tsx           # Error boundary
  components/
    hub/
      habits-card.tsx     # NEW: Habits hub card (no link, no detail page)
      oura-growth-card.tsx # NEW: Oura card for /growth (7-day sparkline)
      insights-card.tsx   # NEW: Full-width weekly insights card
      goals-card.tsx      # EXISTING: reuse as-is
      journal-card.tsx    # EXISTING: reuse as-is
      card-skeleton.tsx   # EXISTING: reuse as-is
  lib/
    data/
      growth.ts           # NEW: data fetching for habits, oura 7-day, insights
    schema.ts             # MODIFIED: add habit, habitLog, ouraSnapshot, commutePrompt, weeklyReview tables
  app/api/
    sync/
      habits/route.ts     # NEW: POST endpoint for habit sync
      habit-logs/route.ts # NEW: POST endpoint for habit_log sync
      oura/route.ts       # NEW: POST endpoint for Oura snapshot sync
      commute-prompts/route.ts # NEW: POST endpoint for commute_prompt sync
      weekly-reviews/route.ts  # NEW: POST endpoint for weekly_review sync
```

### Anti-Patterns to Avoid
- **Cross-network calls at page load**: /growth page MUST NOT call EC2 APIs during render (D-08). All data comes from local PostgreSQL.
- **Custom auth on sync endpoints**: Reuse the existing GROWTH_API_KEY Bearer token pattern. Don't invent a new auth mechanism.
- **Separate sparkline components per card**: Parameterize a single GrowthSparkline component with color prop, don't copy-paste OuraSparkline 4 times.
- **SQLite WAL issues from sync reads**: Sync cron reads from within Bob's sandbox where WAL is configured. No issues.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chart rendering | Custom SVG sparklines | Recharts AreaChart (v3.7+, already installed) | 40-line component vs hundreds; responsive, dark-mode-aware |
| Loading skeletons | Per-card custom skeletons | HubCardSkeleton (exists at hub/card-skeleton.tsx) | Consistent animation timing, already matches design system |
| Score coloring | Color threshold logic | getOuraScoreColor() from lib/health-types.ts | 4 thresholds already calibrated, used across health pages |
| API auth | New auth mechanism | resolveUserId() pattern from /api/growth/summary | Dual auth (session + API key) already proven |
| Date formatting | Manual date string building | toLocaleDateString("en-US", {...}) from HubGreeting | Consistent locale formatting |
| DB migrations | Manual SQL | `pnpm db:generate && pnpm db:migrate` (Drizzle Kit) | Type-safe, version-tracked, rollback-capable |

## EC2 Database Schemas (Source of Truth for Sync)

### growth.db Tables (SQLite)

**habits:**
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| name | TEXT NOT NULL UNIQUE | |
| description | TEXT | |
| frequency | TEXT DEFAULT 'daily' | daily or weekly |
| category | TEXT | |
| status | TEXT DEFAULT 'active' | active, paused, archived |
| grace_days | INTEGER DEFAULT 1 | forgiveness window |
| created_at | TEXT DEFAULT datetime('now') | |
| paused_at | TEXT | |
| archived_at | TEXT | |
| streak_current | INTEGER DEFAULT 0 | |
| streak_best | INTEGER DEFAULT 0 | |
| streak_last_date | TEXT | |
| total_completions | INTEGER DEFAULT 0 | |

**habit_logs:**
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| habit_id | INTEGER FK habits(id) | |
| date | TEXT NOT NULL | YYYY-MM-DD |
| status | TEXT DEFAULT 'done' | done, skipped |
| skip_reason | TEXT | |
| logged_at | TEXT DEFAULT datetime('now') | |
| UNIQUE(habit_id, date) | | |

**commute_prompts:**
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| date | TEXT NOT NULL UNIQUE | |
| prompt_text | TEXT NOT NULL | |
| prompt_category | TEXT | |
| delivered_at | TEXT | |
| response_text | TEXT | |
| response_source | TEXT | e.g., 'voice' |
| responded_at | TEXT | |
| key_insights | TEXT | Extracted by voice-notes-processor |

**weekly_reviews:**
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| week_start | TEXT NOT NULL UNIQUE | Monday YYYY-MM-DD |
| went_well | TEXT | Prose |
| to_improve | TEXT | Prose |
| insights | TEXT | Prose (correlations + reflection) |
| oura_summary | TEXT | Compact: "sleep:82/readiness:78/hrv:45/rhr:58" |
| habit_summary | TEXT | Compact: "meditate:5/7,exercise:3/7" |
| goal_summary | TEXT | Compact: "Get in shape:58%" |
| created_at | TEXT DEFAULT datetime('now') | |

### health.db Tables (SQLite)

**health_snapshots:**
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| date | TEXT NOT NULL UNIQUE | YYYY-MM-DD |
| sleep_score | INTEGER | 0-100 |
| sleep_efficiency | REAL | |
| sleep_duration_hours | REAL | |
| readiness_score | INTEGER | 0-100 |
| hrv_balance | REAL | |
| resting_hr | REAL | |
| body_temp_deviation | REAL | |
| activity_score | INTEGER | |
| steps | INTEGER | |
| active_calories | INTEGER | |
| raw_json | TEXT | Full API response |
| created_at | TEXT DEFAULT datetime('now') | |

**62+ days of data** (Feb 6 - Apr 12, 2026). Sufficient for 4+ week correlations required by INSG-01.

### PostgreSQL Mirror Schema Design (Recommendation)

New Drizzle tables should mirror the SQLite structure but use PostgreSQL conventions:

```typescript
// Recommended: src/lib/schema.ts additions
export const habit = pgTable("habit", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
  sourceId: integer("source_id").notNull(), // SQLite id for dedup
  name: text("name").notNull(),
  description: text("description"),
  frequency: text("frequency").default("daily").notNull(),
  category: text("category"),
  status: text("status").default("active").notNull(),
  graceDays: integer("grace_days").default(1),
  streakCurrent: integer("streak_current").default(0),
  streakBest: integer("streak_best").default(0),
  streakLastDate: text("streak_last_date"),
  totalCompletions: integer("total_completions").default(0),
  pausedAt: timestamp("paused_at"),
  archivedAt: timestamp("archived_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => [
  index("habit_user_idx").on(table.userId),
  uniqueIndex("habit_source_idx").on(table.userId, table.sourceId),
]);
```

**Key design choice: sourceId for dedup.** Since SQLite uses integer autoincrement IDs and PostgreSQL uses UUIDs, include a `sourceId` integer column that maps to the SQLite `id`. Combined with `userId`, this creates a unique dedup key for idempotent upserts during sync.

### Sync API Endpoint Design (Recommendation)

**Batch approach** (single endpoint per table, batch POST):

```typescript
// POST /api/sync/habits
// Body: { rows: HabitRow[] }
// Auth: Bearer GROWTH_API_KEY
// Response: { synced: number, errors: string[] }
export async function POST(req: Request) {
  const userId = await resolveSyncUserId(req);
  if (!userId) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const { rows } = await req.json();
  // Upsert each row using onConflictDoUpdate on (userId, sourceId)
  // Return count of synced rows
}
```

**Per-table endpoints** (not batch-all-tables) because:
1. Each table has different upsert keys and validation
2. Partial failures are isolated (one table failing doesn't block others)
3. Sync script can report per-table results

### Correlation SQL Patterns (D-10)

```sql
-- Avg sleep score on habit-complete days vs not (last 4 weeks)
SELECT
  CASE WHEN hl.date IS NOT NULL THEN 'habit_day' ELSE 'no_habit_day' END as day_type,
  AVG(hs.sleep_score) as avg_sleep,
  AVG(hs.readiness_score) as avg_readiness,
  COUNT(*) as day_count
FROM health_snapshots hs
LEFT JOIN (
  SELECT DISTINCT date FROM habit_logs WHERE status = 'done'
) hl ON hs.date = hl.date
WHERE hs.date >= date('now', '-28 days')
GROUP BY day_type;

-- Mood vs readiness (from andyOS journal + synced Oura)
-- Run in PostgreSQL after sync, or in weekly review cron against both DBs
```

### Journal Theme LLM Prompt Pattern (D-14)

```
Analyze the following journal entries from the last 4 weeks.
Identify themes and categorize each as:
- recurring: appeared in 3+ entries
- emerging: appeared in last 2 weeks but not before
- declining: appeared in first 2 weeks but not recently

Return JSON: { "themes": [{ "text": "theme name", "category": "recurring|emerging|declining", "count": N }] }

Entries:
[entry list with dates]
```

This runs within Bob's weekly review cron session. Bob has access to Claude API via the gateway. The response gets stored in weekly_reviews.insights column alongside the correlation text.

## Common Pitfalls

### Pitfall 1: Sync Deduplication Failures
**What goes wrong:** Hourly sync pushes duplicate rows, creating inflated habit counts or duplicate snapshots.
**Why it happens:** SQLite integer IDs don't map to PostgreSQL UUIDs. Without a stable dedup key, every sync creates new rows.
**How to avoid:** Use `uniqueIndex("table_source_idx").on(userId, sourceId)` on every synced table. Upsert with `onConflictDoUpdate`. The sourceId is the SQLite integer PK.
**Warning signs:** Row counts in PostgreSQL growing faster than expected. Duplicate entries in dashboard cards.

### Pitfall 2: Timezone Mismatch in Date Joins
**What goes wrong:** Correlation SQL fails to match health_snapshots dates with habit_logs dates because one uses UTC midnight and the other uses local time.
**Why it happens:** EC2 crons run in America/Los_Angeles (OPENCLAW_TZ), health.db dates are YYYY-MM-DD strings, growth.db dates are YYYY-MM-DD strings. PostgreSQL timestamps are UTC.
**How to avoid:** Sync script should transmit dates as YYYY-MM-DD strings. PostgreSQL should store date-type columns as `text("date")` (matching SQLite), not `timestamp`. Only use timestamp for created_at/updated_at.
**Warning signs:** Correlations return 0 matching days despite both datasets having data.

### Pitfall 3: Oura Sparkline Data Shape Mismatch
**What goes wrong:** Sparkline renders empty despite data existing.
**Why it happens:** OuraSparkline expects `Array<{ v: number }>` but data fetching returns different shapes (objects with named keys, or arrays with null gaps).
**How to avoid:** Data layer function should transform to `{ v: number }[]` before returning. Handle nulls by filtering or using 0.
**Warning signs:** Empty `<div className="h-10 w-full" />` rendering instead of chart.

### Pitfall 4: Sync Cron GROWTH_API_KEY Not Available in Sandbox
**What goes wrong:** Sync script gets 401 from andyOS API.
**Why it happens:** Environment variables must be in `agents.defaults.sandbox.docker.env` in openclaw.json, not just in `.env`. GROWTH_API_KEY was added in Phase 56-03 but only for Bob's main session.
**How to avoid:** Verify GROWTH_API_KEY is in sandbox env before writing the sync cron. Check with `openclaw config show`.
**Warning signs:** Sync script runs but all API calls return 401.

### Pitfall 5: Weekly Review Cron Payload Size
**What goes wrong:** Cron payload exceeds OpenClaw limits after adding correlation + theme sections.
**Why it happens:** Phase 57 already expanded the payload from 3KB to 9.4KB. Adding more sections could push it over.
**How to avoid:** Keep new sections concise -- reference Python scripts or commands rather than embedding full SQL in the payload. Test payload size after edit.
**Warning signs:** `openclaw cron edit` fails or truncates. Review DM is cut off.

### Pitfall 6: Drizzle Migration Not Run After Schema Changes
**What goes wrong:** Application errors at runtime because new tables don't exist in PostgreSQL.
**Why it happens:** Adding table definitions to schema.ts doesn't create them in the database. Must run `pnpm db:generate && pnpm db:migrate`.
**How to avoid:** Always run migration commands after schema.ts changes. Verify with `pnpm db:studio` or a test query.
**Warning signs:** Drizzle throws "relation does not exist" errors.

### Pitfall 7: Missing Sprout Icon Import
**What goes wrong:** Build fails when adding Growth to sidebar nav.
**Why it happens:** `Sprout` icon must be imported from lucide-react. The dashboard-shell.tsx already imports many icons but not Sprout.
**How to avoid:** Add `Sprout` to the lucide-react import statement in dashboard-shell.tsx.
**Warning signs:** TypeScript error on `Sprout` reference.

## Code Examples

### Verified: Hub Card Data Fetching Pattern
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/lib/data/hub.ts
// Pattern: async function returning typed result, called directly in server component
export async function getGoalsSummary(userId: string): Promise<GoalsSummaryResult> {
  const goals = await db
    .select({ title: goal.title, progress: goal.progress })
    .from(goal)
    .where(and(eq(goal.userId, userId), eq(goal.status, "active")))
    .orderBy(goal.progress);

  if (goals.length === 0) return { activeCount: 0, lowestGoal: null };
  const lowest = goals[0]!;
  return { activeCount: goals.length, lowestGoal: { title: lowest.title, progress: lowest.progress } };
}
```

### Verified: Oura Data Range Query
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/lib/data/health.ts
// Pattern: date range query for Oura metrics (reuse for 7-day sparkline on /growth)
export async function getOuraMetricsRange(userId: string, startDate: string, endDate: string): Promise<OuraMetricsRange> {
  const start = new Date(`${startDate}T00:00:00.000Z`);
  const end = new Date(`${endDate}T23:59:59.999Z`);
  // ... query healthMetric table, group by type, return point arrays
}
```

### Verified: Error Page Pattern
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/app/(dashboard)/overview/error.tsx
"use client";
export default function GrowthError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Card className="mx-auto max-w-md mt-12">
      <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
        <div className="rounded-full bg-destructive/10 p-3">
          <Sprout className="h-6 w-6 text-destructive" />
        </div>
        <div className="space-y-1.5">
          <p className="font-semibold">Something went wrong</p>
          <p className="text-sm text-muted-foreground">
            We couldn&apos;t load your growth dashboard. Please try again.
          </p>
        </div>
        <Button onClick={reset} size="sm">Try again</Button>
      </CardContent>
    </Card>
  );
}
```

### Verified: Upsert Pattern for Sync
```typescript
// Source: /Users/andykaufman/Desktop/Projects/andyos-dashboard/src/lib/data/health.ts
// Pattern: onConflictDoUpdate for idempotent syncs
await db
  .insert(healthMetric)
  .values(inserts)
  .onConflictDoUpdate({
    target: [healthMetric.userId, healthMetric.type, healthMetric.source, healthMetric.recordedAt],
    set: { value: sql`excluded.value` },
  });
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mission Control on EC2 for growth | andyOS Dashboard on Vercel | Phase 56 (Mar 2026) | Goals/journal already on andyOS; /growth continues this migration |
| Recharts v2 API | Recharts v3.7+ | Already installed | AreaChart API unchanged; ResponsiveContainer works the same |
| Next.js 15 | Next.js 16.1.6 | Already installed | Route Handlers, Server Components, Suspense patterns stable |

## Open Questions

1. **Sync cron: Python script in sandbox or standalone shell script?**
   - What we know: Existing crons use Python scripts bind-mounted to sandbox (habit-manager.py). Standalone shell scripts run outside sandbox (db-health-check.sh).
   - What's unclear: Whether sync cron should run inside Bob's sandbox (access to growth.db, GROWTH_API_KEY env) or as a standalone systemd timer
   - Recommendation: Python script bind-mounted to sandbox, triggered by a new openclaw cron (pattern matches habit-manager.py). This gives access to both growth.db and GROWTH_API_KEY already configured in sandbox env.

2. **weekly_reviews column expansion for correlation + theme data**
   - What we know: Current columns are went_well, to_improve, insights, oura_summary, habit_summary, goal_summary. Insights column holds free-form prose.
   - What's unclear: Whether to add dedicated `correlations_json` and `themes_json` columns or pack everything into the existing `insights` TEXT column
   - Recommendation: Add `correlations_json TEXT` and `themes_json TEXT` columns to weekly_reviews (ALTER TABLE on SQLite, new Drizzle columns on PostgreSQL). Structured JSON enables the /growth Insights card to parse and display specific items without regex-parsing prose.

3. **GROWTH_DEFAULT_USER_ID for sync endpoints**
   - What we know: /api/growth/summary uses `process.env.GROWTH_DEFAULT_USER_ID` to resolve the user for API key auth. Value is Andy's dashboard account ID: `bd03PGkQBkvkUKhnu1XDxT55PTHCQPOC`.
   - What's unclear: Nothing -- this is already configured and will work for sync endpoints too.
   - Recommendation: Reuse same env vars (GROWTH_API_KEY + GROWTH_DEFAULT_USER_ID). Extract the resolveUserId helper into a shared utility so sync routes don't duplicate it.

## Environment Availability

> Step 2.6: SKIPPED for andyOS (code-only changes, deployed via Vercel git push). EC2 environment confirmed from MEMORY.md and prior phase summaries.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js + pnpm | andyOS development | Yes | Node via Vercel | -- |
| PostgreSQL (Neon) | andyOS data storage | Yes | Managed | -- |
| Drizzle Kit | Schema migrations | Yes | 0.31.9 | -- |
| Recharts | Sparkline charts | Yes | 3.7.0 | -- |
| Python 3 | EC2 sync script | Yes | System Python on EC2 | -- |
| sqlite3 | EC2 DB queries | Yes | System on EC2 | -- |
| GROWTH_API_KEY | Sync auth | Yes | Configured in EC2 sandbox env + Vercel env | -- |
| SSH access | EC2 operations | Yes | Key at ~/.ssh/clawdbot-key.pem | -- |

**Missing dependencies:** None.

## Sources

### Primary (HIGH confidence)
- andyOS Dashboard codebase: `/Users/andykaufman/Desktop/Projects/andyos-dashboard/` -- schema.ts, hub components, API routes, data layer, dashboard-shell.tsx, health-types.ts all read directly
- pops-claw planning docs: Phase 55/56/57 CONTEXT.md, Phase 57-02 PLAN.md and SUMMARY.md -- growth.db schema, weekly review cron structure, health.db schema
- Phase 58 CONTEXT.md and UI-SPEC.md -- all locked decisions and design contract

### Secondary (MEDIUM confidence)
- npm registry: recharts 3.8.1, drizzle-orm 0.45.2, next 16.2.3 (latest versions verified 2026-04-12)
- MEMORY.md: EC2 infrastructure state, database locations, cron inventory

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified in codebase
- Architecture: HIGH -- patterns extracted directly from existing code, not hypothesized
- Pitfalls: HIGH -- based on actual codebase patterns and known issues from prior phases
- Sync design: MEDIUM -- sync cron is net-new, but follows established EC2 patterns
- Correlation SQL: MEDIUM -- SQL patterns are straightforward but untested against actual data distribution

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable -- no expected breaking changes in established stack)
