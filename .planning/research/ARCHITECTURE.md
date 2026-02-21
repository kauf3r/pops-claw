# Architecture: Mission Control Dashboard v2.5

**Domain:** Next.js 14 dashboard integrating 5 SQLite databases + OpenClaw gateway for personal AI companion monitoring
**Researched:** 2026-02-20
**Confidence:** HIGH (Next.js patterns, SQLite access), MEDIUM (OpenClaw gateway API, Tailscale binding)

---

## System Context: What Already Exists

```
EC2 (100.72.143.9) -- Tailscale
|
+-- OpenClaw Gateway :18789 (tailnet bind)
|   +-- 7 agents (main, landos, rangeos, ops, quill, sage, ezra)
|   +-- 20 cron jobs
|   +-- 13 skills
|   +-- Session JSONL: ~/.openclaw/agents/<id>/sessions/*.jsonl
|
+-- SQLite Databases (~/clawd/agents/main/)
|   +-- coordination.db -- agent coordination, standup data
|   +-- health.db ------- Oura Ring metrics (sleep, readiness, HRV, HR)
|   +-- content.db ------ content pipeline (topics, articles, reviews)
|   +-- email.db -------- email tracking (sent, received, bounced, quota)
|   +-- observability.db  LLM usage (tokens, models, turns per agent)
|
+-- Mission Control (~/clawd/mission-control/)
|   +-- Next.js 14.2.15 + Tailwind + better-sqlite3
|   +-- Dev server: 127.0.0.1:3001 (SSH tunnel required)
|   +-- Current: Convex activity feed (to be replaced)
|   +-- Current: coordination.db for calendar tasks
|
+-- Docker Sandbox (agent runtime, network=bridge)
    +-- /workspace/ = ~/clawd/agents/main/ (bind-mount)
    +-- DBs accessible inside sandbox AND on host
```

**Key constraint:** Next.js runs on the EC2 host (not in Docker). It has direct filesystem access to all 5 SQLite databases. No network hop needed for DB reads. This is the single biggest architectural advantage -- use it.

---

## Recommended Architecture

### System Overview

```
                    Tailscale Network
                         |
                    100.72.143.9:3001
                         |
+--------------------------------------------------------+
|                   Next.js 14 App Router                |
|                                                        |
|  +------------------+    +------------------------+    |
|  | Server Components|    | API Route Handlers     |    |
|  | (pages, layouts) |    | /api/agents/[id]       |    |
|  |                  |    | /api/activity           |    |
|  | Direct DB reads  |    | /api/crons             |    |
|  | via db modules   |    | /api/email/stats        |    |
|  +--------+---------+    | /api/content/pipeline   |    |
|           |              +----------+--------------+    |
|           |                         |                   |
|  +--------+-------------------------+----------+       |
|  |              Database Layer (lib/db/)        |       |
|  |                                              |       |
|  |  +-------------+  +--------------+           |       |
|  |  | db/index.ts  |  | db/queries/  |          |       |
|  |  | (singletons) |  | (prepared    |          |       |
|  |  |              |  |  statements) |          |       |
|  |  +------+-------+  +------+------+           |       |
|  |         |                 |                   |       |
|  +---------+-----------------+-------------------+       |
|            |                                             |
+------------|---------------------------------------------+
             |
    +--------+-------------------------------------------+
    |              SQLite Files (read-only access)        |
    |                                                    |
    |  coordination.db  health.db  content.db            |
    |  email.db  observability.db                        |
    +----------------------------------------------------+
             |
    +--------+-------------------------------------------+
    |          Client Components ("use client")          |
    |                                                    |
    |  +------------+  +-----------+  +------------+    |
    |  | Dashboard   |  | Agent     |  | Activity   |    |
    |  | Status Cards|  | Board     |  | Feed       |    |
    |  | (SWR poll)  |  | (SWR poll)|  | (SWR poll) |    |
    |  +------------+  +-----------+  +------------+    |
    +----------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|---------------|----------------|
| Database Layer (`lib/db/`) | Singleton better-sqlite3 connections to all 5 DBs; prepared statements for common queries | Module-level singletons, WAL mode, `readonly: true` for all DBs |
| Server Components (pages) | Initial page render with fresh data; no client JS for static content | Direct import of db query functions; no fetch() needed |
| API Route Handlers (`/api/`) | JSON endpoints for client-side polling via SWR | Call same db query functions; return JSON; 5-30s cache headers |
| Client Components | Interactive UI, auto-refreshing status cards, activity feed with polling | SWR with `refreshInterval`, "use client" directive |
| Status Cards | At-a-glance system health: agent heartbeats, cron success, email quota | Server-rendered initial, SWR-polled updates every 30s |
| Activity Feed | Chronological stream of agent actions, cron runs, emails | Replaces Convex; reads coordination.db + observability.db |
| Agent Board | Per-agent detail: heartbeat status, work queue, token usage, last action | Reads coordination.db + observability.db per agent |
| Content Pipeline | Article status counts and flow visualization | Reads content.db `articles` table grouped by status |
| Email Metrics | Sent/received counts, bounce rate, quota usage | Reads email.db aggregate queries |

---

## Database Layer: The Core Pattern

### Singleton Module with Read-Only Connections

**This is the most important architectural decision.** better-sqlite3 is synchronous. Opening multiple connections per request is wasteful and risks file locking issues. Use module-level singletons with WAL mode and read-only access.

```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_BASE = process.env.DB_PATH || '/home/ubuntu/clawd/agents/main';

function openDb(filename: string): Database.Database {
  const db = new Database(path.join(DB_BASE, filename), {
    readonly: true,
    fileMustExist: true,
  });
  db.pragma('journal_mode = WAL');
  db.pragma('busy_timeout = 3000');
  return db;
}

// Module-level singletons -- created once, reused across requests
export const coordinationDb = openDb('coordination.db');
export const healthDb = openDb('health.db');
export const contentDb = openDb('content.db');
export const emailDb = openDb('email.db');
export const observabilityDb = openDb('observability.db');
```

**Why `readonly: true`:** Mission Control is a monitoring dashboard. It NEVER writes to these databases. The agents (running in Docker) and cron hooks are the writers. Opening read-only prevents accidental writes and avoids WAL checkpoint contention with the writer processes.

**Why WAL mode:** SQLite WAL allows concurrent readers without blocking writers. The OpenClaw agents write to these databases while Mission Control reads. WAL mode is essential -- without it, a long-running dashboard query could block an agent's write, or vice versa.

**Why singletons:** better-sqlite3 connections are lightweight but opening them per-request is unnecessary overhead. Module-level singletons survive across requests in the same Node.js process. In development with hot reload, Next.js may re-execute the module -- this is fine; a new read-only connection replaces the old one.

### Prepared Statements for Common Queries

```typescript
// lib/db/queries/agents.ts
import { coordinationDb, observabilityDb } from '../index';

// Prepare once, execute many times -- better-sqlite3 caches compiled SQL
const getAgentStatusStmt = coordinationDb.prepare(`
  SELECT agent_id, last_heartbeat, status, last_action
  FROM agent_status
  ORDER BY last_heartbeat DESC
`);

const getTokenUsageStmt = observabilityDb.prepare(`
  SELECT agent_id,
         SUM(input_tokens) as total_input,
         SUM(output_tokens) as total_output,
         COUNT(*) as turn_count,
         model
  FROM llm_usage
  WHERE timestamp > datetime('now', '-24 hours')
  GROUP BY agent_id, model
`);

export function getAgentStatuses() {
  return getAgentStatusStmt.all();
}

export function getTokenUsage24h() {
  return getTokenUsageStmt.all();
}
```

**Why prepared statements:** better-sqlite3 compiles SQL once and reuses the compiled statement. For a dashboard making the same queries every 30 seconds, this eliminates repeated SQL parsing overhead.

---

## Data Flow Patterns

### Pattern 1: Server Component Initial Render (No Polling)

**What:** Server Components read directly from SQLite during SSR. No API route, no fetch, no network hop. The query runs in the same Node.js process as the page render.

**When to use:** Pages that load with data but don't need auto-refresh (calendar page, settings, historical views).

**Trade-offs:**
- Pro: Zero client JS for data fetching. Fastest possible initial load.
- Pro: No API layer to maintain for read-only views.
- Con: Data is stale after initial render unless client-side polling is added.

```typescript
// app/dashboard/page.tsx (Server Component -- default in App Router)
import { getAgentStatuses } from '@/lib/db/queries/agents';
import { getContentPipelineCounts } from '@/lib/db/queries/content';
import { getEmailStats } from '@/lib/db/queries/email';
import { DashboardClient } from './dashboard-client';

export const dynamic = 'force-dynamic'; // Always fresh data, no caching

export default function DashboardPage() {
  // These run server-side, synchronously, no await needed for better-sqlite3
  const agents = getAgentStatuses();
  const pipeline = getContentPipelineCounts();
  const emailStats = getEmailStats();

  return (
    <DashboardClient
      initialAgents={agents}
      initialPipeline={pipeline}
      initialEmailStats={emailStats}
    />
  );
}
```

### Pattern 2: SWR Polling for Live Updates (Client Components)

**What:** Client components use SWR with `refreshInterval` to poll API routes for updated data. Server-rendered initial data is passed as `fallbackData` to avoid a loading flash.

**When to use:** Dashboard cards, activity feed, agent board -- anything that should update without page reload.

**Trade-offs:**
- Pro: Near-real-time updates without WebSocket complexity.
- Pro: SWR deduplicates requests, handles errors, auto-retries.
- Con: Polling adds server load (mitigated by 30s intervals and lightweight SQLite queries).

```typescript
// app/dashboard/dashboard-client.tsx
'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

export function DashboardClient({ initialAgents, initialPipeline, initialEmailStats }) {
  const { data: agents } = useSWR('/api/agents', fetcher, {
    fallbackData: initialAgents,
    refreshInterval: 30_000,  // 30 seconds
  });

  const { data: pipeline } = useSWR('/api/content/pipeline', fetcher, {
    fallbackData: initialPipeline,
    refreshInterval: 60_000,  // 1 minute -- content changes slowly
  });

  const { data: emailStats } = useSWR('/api/email/stats', fetcher, {
    fallbackData: initialEmailStats,
    refreshInterval: 60_000,
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      <AgentStatusCards agents={agents} />
      <PipelineOverview pipeline={pipeline} />
      <EmailMetrics stats={emailStats} />
    </div>
  );
}
```

### Pattern 3: API Route Handlers (JSON Endpoints)

**What:** Thin Route Handlers that call the same query functions used by Server Components. Return JSON for SWR consumers.

**When to use:** Every data endpoint that client components poll.

```typescript
// app/api/agents/route.ts
import { NextResponse } from 'next/server';
import { getAgentStatuses } from '@/lib/db/queries/agents';
import { getTokenUsage24h } from '@/lib/db/queries/agents';

export const dynamic = 'force-dynamic';

export async function GET() {
  const statuses = getAgentStatuses();
  const usage = getTokenUsage24h();

  // Merge agent status with token usage
  const agents = statuses.map(agent => ({
    ...agent,
    usage: usage.filter(u => u.agent_id === agent.agent_id),
  }));

  return NextResponse.json(agents, {
    headers: { 'Cache-Control': 'no-store' },
  });
}
```

---

## Page Structure and Data Flows

### Dashboard Page (`/`)

**Purpose:** Single-pane-of-glass overview of the entire system.

```
Dashboard Page
|
+-- Status Bar (server-rendered)
|   +-- Gateway status indicator
|   +-- Last briefing time
|   +-- Current time (PT)
|
+-- Status Cards Row (SWR 30s poll)
|   +-- Agent Health: 7/7 heartbeating, last heartbeat times
|   +-- Cron Status: success rate (last 24h), next run times
|   +-- Email Quota: sent today / 100 limit, bounce rate
|   +-- Content Pipeline: articles by status (researched/drafted/reviewed/published)
|   +-- Token Usage: total tokens today, model distribution pie
|
+-- Activity Feed (SWR 15s poll)
|   +-- Chronological stream merging:
|       +-- coordination.db: agent actions, standup entries
|       +-- observability.db: LLM calls with agent/model/tokens
|       +-- email.db: sent/received emails
|       +-- content.db: article status changes
|   +-- Filter by: agent, type, time range
|
+-- Data sources:
    coordination.db -> agent status, standup, actions
    observability.db -> token usage, model distribution
    email.db -> quota usage, bounce rate
    content.db -> pipeline counts
    health.db -> (optional) latest health score in status bar
```

### Agent Board Page (`/agents`)

**Purpose:** Per-agent detail view with drill-down.

```
Agent Board Page
|
+-- Agent Grid (SWR 30s poll)
|   +-- Card per agent (7 total):
|       +-- Agent name + domain label
|       +-- Heartbeat status: "alive" (green) / "stale" (yellow) / "dead" (red)
|       +-- Last action timestamp + description
|       +-- Token usage spark chart (24h)
|       +-- Active session indicator
|
+-- Agent Detail Panel (click to expand)
    +-- Token usage by model (last 7 days)
    +-- Recent LLM calls (last 20 turns from observability.db)
    +-- Cron jobs owned by this agent + last run status
    +-- Work queue items (from coordination.db)
    +-- Skills assigned
|
+-- Data sources:
    coordination.db -> per-agent status, work queue, standup
    observability.db -> per-agent tokens, turns, model split
```

### Calendar Page (`/calendar`) -- EXISTING

Already built with `coordination.db` user_calendar_tasks table + cron-parser v5. Retain as-is; no architecture changes needed.

---

## Recommended Project Structure

```
~/clawd/mission-control/
+-- src/
|   +-- app/
|   |   +-- layout.tsx              # Root layout with nav + SWRConfig
|   |   +-- page.tsx                # Dashboard (server component, initial render)
|   |   +-- dashboard-client.tsx    # Dashboard client component (SWR polling)
|   |   +-- agents/
|   |   |   +-- page.tsx            # Agent board
|   |   |   +-- [id]/
|   |   |       +-- page.tsx        # Agent detail
|   |   +-- calendar/
|   |   |   +-- page.tsx            # Calendar (existing)
|   |   +-- api/
|   |       +-- agents/
|   |       |   +-- route.ts        # GET /api/agents
|   |       |   +-- [id]/
|   |       |       +-- route.ts    # GET /api/agents/:id
|   |       +-- activity/
|   |       |   +-- route.ts        # GET /api/activity
|   |       +-- content/
|   |       |   +-- pipeline/
|   |       |       +-- route.ts    # GET /api/content/pipeline
|   |       +-- email/
|   |       |   +-- stats/
|   |       |       +-- route.ts    # GET /api/email/stats
|   |       +-- crons/
|   |       |   +-- route.ts        # GET /api/crons
|   |       +-- health/
|   |           +-- route.ts        # GET /api/health (Oura data)
|   +-- lib/
|   |   +-- db/
|   |   |   +-- index.ts            # Database singletons (5 connections)
|   |   |   +-- queries/
|   |   |       +-- agents.ts       # Agent status + token queries
|   |   |       +-- activity.ts     # Cross-DB activity feed query
|   |   |       +-- content.ts      # Content pipeline queries
|   |   |       +-- email.ts        # Email stats queries
|   |   |       +-- health.ts       # Oura health queries
|   |   |       +-- crons.ts        # Cron status queries
|   |   +-- types/
|   |   |   +-- agent.ts            # Agent type definitions
|   |   |   +-- activity.ts         # Activity feed types
|   |   |   +-- content.ts          # Content pipeline types
|   |   |   +-- email.ts            # Email stats types
|   |   +-- utils/
|   |       +-- time.ts             # PT timezone helpers
|   |       +-- format.ts           # Number/date formatting
|   +-- components/
|       +-- cards/
|       |   +-- agent-card.tsx      # Agent status card
|       |   +-- stat-card.tsx       # Generic stat card
|       |   +-- pipeline-card.tsx   # Content pipeline card
|       +-- feed/
|       |   +-- activity-feed.tsx   # Activity stream component
|       |   +-- activity-item.tsx   # Single activity row
|       +-- charts/
|       |   +-- token-spark.tsx     # Sparkline for token usage
|       |   +-- pipeline-flow.tsx   # Status flow visualization
|       +-- layout/
|           +-- nav.tsx             # Navigation sidebar
|           +-- header.tsx          # Page header
+-- public/
+-- next.config.js
+-- package.json
+-- tsconfig.json
```

### Structure Rationale

- **`lib/db/`:** Isolates all database access. Every query function lives here. Server Components and API Routes both import from the same place -- single source of truth for data access.
- **`lib/db/queries/`:** One file per domain. Prepared statements are module-level constants. Functions are exported for use in both Server Components and API Routes.
- **`components/`:** Shared UI components grouped by function (cards, feed, charts), not by page. Allows reuse across dashboard and agent board pages.
- **`app/api/`:** Thin handlers that call query functions and return JSON. No business logic in route handlers -- that belongs in `lib/db/queries/`.
- **`lib/types/`:** TypeScript types matching SQLite row shapes. better-sqlite3 returns plain objects, so types are applied at the query function level.

---

## Integration Points

### SQLite Databases (Direct Filesystem)

| Database | Read Pattern | Key Tables/Queries | Notes |
|----------|-------------|-------------------|-------|
| coordination.db | Singleton, read-only, WAL | `agent_status`, `standup_entries`, `work_queue` | Primary source for agent health; agents write heartbeats here |
| observability.db | Singleton, read-only, WAL | `llm_usage` (tokens, model, agent_id, timestamp) | Per-turn LLM telemetry; written by observability hooks |
| content.db | Singleton, read-only, WAL | `articles` (status, published_at, notified_at) | Pipeline status counts; `GROUP BY status` for overview |
| email.db | Singleton, read-only, WAL | `sent_emails`, `received_emails`, `bounces` | Quota math: `COUNT WHERE date = today`; bounce rate |
| health.db | Singleton, read-only, WAL | `daily_metrics` (sleep_score, readiness, HRV) | Optional status bar widget; low-frequency reads |

**Cross-database activity feed query:** The activity feed merges events from 4 databases. Since SQLite doesn't support cross-database joins in better-sqlite3 read-only mode, the merge happens in JavaScript:

```typescript
// lib/db/queries/activity.ts
import { coordinationDb, observabilityDb, emailDb, contentDb } from '../index';

interface ActivityItem {
  timestamp: string;
  type: 'agent_action' | 'llm_call' | 'email' | 'content_update';
  agent?: string;
  description: string;
  metadata?: Record<string, unknown>;
}

const recentActionsStmt = coordinationDb.prepare(`
  SELECT timestamp, agent_id, action, details
  FROM agent_actions
  WHERE timestamp > datetime('now', '-24 hours')
  ORDER BY timestamp DESC LIMIT 50
`);

const recentLlmCallsStmt = observabilityDb.prepare(`
  SELECT timestamp, agent_id, model, input_tokens, output_tokens
  FROM llm_usage
  WHERE timestamp > datetime('now', '-24 hours')
  ORDER BY timestamp DESC LIMIT 50
`);

const recentEmailsStmt = emailDb.prepare(`
  SELECT sent_at as timestamp, 'sent' as direction, subject, recipient
  FROM sent_emails
  WHERE sent_at > datetime('now', '-24 hours')
  UNION ALL
  SELECT received_at as timestamp, 'received' as direction, subject, sender
  FROM received_emails
  WHERE received_at > datetime('now', '-24 hours')
  ORDER BY timestamp DESC LIMIT 20
`);

const recentContentStmt = contentDb.prepare(`
  SELECT updated_at as timestamp, title, status, agent_id
  FROM articles
  WHERE updated_at > datetime('now', '-24 hours')
  ORDER BY updated_at DESC LIMIT 20
`);

export function getActivityFeed(): ActivityItem[] {
  const actions = recentActionsStmt.all().map(r => ({
    timestamp: r.timestamp,
    type: 'agent_action' as const,
    agent: r.agent_id,
    description: r.action,
    metadata: { details: r.details },
  }));

  const llmCalls = recentLlmCallsStmt.all().map(r => ({
    timestamp: r.timestamp,
    type: 'llm_call' as const,
    agent: r.agent_id,
    description: `${r.model}: ${r.input_tokens}+${r.output_tokens} tokens`,
    metadata: { model: r.model, input: r.input_tokens, output: r.output_tokens },
  }));

  const emails = recentEmailsStmt.all().map(r => ({
    timestamp: r.timestamp,
    type: 'email' as const,
    description: `${r.direction}: ${r.subject}`,
    metadata: { direction: r.direction },
  }));

  const content = recentContentStmt.all().map(r => ({
    timestamp: r.timestamp,
    type: 'content_update' as const,
    agent: r.agent_id,
    description: `"${r.title}" -> ${r.status}`,
  }));

  // Merge and sort by timestamp descending
  return [...actions, ...llmCalls, ...emails, ...content]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 100);
}
```

### OpenClaw Gateway (Potential API Integration)

The OpenClaw gateway at `ws://100.72.143.9:18789` is a WebSocket-based service, not a REST API. Direct integration is limited.

**What is available (MEDIUM confidence):**
- `openclaw sessions list` (CLI) returns active session data
- `openclaw cron list` (CLI) returns cron job status including `lastStatus`, `lastRunAtMs`, `nextRunAtMs`
- Session transcripts stored at `~/.openclaw/agents/<agentId>/sessions/*.jsonl`

**What is NOT available:**
- No REST API on the gateway for programmatic queries
- No WebSocket subscription API for real-time events
- No built-in dashboard API endpoints

**Recommendation:** Do NOT integrate directly with the OpenClaw gateway WebSocket. Instead:
1. Read cron status by parsing `openclaw cron list --json` output via a periodic script that writes to a JSON file Mission Control reads
2. Read session data from the JSONL files directly (same filesystem access pattern as the databases)
3. Agent heartbeat status is already in coordination.db -- no need to query the gateway

**Alternative considered:** The community `openclaw-dashboard` projects (tugcantopaloglu/openclaw-dashboard, abhi1693/openclaw-mission-control) connect directly to the gateway. This requires auth token management and WebSocket handling that adds complexity for this single-user deployment. Reading from files and databases is simpler, more reliable, and sufficient.

### Tailscale Direct Access

**Current:** Dev server binds to `127.0.0.1:3001`, accessed via SSH tunnel (`-L 3001:127.0.0.1:3001`).

**Target:** Bind to Tailscale IP `100.72.143.9:3001`, accessible directly from any device on the tailnet.

**Implementation:**

```json
// package.json
{
  "scripts": {
    "dev": "next dev -H 100.72.143.9 -p 3001",
    "start": "next start -H 100.72.143.9 -p 3001"
  }
}
```

Or, bind to `0.0.0.0` and rely on the EC2 security group (which restricts to `100.64.0.0/10` only) for access control:

```json
{
  "scripts": {
    "dev": "next dev -H 0.0.0.0 -p 3001"
  }
}
```

**Recommendation:** Bind to `0.0.0.0:3001` and trust the security group. The Tailscale IP may change if the node re-registers, but `0.0.0.0` with SG restriction is equivalent and more robust. UFW is also active on the EC2 host -- add a UFW rule to allow port 3001 from the Tailscale subnet.

```bash
sudo ufw allow from 100.64.0.0/10 to any port 3001
```

**No authentication layer needed:** The Tailscale network IS the authentication. Only devices on Andy's tailnet can reach this IP. Adding username/password auth would be security theater on top of a zero-trust network.

---

## Convex Removal Strategy

The current Mission Control uses Convex for the activity feed. This must be replaced with direct SQLite reads.

**What Convex currently provides:**
- Real-time activity feed updates (push-based)
- Cloud-hosted data storage for feed items

**What replaces it:**
- SWR polling every 15 seconds against `/api/activity` route handler
- Activity data sourced from coordination.db + observability.db + email.db + content.db
- No cloud dependency -- all data is local SQLite

**Migration steps:**
1. Create `lib/db/queries/activity.ts` with the cross-database activity feed query
2. Create `/api/activity/route.ts` that calls the query function
3. Replace Convex hooks with SWR hooks in the activity feed component
4. Remove Convex SDK dependency from `package.json`
5. Remove Convex configuration files

**Trade-off:** Losing real-time push in favor of 15-second polling. For a single-user personal dashboard, this is acceptable. The polling interval can be reduced to 5 seconds if needed without meaningful server impact (SQLite reads are sub-millisecond).

---

## Architectural Patterns

### Pattern 1: Server-First with Client Hydration

**What:** Every page renders server-side with fresh data. Client components take over for polling. Initial data is passed as `fallbackData` to SWR so there's no loading state on first render.

**When to use:** Every data-displaying page in this dashboard.

**Why:** Eliminates the "loading spinner on page load" anti-pattern. The page is immediately useful, then stays current via polling.

### Pattern 2: One Query File Per Domain

**What:** Each database domain (agents, content, email, health, observability) gets its own query file with prepared statements and exported functions.

**When to use:** Always. Even if a query is only used in one place today, isolating it makes the codebase navigable and prevents query duplication.

**Why:** Prevents the "queries scattered across route handlers" problem. When a table schema changes, you update one file, not 5 route handlers.

### Pattern 3: Thin Route Handlers

**What:** API route handlers contain zero business logic. They call a query function, return the result as JSON. No data transformation, no computation.

**When to use:** All `/api/` routes in this project.

**Why:** Keeps the API layer maintainable. If you need the same data in a server component and an API route, both call the same function from `lib/db/queries/`.

### Pattern 4: Time-Based Aggregation in SQL

**What:** Dashboard aggregations (token usage per day, email counts per hour, pipeline status counts) are computed in SQL with `GROUP BY` and `datetime()` functions, not in JavaScript.

**When to use:** Any summary statistic displayed on the dashboard.

**Why:** SQLite is faster at aggregation than JavaScript array operations. The database has indexes; the JavaScript runtime does not. Also reduces data transfer from the query -- return 7 daily totals, not 10,000 individual rows.

```sql
-- Token usage per agent per day (last 7 days)
SELECT agent_id,
       date(timestamp) as day,
       SUM(input_tokens) as input_total,
       SUM(output_tokens) as output_total,
       COUNT(*) as turns
FROM llm_usage
WHERE timestamp > datetime('now', '-7 days')
GROUP BY agent_id, date(timestamp)
ORDER BY day DESC;
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Using Prisma or Drizzle for Read-Only SQLite

**What people do:** Add an ORM for "type safety" when reading from SQLite.

**Why it's wrong:** ORMs add connection pooling, migration systems, and schema management overhead. This project uses 5 existing SQLite databases that it does not own the schema for -- the agents and hooks create and manage these schemas. An ORM's migration system would conflict. Prisma's SQLite support also has limitations with read-only mode and WAL.

**Do this instead:** Use better-sqlite3 directly with TypeScript interfaces for row types. Prepared statements give you all the performance benefit. Manual type assertions on query results give you type safety without the overhead.

### Anti-Pattern 2: One Database Connection Per Request

**What people do:** Open a new better-sqlite3 connection in each API route handler or server component render.

**Why it's wrong:** Each connection opens a file handle. While better-sqlite3 handles this gracefully, it's wasteful when a singleton works perfectly. More importantly, you lose the benefit of prepared statement caching -- each new connection must recompile all SQL.

**Do this instead:** Module-level singletons as shown in the database layer pattern above. One connection per database, shared across all requests in the Node.js process.

### Anti-Pattern 3: WebSocket to OpenClaw Gateway for Dashboard Data

**What people do:** Connect to the OpenClaw gateway WebSocket to get real-time agent data.

**Why it's wrong:** The gateway WebSocket is designed for agent communication, not monitoring. Connecting a dashboard client adds a persistent connection that could interfere with agent sessions. The gateway also requires auth tokens that rotate. Community dashboard projects that do this require significant auth management code.

**Do this instead:** Read from SQLite databases and session JSONL files directly. The data you need is already persisted on disk by the agents. The 15-30 second polling delay is acceptable for a monitoring dashboard.

### Anti-Pattern 4: Server Actions for Data Reads

**What people do:** Use Next.js Server Actions (`'use server'` functions) for fetching dashboard data.

**Why it's wrong:** Server Actions are designed for mutations (form submissions, data writes). Using them for reads creates unnecessary POST requests and doesn't benefit from caching. The Next.js team recommends API Routes for data fetching and Server Actions for mutations.

**Do this instead:** Use Server Components for initial data loading (no fetch at all) and API Route Handlers for SWR-polled updates.

### Anti-Pattern 5: Building a Cron Status API When the CLI Already Works

**What people do:** Build a custom cron monitoring system that queries OpenClaw internals.

**Why it's wrong:** `openclaw cron list --json` already returns structured cron status data. Building a parallel monitoring system duplicates effort and can diverge from reality.

**Do this instead:** Run `openclaw cron list --json` periodically (via a cron job or startup script) and write the output to a JSON file that Mission Control reads. Simple, reliable, always accurate.

---

## Build Order (Dependency-Aware)

The build order reflects true dependencies, not just feature grouping.

```
Phase A: Database Layer Foundation
  A1. Create lib/db/index.ts with 5 singleton connections
  A2. Create lib/db/queries/ with prepared statements for each domain
  A3. Verify: import queries in a test page, confirm data returns
  DEPENDS ON: Nothing (all DBs exist on disk)
  RISK: Schema discovery -- must inspect actual table names/columns in each DB
  NOTE: Before writing queries, SSH to EC2 and run:
        sqlite3 ~/clawd/agents/main/coordination.db ".tables" ".schema"
        ...for each database to discover actual schema

Phase B: Dashboard Page (Replace Convex)
  B1. Create /api/agents route handler
  B2. Create /api/activity route handler (cross-DB merge)
  B3. Create /api/content/pipeline route handler
  B4. Create /api/email/stats route handler
  B5. Build dashboard page with status cards + activity feed
  B6. Wire SWR polling to API routes
  B7. Remove Convex dependency from package.json
  DEPENDS ON: Phase A (database layer must exist)

Phase C: Agent Board Page
  C1. Create /api/agents/[id] route handler (per-agent detail)
  C2. Build agent grid with heartbeat indicators
  C3. Build agent detail panel with token usage + recent activity
  DEPENDS ON: Phase A (queries), Phase B is independent

Phase D: Tailscale Direct Access
  D1. Update package.json scripts to bind 0.0.0.0:3001
  D2. Add UFW rule for port 3001 from Tailscale subnet
  D3. Verify access from Mac via Tailscale IP
  D4. Remove SSH tunnel from workflow
  DEPENDS ON: Nothing (independent of B and C)
  NOTE: Can be done in parallel with B or C

Phase E: Cron Status Integration
  E1. Create script to run `openclaw cron list --json > /path/to/crons.json`
  E2. Create /api/crons route handler that reads the JSON file
  E3. Add cron status cards to dashboard
  E4. Schedule the script to run every 5 minutes
  DEPENDS ON: Phase B (dashboard page exists to show the data)
```

**Parallelization opportunity:** Phases B and D are independent. Phase C can start after Phase A without waiting for Phase B. A developer could work on B and D simultaneously.

---

## Scaling Considerations

This is a single-user personal dashboard. Scaling is not a concern.

| Concern | Current (1 user) | If exposed to a team (5 users) |
|---------|------------------|--------------------------------|
| SQLite read contention | Zero -- WAL mode handles this | Still fine -- read-only connections don't block |
| SWR polling load | ~10 requests/minute | ~50 requests/minute -- still negligible for SQLite |
| Database file size | 5 DBs, likely <100MB total | Same -- data volume is agent-driven, not dashboard-driven |
| Node.js memory (t3.small) | Next.js dev server: ~150MB | Same -- additional users don't increase server memory |
| Network bandwidth | <1KB per API response | Same -- JSON payloads are tiny |

**First bottleneck (if it ever mattered):** The activity feed cross-database merge in JavaScript. If individual database queries return large result sets, the merge + sort step could be slow. Mitigation: limit each sub-query to 50 rows (already done in the example above).

---

## Open Questions (Must Verify Before Implementation)

1. **Actual database schemas:** The table names and columns used in query examples above are inferred from project context (MEMORY.md, PROJECT.md). Before writing Phase A, SSH to EC2 and run `.tables` and `.schema` on each database to discover the actual schema. Confidence: MEDIUM -- table names may differ from what's documented.

2. **observability.db existence:** MEMORY.md mentions `observability.db` and the v2.4 milestone added it, but it may not have accumulated much data yet. Verify it has data before building the token usage views.

3. **Cron list JSON output:** The `openclaw cron list` command may or may not support `--json` flag. Verify on EC2. If not available, parse the text output or read from the OpenClaw config file directly.

4. **better-sqlite3 compatibility with current Next.js 14.2.15:** better-sqlite3 is a native module. The existing Mission Control already uses it (for calendar tasks), so this is likely fine. Verify it's working in the current `node_modules/`.

5. **Convex removal scope:** Need to read the current Mission Control source code on EC2 to understand exactly what Convex provides and how deeply integrated it is. The removal may be trivial (swap hooks) or complex (data model dependency).

---

## Sources

### HIGH confidence
- [Next.js 14 Data Fetching Documentation](https://nextjs.org/docs/14/app/building-your-application/data-fetching/fetching-caching-and-revalidating) -- Server Components, Route Handlers, caching
- [Next.js unstable_cache API](https://nextjs.org/docs/app/api-reference/functions/unstable_cache) -- cache for non-fetch data sources
- [SWR Documentation](https://swr.vercel.app/docs/with-nextjs) -- useSWR with Next.js, refreshInterval
- [SQLite WAL Mode](https://sqlite.org/wal.html) -- concurrent reader/writer behavior
- [better-sqlite3 GitHub](https://github.com/WiseLibs/better-sqlite3) -- API, `readonly` option, prepared statements
- [Fly.io: How SQLite Scales Read Concurrency](https://fly.io/blog/sqlite-internals-wal/) -- WAL mode deep dive, end-mark isolation
- Project MEMORY.md -- database locations, Tailscale IPs, security group rules, Mission Control current state

### MEDIUM confidence
- [OpenClaw Dashboard (tugcantopaloglu)](https://github.com/tugcantopaloglu/openclaw-dashboard) -- community dashboard patterns, gateway integration approach
- [OpenClaw Mission Control (abhi1693)](https://github.com/abhi1693/openclaw-mission-control) -- agent orchestration dashboard patterns
- [BitDoze: Best OpenClaw Dashboards 2026](https://www.bitdoze.com/best-openclaw-dashboards/) -- ecosystem survey of monitoring tools
- [Next.js GitHub Discussion: Server Actions vs Route Handlers](https://github.com/vercel/next.js/discussions/72919) -- when to use each
- [Next.js GitHub: Binding to Network Interface](https://github.com/vercel/next.js/issues/4025) -- `-H 0.0.0.0` flag

### LOW confidence (needs verification during implementation)
- Database schemas -- inferred from project documentation, not verified against actual files
- `openclaw cron list --json` flag existence -- assumed, not verified
- Convex integration depth in current Mission Control codebase -- not inspected directly

---

*Architecture research for: pops-claw v2.5 Mission Control Dashboard*
*Researched: 2026-02-20*
*Replaces: previous ARCHITECTURE.md covering v2.3/v2.4 security hardening and content distribution*
