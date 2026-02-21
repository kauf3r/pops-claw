# Phase 30: Dashboard & Metrics - Research

**Researched:** 2026-02-21
**Domain:** Next.js dashboard components, SWR polling, SQLite aggregate queries, cross-database activity feed
**Confidence:** HIGH

## Summary

Phase 30 transforms the Phase 29 infrastructure landing page (5 DB status cards) into a full operational dashboard that answers "is everything OK?" at a glance. The existing foundation is solid: `getDb()` singleton factory for 5 SQLite databases, SWR installed, shadcn Card/Badge/Table components ready, RelativeTime component built, dark zinc+blue palette active, and production systemd service running on Tailscale.

The work divides into two clear streams: (1) API routes + status cards for the 4 subsystems (agents, crons, content pipeline, email) with SWR 30-second polling and a freshness indicator, and (2) a chronological activity feed that merges entries from coordination.db (`agent_activity`), observability.db (`agent_runs`), email.db (`email_conversations`), and content.db (when populated). The activity feed replaces the deleted Convex-based feed with a pure SQLite implementation.

Key data reality from EC2 inspection (2026-02-21): coordination.db has 119 activity entries and 16 agent tasks. observability.db has 8,676 agent runs and 1,972 LLM calls across 5 agents (main, ops, rangeos, landos, quill). email.db has the schema but 0 rows. content.db is 0 bytes (no schema). 20 cron jobs all enabled, 19/20 with lastStatus "ok". 7 configured agents: main/Bob, landos/Scout, rangeos/Vector, ops/Sentinel, quill/Quill, sage/Sage, ezra/Ezra. Sage and Ezra have no observability data yet.

**Primary recommendation:** Build 4 new API routes (`/api/dashboard/agents`, `/api/dashboard/crons`, `/api/dashboard/metrics`, `/api/dashboard/activity`) that query the existing databases, add SWR polling with `refreshInterval: 30000` via a global `SWRConfig` in providers.tsx, then compose the landing page from 4 status cards + activity feed + pipeline/email metrics sections.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- 4-card grid layout: Agent Health, Cron Success, Content Pipeline, Email Quota
- Each card shows a single headline number with colored dot indicator (green/yellow/red)
- One-line detail beneath the headline number (e.g., "7/7 agents alive", "98% success rate")
- Clean and not busy -- no inline breakdowns or expandable sections
- Activity feed is a flat chronological list, newest first
- Each entry is one line: icon + timestamp + description
- Color-coded by type: agent=blue, cron=purple, email=green, content=orange
- No grouping by time or type, no nesting -- clean log view
- Replaces the existing Convex-based activity feed
- Content pipeline: 4 count badges (researched / written / reviewed / published)
- Email: sent/received/bounced counts + quota usage bar
- Numbers only -- no charts, no sparklines
- Simple and scannable
- Subtle "Updated X seconds ago" text in page header
- Color changes on staleness: normal -> yellow after 60s -> red after 120s
- No manual refresh button -- SWR polling handles everything at 30s intervals
- Auto-refresh is invisible when working normally

### Claude's Discretion
- Exact card dimensions and spacing
- Activity feed pagination approach (infinite scroll vs load more vs fixed window)
- Icon choices for activity types
- Empty state design for each section
- Error state handling when a database is unreachable

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Dashboard shows status cards for agent health summary, cron success rates, content pipeline counts, and email quota/bounce stats | 4 API routes querying coordination.db (agent heartbeats), cron jobs.json (success rates), content.db (article counts), email.db (sent/received/bounced). Status cards use shadcn Card + Badge with green/yellow/red dot indicators. See Architecture Patterns "Status Card Pattern" and Code Examples. |
| DASH-02 | Dashboard shows chronological activity stream from coordination.db replacing Convex feed | Activity feed API route merges `agent_activity` from coordination.db with `agent_runs` from observability.db (and email/content when populated), sorts by timestamp DESC, returns paginated results. Client renders with type-based color coding. See Architecture Patterns "Activity Feed Pattern". |
| DASH-03 | Dashboard auto-refreshes data every 30 seconds via SWR polling with freshness indicator | SWR `refreshInterval: 30000` set globally via `SWRConfig` in providers.tsx. Freshness indicator component tracks time since last successful fetch, changes color at 60s (yellow) and 120s (red). See Code Examples "SWR Polling Configuration" and "Freshness Indicator". |
| PIPE-01 | Content pipeline section shows article counts by status (researched, written, reviewed, published) | Query content.db `SELECT status, count(*) FROM articles GROUP BY status`. content.db is currently 0 bytes -- show "No articles yet" empty state with 4 zero-count badges. See Code Examples "Content Pipeline Query". |
| PIPE-02 | Email metrics section shows sent/received counts, bounce rate, and quota usage from email.db | Query email.db for direction-based counts and delivery_status. Currently 0 rows -- show zeros gracefully. Resend free tier: 100/day, 3000/month hardcoded as quota limits (no API for quota checking on free tier). See Code Examples "Email Metrics Query". |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | ^12.6.2 | SQLite read-only queries via existing `getDb()` factory | Already in use (Phase 29), synchronous API, singleton pattern established |
| swr | 2.4.0 | Client-side data fetching with 30s polling via `refreshInterval` | Already installed (Phase 29), stale-while-revalidate caching, focus revalidation |
| next | 14.2.15 | Framework, API routes in App Router | Already running in production |
| date-fns | ^3.6.0 | Timestamp formatting in activity feed | Already installed, `formatDistanceToNow` used by RelativeTime |
| lucide-react | ^0.475.0 | Icons for status cards and activity feed entries | Already installed, used in db-status-card |
| tailwindcss | ^3.4.10 | Styling, responsive grid | Already configured with zinc+blue palette |

### shadcn/ui Components (already installed)
| Component | Status | Use In Phase 30 |
|-----------|--------|-----------------|
| Card | Installed | 4 status cards, activity feed container |
| Badge | Installed (success/warning/error variants) | Pipeline count badges, status indicators |
| Button | Installed | Load more button for activity feed |
| Scroll Area | Installed | Activity feed scrollable container |

### No New Packages Needed
All dependencies for Phase 30 are already installed. No `npm install` required.

## Architecture Patterns

### Recommended Project Structure (New/Modified Files)
```
src/
├── app/
│   ├── api/
│   │   ├── dashboard/
│   │   │   ├── agents/route.ts      # NEW: agent health summary
│   │   │   ├── crons/route.ts       # NEW: cron success rates
│   │   │   ├── metrics/route.ts     # NEW: content pipeline + email metrics
│   │   │   └── activity/route.ts    # NEW: merged activity feed
│   │   ├── db-status/route.ts       # EXISTING (keep for DB health)
│   │   └── cron/route.ts            # EXISTING (raw cron data for calendar)
│   ├── page.tsx                      # REWRITE: full dashboard layout
│   └── providers.tsx                 # MODIFY: add SWRConfig with refreshInterval
├── components/
│   └── dashboard/
│       ├── status-card.tsx           # NEW: generic status card (headline number + dot + detail)
│       ├── activity-feed.tsx         # REWRITE: chronological feed from SQLite
│       ├── pipeline-metrics.tsx      # NEW: 4 count badges
│       ├── email-metrics.tsx         # NEW: sent/received/bounced + quota bar
│       ├── freshness-indicator.tsx   # NEW: "Updated X seconds ago" with color
│       ├── db-status-card.tsx        # EXISTING (keep for DB health view)
│       ├── system-status.tsx         # EXISTING (keep, maybe enhance)
│       └── relative-time.tsx         # EXISTING (reuse in activity feed)
├── lib/
│   ├── db.ts                        # EXISTING (getDb singleton factory)
│   ├── db-paths.ts                  # EXISTING (5 database paths)
│   ├── queries/
│   │   ├── agents.ts                # NEW: agent health queries
│   │   ├── crons.ts                 # NEW: cron status queries
│   │   ├── metrics.ts               # NEW: content + email metric queries
│   │   └── activity.ts              # NEW: cross-DB activity merge
│   └── constants.ts                 # NEW: agent list, email quota limits, colors
```

### Pattern 1: Status Card (User-Locked Design)
**What:** Each of the 4 status cards shows a single headline number, a colored dot (green/yellow/red), and a one-line detail. Clean, not busy.
**Implementation:**
```typescript
// src/components/dashboard/status-card.tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";

type StatusLevel = "ok" | "warn" | "error";

const DOT_COLORS: Record<StatusLevel, string> = {
  ok: "bg-emerald-500",
  warn: "bg-amber-500",
  error: "bg-rose-500",
};

interface StatusCardProps {
  title: string;
  headline: string;
  detail: string;
  status: StatusLevel;
  icon: React.ReactNode;
}

export function StatusCard({ title, headline, detail, status, icon }: StatusCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {title}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-2xl font-bold text-foreground">{headline}</span>
            <div className={`h-2.5 w-2.5 rounded-full ${DOT_COLORS[status]}`} />
          </div>
          <p className="text-sm text-muted-foreground truncate">{detail}</p>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Pattern 2: SWR Global Polling Configuration
**What:** Set `refreshInterval: 30000` globally so ALL dashboard data refreshes every 30 seconds without per-hook configuration.
**Why global:** Consistent refresh timing, single source of truth, easy to adjust.
```typescript
// src/app/providers.tsx
"use client";

import { SWRConfig } from "swr";

const fetcher = (url: string) => fetch(url).then((res) => {
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        refreshInterval: 30000,
        revalidateOnFocus: true,
        dedupingInterval: 5000,
      }}
    >
      {children}
    </SWRConfig>
  );
}
```
**Key:** providers.tsx must become a `"use client"` component since SWRConfig uses React context.

### Pattern 3: Activity Feed Cross-DB Merge
**What:** Merge entries from multiple SQLite databases into a single chronological feed.
**Why not ATTACH:** better-sqlite3 in read-only mode cannot ATTACH databases. Instead, query each DB separately and merge in JS.
**Pattern:**
1. Each query module exports a function returning `ActivityEntry[]` with a consistent shape
2. The API route calls each, concatenates, sorts by timestamp DESC, slices to page size
3. Client renders with type-based color coding (agent=blue, cron=purple, email=green, content=orange)

```typescript
// Activity entry shape (shared type)
interface ActivityEntry {
  id: string;          // "${source}-${rowId}" for uniqueness
  type: "agent" | "cron" | "email" | "content";
  summary: string;
  agentId?: string;
  timestamp: string;   // ISO 8601
}
```

### Pattern 4: Freshness Indicator
**What:** "Updated X seconds ago" text that tracks time since SWR's last successful data fetch.
**How:** Use SWR's `data` return to detect when data changes, reset a timer on each change.
**Color transitions:** Default text color -> amber after 60s -> rose after 120s.
```typescript
// src/components/dashboard/freshness-indicator.tsx
"use client";

import { useEffect, useState } from "react";

interface FreshnessIndicatorProps {
  lastUpdated: number; // Date.now() timestamp from parent
}

export function FreshnessIndicator({ lastUpdated }: FreshnessIndicatorProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    setElapsed(0);
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - lastUpdated) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  const color =
    elapsed > 120
      ? "text-rose-400"
      : elapsed > 60
        ? "text-amber-400"
        : "text-muted-foreground";

  return (
    <span className={`text-xs ${color} transition-colors`}>
      Updated {elapsed}s ago
    </span>
  );
}
```

### Pattern 5: Empty State Handling (Claude's Discretion)
**Recommendation:** When a database has no data (content.db is 0 bytes, email.db has 0 rows), show the status card with a "0" headline in muted styling and detail text like "No articles yet" or "No emails tracked". Do NOT hide the card or show an error -- partial data is normal for this system.

### Pattern 6: Error State Handling (Claude's Discretion)
**Recommendation:** When a database is unreachable (file missing, permission denied), the `getDb()` factory returns `null`. API routes should return a response with an `error` field alongside the data fields set to null/empty. The status card shows an amber dot with detail "Database unavailable". SWR will retry on next poll.

### Anti-Patterns to Avoid
- **Querying databases in client components:** All database access happens in API routes (server-side). Client components use SWR to fetch from API routes.
- **One mega API route for all dashboard data:** Split into focused routes (`/agents`, `/crons`, `/metrics`, `/activity`). This allows independent error handling and prevents one slow query from blocking everything.
- **Polling the cron jobs.json file too frequently:** The file is written by the gateway process. Reading it every 30s is fine (it's a local file read), but don't cache the file descriptor -- re-read fresh each time.
- **Importing better-sqlite3 in shared modules that might run on client:** Always keep DB imports in files under `src/lib/queries/` or `src/app/api/`, never in components.
- **Complex date arithmetic for freshness:** Use simple `Date.now()` subtraction, not date-fns for the 1-second-resolution freshness counter.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data polling | Custom setInterval + fetch | SWR `refreshInterval: 30000` | Dedup, error retry, focus revalidation, stale-while-revalidate built in |
| Relative timestamps | Manual date math | date-fns `formatDistanceToNow` via existing RelativeTime component | Edge cases with locale, DST, "just now" |
| Cross-DB query | ATTACH database SQL | Separate queries + JS merge + sort | better-sqlite3 read-only can't ATTACH; JS merge is simpler and handles missing DBs gracefully |
| Status dot colors | Inline color logic per card | Shared `StatusLevel` type + `DOT_COLORS` map | Consistent coloring across all 4 cards |
| Quota tracking | Resend API calls | Hardcoded constants (100/day, 3000/month) + count from email.db | Free tier has no quota API; count outbound emails per day/month |

**Key insight:** Phase 30 is pure read-only presentation. No writes, no mutations, no external API calls. Every data point comes from a local SQLite file or a local JSON file. Keep it simple.

## Common Pitfalls

### Pitfall 1: Stale SWR Data on Mount
**What goes wrong:** Dashboard shows cached data from previous session, looks outdated until first poll.
**Why it happens:** SWR caches responses in memory. On page refresh (full reload), cache is empty so this isn't an issue. On client-side navigation, stale cache may show.
**How to avoid:** `revalidateOnFocus: true` and `revalidateOnMount: true` (SWR defaults) handle this. No custom config needed.
**Warning signs:** Dashboard shows old data immediately on page load.

### Pitfall 2: Activity Feed N+1 Query Problem
**What goes wrong:** Querying each database for activity entries in a loop, causing many small queries per request.
**Why it happens:** Temptation to query per-agent or per-type in separate calls.
**How to avoid:** Use single aggregate queries per database with LIMIT. Each of the 4 source queries returns at most 50 entries, then merge and re-sort in JS.
**Warning signs:** API response times > 100ms for activity feed.

### Pitfall 3: content.db 0 Bytes Crashes Query
**What goes wrong:** Trying to run a SQL query against a 0-byte database file.
**Why it happens:** content.db is currently 0 bytes -- no schema exists.
**How to avoid:** The existing `getDb("content")` returns `null` for 0-byte files. Always check for null before querying. Return empty/zero data.
**Warning signs:** Unhandled exception in `/api/dashboard/metrics` route.

### Pitfall 4: Cron Jobs JSON vs SQLite Confusion
**What goes wrong:** Looking for cron data in SQLite databases when it's actually in a JSON file.
**Why it happens:** Everything else is in SQLite, so assumption is cron is too.
**How to avoid:** Cron job data lives at `/home/ubuntu/.openclaw/cron/jobs.json` (JSON file). Read with `fs.readFileSync`. The existing `/api/cron/route.ts` already reads this file. Cron success rates come from `state.lastStatus` and `state.consecutiveErrors` fields in each job object.
**Warning signs:** Looking for a "crons" table in SQLite.

### Pitfall 5: Providers.tsx Must Be "use client" for SWRConfig
**What goes wrong:** Build error or runtime error when wrapping children in SWRConfig without "use client" directive.
**Why it happens:** SWRConfig uses React context (createContext/useContext), which requires client component.
**How to avoid:** Add `"use client"` at top of providers.tsx. This is already a passthrough component, making it a client component is fine.
**Warning signs:** "createContext is not a function" or similar React server component errors.

### Pitfall 6: Agent Health "N/7" When Only 5 Have Data
**What goes wrong:** Dashboard shows "5/7 agents alive" because sage and ezra have no observability data.
**Why it happens:** Only main, ops, rangeos, landos, and quill have entries in observability.db. Sage and Ezra exist in config but have never run.
**How to avoid:** Agent health should check for recent heartbeats (agent_activity with type "heartbeat" in coordination.db) OR recent agent_runs in observability.db. Agents with no data should show as "idle" or "no data" rather than "down". The 7-agent list comes from a constant, not from database discovery.
**Warning signs:** Sage and Ezra permanently showing as "down" when they just haven't been activated.

### Pitfall 7: Timestamp Format Inconsistency
**What goes wrong:** Activity entries from different databases have different timestamp formats, causing sort failures.
**Why it happens:** coordination.db uses `TEXT` timestamps like "2026-02-21 06:36:05", observability.db uses ISO format "2026-02-21T06:36:06.232Z".
**How to avoid:** Normalize all timestamps to ISO 8601 in query results before merging. `new Date(timestamp).toISOString()` handles both formats.
**Warning signs:** Activity feed shows entries in wrong order or displays "Invalid Date".

## Code Examples

### Agent Health Query
```typescript
// src/lib/queries/agents.ts
import { getDb } from "@/lib/db";
import { AGENTS } from "@/lib/constants";

interface AgentHealthSummary {
  total: number;
  alive: number;
  detail: string;
  agents: Array<{
    id: string;
    name: string;
    lastSeen: string | null;
    status: "active" | "stale" | "idle";
  }>;
}

export function getAgentHealth(): AgentHealthSummary {
  const coordDb = getDb("coordination");
  const obsDb = getDb("observability");

  const agentStatuses = AGENTS.map((agent) => {
    let lastSeen: string | null = null;

    // Check coordination.db for recent heartbeats
    if (coordDb) {
      const row = coordDb
        .prepare(
          `SELECT created_at FROM agent_activity
           WHERE agent_id = ?
           ORDER BY created_at DESC LIMIT 1`
        )
        .get(agent.id) as { created_at: string } | undefined;
      if (row) lastSeen = row.created_at;
    }

    // Also check observability.db for recent runs
    if (obsDb) {
      const row = obsDb
        .prepare(
          `SELECT created_at FROM agent_runs
           WHERE agent_id = ?
           ORDER BY created_at DESC LIMIT 1`
        )
        .get(agent.id) as { created_at: string } | undefined;
      if (row && (!lastSeen || row.created_at > lastSeen)) {
        lastSeen = row.created_at;
      }
    }

    // Determine status based on recency
    let status: "active" | "stale" | "idle" = "idle";
    if (lastSeen) {
      const elapsed = Date.now() - new Date(lastSeen).getTime();
      const oneHour = 60 * 60 * 1000;
      status = elapsed < oneHour ? "active" : "stale";
    }

    return { id: agent.id, name: agent.name, lastSeen, status };
  });

  const alive = agentStatuses.filter((a) => a.status === "active").length;

  return {
    total: AGENTS.length,
    alive,
    detail: `${alive}/${AGENTS.length} agents alive`,
    agents: agentStatuses,
  };
}
```

### Cron Success Query
```typescript
// src/lib/queries/crons.ts
import fs from "fs";

const CRON_PATH = "/home/ubuntu/.openclaw/cron/jobs.json";

interface CronSummary {
  total: number;
  enabled: number;
  successRate: number; // 0-100
  withErrors: number;
  detail: string;
}

export function getCronSummary(): CronSummary {
  try {
    const raw = fs.readFileSync(CRON_PATH, "utf-8");
    const data = JSON.parse(raw);
    const jobs = data.jobs ?? [];

    const enabled = jobs.filter((j: any) => j.enabled).length;
    const withStatus = jobs.filter(
      (j: any) => j.state?.lastStatus != null
    );
    const ok = withStatus.filter(
      (j: any) => j.state.lastStatus === "ok"
    ).length;
    const withErrors = jobs.filter(
      (j: any) => (j.state?.consecutiveErrors ?? 0) > 0
    ).length;

    const successRate =
      withStatus.length > 0
        ? Math.round((ok / withStatus.length) * 100)
        : 100;

    return {
      total: jobs.length,
      enabled,
      successRate,
      withErrors,
      detail: `${successRate}% success rate`,
    };
  } catch {
    return {
      total: 0,
      enabled: 0,
      successRate: 0,
      withErrors: 0,
      detail: "Cron data unavailable",
    };
  }
}
```

### Content Pipeline Query
```typescript
// src/lib/queries/metrics.ts
import { getDb } from "@/lib/db";

interface PipelineMetrics {
  researched: number;
  written: number;
  reviewed: number;
  published: number;
  total: number;
}

export function getPipelineMetrics(): PipelineMetrics {
  const db = getDb("content");

  if (!db) {
    // content.db is 0 bytes -- no schema, no data
    return { researched: 0, written: 0, reviewed: 0, published: 0, total: 0 };
  }

  // Check if articles table exists
  const tableCheck = db
    .prepare(
      `SELECT name FROM sqlite_master WHERE type='table' AND name='articles'`
    )
    .get();

  if (!tableCheck) {
    return { researched: 0, written: 0, reviewed: 0, published: 0, total: 0 };
  }

  const rows = db
    .prepare(`SELECT status, count(*) as cnt FROM articles GROUP BY status`)
    .all() as Array<{ status: string; cnt: number }>;

  const counts: Record<string, number> = {};
  for (const row of rows) {
    counts[row.status] = row.cnt;
  }

  return {
    researched: counts["researched"] ?? 0,
    written: counts["written"] ?? 0,
    reviewed: counts["reviewed"] ?? 0,
    published: counts["published"] ?? 0,
    total: rows.reduce((sum, r) => sum + r.cnt, 0),
  };
}
```

### Email Metrics Query
```typescript
// src/lib/queries/metrics.ts (continued)

interface EmailMetrics {
  sent: number;
  received: number;
  bounced: number;
  total: number;
  bounceRate: number;     // 0-100
  dailySent: number;      // today's outbound count
  dailyQuota: number;     // 100 (Resend free tier)
  monthlyQuota: number;   // 3000 (Resend free tier)
  monthlySent: number;    // this month's outbound count
}

export function getEmailMetrics(): EmailMetrics {
  const db = getDb("email");

  const empty: EmailMetrics = {
    sent: 0, received: 0, bounced: 0, total: 0,
    bounceRate: 0, dailySent: 0, dailyQuota: 100,
    monthlyQuota: 3000, monthlySent: 0,
  };

  if (!db) return empty;

  try {
    // Overall counts
    const sent = (db.prepare(
      `SELECT count(*) as c FROM email_conversations WHERE direction = 'outbound'`
    ).get() as { c: number })?.c ?? 0;

    const received = (db.prepare(
      `SELECT count(*) as c FROM email_conversations WHERE direction = 'inbound'`
    ).get() as { c: number })?.c ?? 0;

    const bounced = (db.prepare(
      `SELECT count(*) as c FROM email_conversations
       WHERE direction = 'outbound' AND delivery_status = 'bounced'`
    ).get() as { c: number })?.c ?? 0;

    // Today's sends (UTC day)
    const dailySent = (db.prepare(
      `SELECT count(*) as c FROM email_conversations
       WHERE direction = 'outbound' AND date(created_at) = date('now')`
    ).get() as { c: number })?.c ?? 0;

    // This month's sends
    const monthlySent = (db.prepare(
      `SELECT count(*) as c FROM email_conversations
       WHERE direction = 'outbound'
       AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')`
    ).get() as { c: number })?.c ?? 0;

    const total = sent + received;
    const bounceRate = sent > 0 ? Math.round((bounced / sent) * 100) : 0;

    return {
      sent, received, bounced, total, bounceRate,
      dailySent, dailyQuota: 100, monthlyQuota: 3000, monthlySent,
    };
  } catch {
    return empty;
  }
}
```

### Activity Feed Query (Cross-DB Merge)
```typescript
// src/lib/queries/activity.ts
import { getDb } from "@/lib/db";

export interface ActivityEntry {
  id: string;
  type: "agent" | "cron" | "email" | "content";
  summary: string;
  agentId?: string;
  timestamp: string;
}

const PAGE_SIZE = 50;

export function getActivity(offset: number = 0): {
  entries: ActivityEntry[];
  hasMore: boolean;
} {
  const entries: ActivityEntry[] = [];

  // Source 1: coordination.db agent_activity
  const coordDb = getDb("coordination");
  if (coordDb) {
    const rows = coordDb
      .prepare(
        `SELECT id, agent_id, activity_type, summary, created_at
         FROM agent_activity
         ORDER BY created_at DESC
         LIMIT 100`
      )
      .all() as Array<{
        id: number;
        agent_id: string;
        activity_type: string;
        summary: string;
        created_at: string;
      }>;

    for (const row of rows) {
      entries.push({
        id: `coord-${row.id}`,
        type: "agent",
        summary: row.summary ?? `${row.activity_type} by ${row.agent_id}`,
        agentId: row.agent_id,
        timestamp: new Date(row.created_at).toISOString(),
      });
    }
  }

  // Source 2: observability.db agent_runs (errors only, to avoid noise)
  const obsDb = getDb("observability");
  if (obsDb) {
    const rows = obsDb
      .prepare(
        `SELECT id, agent_id, error, created_at
         FROM agent_runs
         WHERE success = 0
         ORDER BY created_at DESC
         LIMIT 50`
      )
      .all() as Array<{
        id: number;
        agent_id: string;
        error: string | null;
        created_at: string;
      }>;

    for (const row of rows) {
      entries.push({
        id: `obs-${row.id}`,
        type: "agent",
        summary: `Error: ${row.error ?? "unknown"} (${row.agent_id})`,
        agentId: row.agent_id,
        timestamp: new Date(row.created_at).toISOString(),
      });
    }
  }

  // Source 3: email.db email_conversations (when populated)
  const emailDb = getDb("email");
  if (emailDb) {
    try {
      const rows = emailDb
        .prepare(
          `SELECT id, direction, from_addr, to_addr, subject, created_at
           FROM email_conversations
           ORDER BY created_at DESC
           LIMIT 50`
        )
        .all() as Array<{
          id: number;
          direction: string;
          from_addr: string;
          to_addr: string;
          subject: string | null;
          created_at: string;
        }>;

      for (const row of rows) {
        const dir = row.direction === "inbound" ? "Received" : "Sent";
        entries.push({
          id: `email-${row.id}`,
          type: "email",
          summary: `${dir}: ${row.subject ?? "(no subject)"}`,
          timestamp: new Date(row.created_at).toISOString(),
        });
      }
    } catch {
      // email.db may have 0 rows, that's fine
    }
  }

  // Sort all entries by timestamp DESC
  entries.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  // Paginate
  const page = entries.slice(offset, offset + PAGE_SIZE);
  return { entries: page, hasMore: entries.length > offset + PAGE_SIZE };
}
```

### Constants File
```typescript
// src/lib/constants.ts

export const AGENTS = [
  { id: "main", name: "Bob" },
  { id: "landos", name: "Scout" },
  { id: "rangeos", name: "Vector" },
  { id: "ops", name: "Sentinel" },
  { id: "quill", name: "Quill" },
  { id: "sage", name: "Sage" },
  { id: "ezra", name: "Ezra" },
] as const;

export const AGENT_COUNT = AGENTS.length; // 7

// Resend free tier limits
export const EMAIL_DAILY_QUOTA = 100;
export const EMAIL_MONTHLY_QUOTA = 3000;

// Activity feed type colors (Tailwind classes)
export const ACTIVITY_COLORS: Record<string, string> = {
  agent: "text-blue-400",
  cron: "text-purple-400",
  email: "text-emerald-400",
  content: "text-orange-400",
};
```

### Dashboard API Route Example
```typescript
// src/app/api/dashboard/agents/route.ts
import { NextResponse } from "next/server";
import { getAgentHealth } from "@/lib/queries/agents";

export const dynamic = "force-dynamic";

export function GET() {
  try {
    const health = getAgentHealth();
    return NextResponse.json(health);
  } catch (error) {
    return NextResponse.json(
      { total: 7, alive: 0, detail: "Error loading agent data", agents: [], error: String(error) },
      { status: 500 }
    );
  }
}
```

### SWR Usage in Dashboard Page
```typescript
// Snippet from rewritten src/app/page.tsx
"use client";

import useSWR from "swr";
import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [lastUpdated, setLastUpdated] = useState(Date.now());

  const { data: agents } = useSWR("/api/dashboard/agents");
  const { data: crons } = useSWR("/api/dashboard/crons");
  const { data: metrics } = useSWR("/api/dashboard/metrics");
  const { data: activity } = useSWR("/api/dashboard/activity");

  // Track freshness -- reset timer when any data changes
  useEffect(() => {
    setLastUpdated(Date.now());
  }, [agents, crons, metrics, activity]);

  // ... render status cards, activity feed, metrics
}
```

### Activity Feed Pagination (Claude's Discretion)
**Recommendation: Fixed window with "Load more" button.**
- Show 50 most recent entries by default
- "Load more" button at bottom fetches next 50 (offset parameter)
- Simpler than infinite scroll (no intersection observer), less jarring than full pagination
- SWR polling refreshes the visible window every 30s

## Discovered Facts (from EC2 Inspection 2026-02-21)

### Database Content Summary

| Database | Table | Rows | Key Fields for Dashboard |
|----------|-------|------|--------------------------|
| coordination | agent_activity | 119 | agent_id, activity_type, summary, created_at |
| coordination | agent_tasks | 16 | agent_id, title, status, priority |
| coordination | agent_messages | 0 | (empty) |
| coordination | user_calendar_tasks | 0 | (empty) |
| observability | agent_runs | 8,676 | agent_id, success (0/1), error, duration_ms, created_at |
| observability | llm_calls | 1,972 | agent_id, model, input_tokens, output_tokens, created_at |
| email | email_conversations | 0 | direction, delivery_status, subject, created_at |
| health | health_snapshots | 14 | date, sleep_score, readiness_score |
| content | (no schema) | 0 | File is 0 bytes |

### Agent Activity (coordination.db)
- 5 agents with activity: main, ops, rangeos, landos, quill
- Activity types: primarily "heartbeat" (every 15 min for ops/rangeos/landos)
- Most recent: 2026-02-21 06:36:05 (ops heartbeat)

### Agent Runs (observability.db)
| Agent ID | Total Runs | Successes | Failures |
|----------|-----------|-----------|----------|
| main | 3,813 | 3,793 | 20 |
| ops | 1,648 | 1,647 | 1 |
| rangeos | 1,626 | 1,624 | 2 |
| landos | 1,586 | 1,585 | 1 |
| quill | 3 | 3 | 0 |
| sage | 0 | 0 | 0 |
| ezra | 0 | 0 | 0 |

### Cron Jobs (jobs.json)
- 20 total jobs, 20 enabled, 0 disabled
- 19/20 with lastStatus "ok", 1 with lastStatus null (monthly-expense-summary, never ran)
- 0 with consecutiveErrors > 0
- Agent distribution: main (7), ops (2), rangeos (1), landos (1), None/unassigned (9)

### Agent Registry (openclaw.json)
| ID | Name | Has Data |
|----|------|----------|
| main | Bob | Yes (3,813 runs, 119 activities) |
| landos | Scout | Yes (1,586 runs) |
| rangeos | Vector | Yes (1,626 runs) |
| ops | Sentinel | Yes (1,648 runs) |
| quill | Quill | Yes (3 runs) |
| sage | Sage | No (0 runs, no activities) |
| ezra | Ezra | No (0 runs, no activities) |

### Content Pipeline Status Mapping
When content.db gets populated, the `articles` table is expected to have a `status` column with values: "researched", "written", "reviewed", "published". This matches the pipeline phases from v2.1 (Phases 12-18). Currently no articles exist.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Convex cloud feed | SQLite local queries + SWR polling | Phase 29 removed Convex | No external dependencies, sub-ms query latency |
| Single monolith page | Focused API routes per subsystem | Phase 30 (this phase) | Independent error handling, parallel SWR fetches |
| No refresh | 30-second SWR polling | Phase 30 (this phase) | Always-current dashboard without WebSockets |

## Open Questions

1. **Content pipeline table name and schema**
   - What we know: content.db is 0 bytes, no schema exists. The content pipeline was built in v2.1 Phases 12-18.
   - What's unclear: Exact table name ("articles"?) and status column values in content.db when it gets populated.
   - Recommendation: Code defensively -- check if table exists before querying. Use the 4 status names from CONTEXT.md (researched/written/reviewed/published). If the actual schema differs, a small query adjustment will fix it. Show "No articles yet" empty state.

2. **Cron success rate calculation**
   - What we know: jobs.json has `state.lastStatus` (ok/null) and `state.consecutiveErrors`. 19/20 show "ok".
   - What's unclear: Whether "success rate" should be current snapshot (% with lastStatus ok) or historical (which would require logging cron outcomes over time, not available).
   - Recommendation: Use current snapshot: `(jobs with lastStatus=ok) / (jobs with any lastStatus) * 100`. This is what the data supports. Historical tracking would need a new database table -- out of scope.

3. **Sage and Ezra agent status**
   - What we know: They exist in config but have 0 runs and 0 activities.
   - What's unclear: Whether they'll ever have data or if they're "dormant by design".
   - Recommendation: Show them as "idle" with muted styling, not "down" (red). This avoids false alarms.

## Sources

### Primary (HIGH confidence)
- EC2 direct inspection (2026-02-21) -- all 5 database schemas, row counts, agent registry, cron job structure, file paths
- SWR official docs (https://swr.vercel.app/docs/api) -- refreshInterval, revalidateOnFocus, SWRConfig global configuration
- Phase 29 RESEARCH.md and VERIFICATION.md -- established patterns, verified artifacts, database connection factory

### Secondary (MEDIUM confidence)
- [SWR Automatic Revalidation docs](https://swr.vercel.app/docs/revalidation) -- polling behavior details
- [SWR Global Configuration docs](https://swr.vercel.app/docs/global-configuration) -- SWRConfig provider pattern
- [shadcn/ui Card documentation](https://ui.shadcn.com/docs/components/card) -- Card composition patterns
- [better-sqlite3 API docs](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md) -- prepare/get/all patterns

### Tertiary (LOW confidence)
- None -- all findings verified against code on EC2 or official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified working in Phase 29
- Architecture: HIGH -- API routes + SWR pattern proven in existing `/api/db-status` + `page.tsx`, database schemas confirmed via SSH
- Pitfalls: HIGH -- based on actual data inspection (0-byte content.db, 0-row email, timestamp format differences, sage/ezra with no data)
- Database queries: HIGH -- tested equivalent queries via SSH to verify data shapes and counts

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable infrastructure, database schemas unlikely to change)
