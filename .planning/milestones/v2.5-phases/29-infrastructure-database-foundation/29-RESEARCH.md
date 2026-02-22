# Phase 29: Infrastructure & Database Foundation - Research

**Researched:** 2026-02-20
**Domain:** Next.js production deployment, SQLite read-only connections, Convex removal, shadcn/ui component library, systemd service management
**Confidence:** HIGH

## Summary

This phase transforms Mission Control from a Convex-dependent dev prototype into a production-ready SQLite dashboard running as a systemd service on the Tailscale network. The existing codebase already has significant infrastructure in place -- better-sqlite3, shadcn/ui base config (components.json, tailwind CSS variables, card/badge/button components), date-fns, and dark mode CSS. The main work involves: (1) replacing the Convex provider and two Convex-consuming components, (2) building a DB connection layer for 5 SQLite databases with graceful "not initialized" handling, (3) installing missing shadcn components (table, chart), (4) adding SWR for client-side polling, (5) binding Next.js to 0.0.0.0 for Tailscale access, and (6) creating a systemd service with production-mode `next start`.

Critical discovery: 3 of the 5 databases (coordination.db at `~/clawd/agents/main/`, content.db, and email.db conversations table) are either empty or have 0 rows. The useful databases are: `observability.db` (10,590 rows across 2 tables), `health.db` (14 rows across 4 tables), and `~/clawd/coordination.db` (119 rows across 4 tables -- the REAL coordination.db, NOT the empty one in `~/.openclaw/`). The planner must use the correct file paths.

**Primary recommendation:** Build a singleton DB connection factory that maps logical names to filesystem paths, opens read-only with WAL + busy_timeout, and returns a "not initialized" sentinel when the file is 0 bytes or missing. Start with `next build` + `next start -H 0.0.0.0 -p 3001` behind a systemd user service.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Dark mode by default, with system preference override
- shadcn/ui "zinc" neutral palette with blue accents for primary actions
- No custom branding beyond "Mission Control" in the header -- utility-focused aesthetic
- Minimal shell: header with "Mission Control" title, grid of 5 database connection status cards
- Each card shows DB name, connection status (connected/not initialized), row counts if available
- "System Status" section showing service uptime
- This foundation gets replaced by real dashboard content in Phase 30; DB status cards remain useful as health indicators
- Inline, per-card: yellow "Not Initialized" badge when DB file doesn't exist, with muted explanation ("Database file not found at expected path")
- No full-page warnings -- partial availability is expected
- Connected DBs show green badge + last-modified timestamp
- Port 3001, bind to 0.0.0.0 (Tailscale interface)
- `OOMScoreAdjust=500` -- gateway and Tailscale survive, dashboard gets killed first
- `NODE_ENV=production` with `next start` (not dev server) for lower memory footprint
- UFW rule: allow 3001 from 100.64.0.0/10 only (Tailscale CGNAT range)

### Claude's Discretion
- Exact shadcn component versions and configuration
- Database singleton implementation pattern
- RelativeTime component approach (date-fns vs custom)
- systemd service file structure and restart policy details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | All 5 SQLite databases accessible via read-only WAL connections with busy_timeout | DB connection factory pattern with better-sqlite3 `readonly: true`, `fileMustExist: false` (custom check), WAL pragma, `busy_timeout = 5000`. See Architecture Patterns and Code Examples. |
| INFRA-02 | Mission Control accessible directly via Tailscale (http://100.72.143.9:3001, no SSH tunnel) | Change `next start` bind from `127.0.0.1` to `0.0.0.0`, add UFW rule for 3001 from 100.64.0.0/10. See Architecture Patterns "Tailscale Network Binding". |
| INFRA-03 | Mission Control runs as systemd service that auto-starts on boot with memory limits and OOMScoreAdjust | New systemd user service `mission-control.service` with `OOMScoreAdjust=500`, `Restart=on-failure`, `RestartSec=5`. See Code Examples "systemd Service". |
| INFRA-04 | Convex dependency fully removed and replaced with SQLite data layer | Remove `convex` package, delete `convex/` dir, delete `.env.local` Convex vars, replace `providers.tsx` (remove ConvexProvider), gut Convex imports from `activity-feed.tsx` and `global-search.tsx`, remove `@convex/*` tsconfig path. See Architecture Patterns "Convex Removal". |
| INFRA-05 | shadcn/ui component library initialized with dashboard primitives (card, table, badge, chart) | Card and badge already exist. Need to install `table` and `chart` components via `npx shadcn@latest add table chart`. Update `components.json` baseColor from "slate" to "zinc". See Standard Stack. |
| INFRA-06 | All timestamps render correctly without hydration mismatches (shared RelativeTime component) | Client-only `RelativeTime` component using date-fns `formatDistanceToNow` inside a `useEffect`-guarded render. Server returns static fallback, client hydrates with relative time. See Code Examples "RelativeTime Component". |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | ^12.6.2 | SQLite connections (already installed) | Synchronous API, fastest Node.js SQLite driver, native bindings pre-built for Node 22 |
| next | 14.2.15 | Framework (already installed) | Already in use, stable LTS |
| react / react-dom | 18.3.1 | UI (already installed) | Already in use |
| date-fns | ^3.6.0 | Date formatting (already installed) | `formatDistanceToNow` for RelativeTime, already a dependency |
| swr | ^2.3.3 | Client-side data fetching with polling | Standard React data-fetching. `refreshInterval` for 30s polling (Phase 30 DASH-03), stale-while-revalidate caching. Lighter than TanStack Query for this use case. |
| tailwindcss | ^3.4.10 | Styling (already installed) | Already configured with shadcn/ui CSS variables |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui CLI | latest | Component installation | `npx shadcn@latest add table chart` to install missing components |
| lucide-react | ^0.475.0 | Icons (already installed) | Status icons on DB cards (Database, CheckCircle, AlertTriangle) |
| @types/better-sqlite3 | ^7.6.13 | TypeScript types (already installed) | Already a devDependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SWR | TanStack Query | TanStack is more powerful (mutations, infinite queries) but heavier; SWR is sufficient for read-only polling dashboard |
| date-fns | dayjs | dayjs is smaller but date-fns is already installed and working |
| shadcn/ui table | @tanstack/react-table | TanStack Table is for complex interactive tables; shadcn table wraps it optionally, but Phase 29 only needs static display |

**Installation (new packages only):**
```bash
npm install swr
npx shadcn@latest add table chart
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── app/
│   ├── api/
│   │   ├── db-status/route.ts    # API route returning 5 DB connection statuses
│   │   ├── calendar/             # (existing)
│   │   ├── cron/                 # (existing)
│   │   └── search/               # (existing, needs Convex removal)
│   ├── layout.tsx                # Remove Providers wrapper, add ThemeProvider if desired
│   ├── page.tsx                  # Rewrite: DB status cards grid + system status
│   ├── providers.tsx             # Gut Convex, replace with SWRConfig or remove entirely
│   └── globals.css               # Update CSS variables for zinc palette + blue primary
├── components/
│   ├── dashboard/
│   │   ├── db-status-card.tsx    # New: per-database status card
│   │   ├── system-status.tsx     # New: uptime display
│   │   └── relative-time.tsx     # New: hydration-safe timestamp
│   ├── calendar/                 # (existing, untouched)
│   ├── ui/                       # shadcn primitives (existing + table, chart)
│   └── NavBar.tsx                # (existing, untouched)
├── lib/
│   ├── db.ts                     # New: DB connection factory (5 singletons)
│   ├── db-paths.ts               # New: canonical paths for all 5 databases
│   ├── utils.ts                  # (existing)
│   ├── cron-utils.ts             # (existing)
│   └── calendar-queries.ts       # Update: use new db factory instead of hardcoded path
├── types/
│   └── calendar.ts               # (existing)
└── data/
    └── cron-jobs.json            # (existing)
```

### Pattern 1: Database Connection Factory (Singleton)
**What:** A module that lazily opens and caches read-only SQLite connections, one per database. Each connection sets WAL mode and busy_timeout. Missing/empty files return a sentinel instead of throwing.
**When to use:** Every API route that reads from a database.
**Key insight:** The existing `calendar-queries.ts` opens and closes a new connection on every request. The singleton pattern is better for production -- better-sqlite3 connections are lightweight and WAL mode handles concurrent reads. One connection per DB, opened once, reused across requests.

```typescript
// src/lib/db.ts
import Database from "better-sqlite3";
import fs from "fs";
import { DB_PATHS, type DbName } from "./db-paths";

const connections = new Map<DbName, Database.Database>();

export type DbStatus = {
  name: DbName;
  status: "connected" | "not_initialized";
  path: string;
  lastModified?: string;
  rowCounts?: Record<string, number>;
  error?: string;
};

function isUsableDb(filePath: string): boolean {
  try {
    const stat = fs.statSync(filePath);
    return stat.size > 0;
  } catch {
    return false;
  }
}

export function getDb(name: DbName): Database.Database | null {
  if (connections.has(name)) return connections.get(name)!;

  const dbPath = DB_PATHS[name];
  if (!isUsableDb(dbPath)) return null;

  const db = new Database(dbPath, { readonly: true, fileMustExist: true });
  db.pragma("journal_mode = WAL");
  db.pragma("busy_timeout = 5000");

  connections.set(name, db);
  return db;
}

export function getDbStatus(name: DbName): DbStatus {
  const dbPath = DB_PATHS[name];
  const db = getDb(name);

  if (!db) {
    return {
      name,
      status: "not_initialized",
      path: dbPath,
      error: "Database file not found at expected path"
    };
  }

  // Get last-modified from filesystem
  const stat = fs.statSync(dbPath);
  const lastModified = stat.mtime.toISOString();

  // Get row counts per table
  const tables = db.pragma("table_list") as Array<{ name: string; type: string }>;
  const rowCounts: Record<string, number> = {};
  for (const t of tables) {
    if (t.type === "table" && !t.name.startsWith("sqlite_")) {
      const row = db.prepare(`SELECT count(*) as c FROM "${t.name}"`).get() as { c: number };
      rowCounts[t.name] = row.c;
    }
  }

  return { name, status: "connected", path: dbPath, lastModified, rowCounts };
}
```

### Pattern 2: Convex Removal
**What:** Systematic removal of all Convex dependencies.
**Files to modify/delete:**
1. **Delete:** `convex/` directory (schema.ts, activities.ts, _generated/)
2. **Delete:** `convex.json`
3. **Modify:** `package.json` -- remove `"convex": "^1.24.4"`
4. **Modify:** `.env.local` -- remove all `CONVEX_*` and `NEXT_PUBLIC_CONVEX_*` variables
5. **Modify:** `.env.example` -- remove `NEXT_PUBLIC_CONVEX_URL=`
6. **Modify:** `tsconfig.json` -- remove `"@convex/*": ["convex/*"]` path alias
7. **Rewrite:** `src/app/providers.tsx` -- remove ConvexProvider, replace with simple passthrough or SWRConfig
8. **Rewrite:** `src/components/dashboard/activity-feed.tsx` -- remove Convex useQuery, replace with SWR + API route (Phase 30 work, but the Convex import must go now)
9. **Rewrite:** `src/components/dashboard/global-search.tsx` -- remove Convex useQuery, replace with SWR + API route
10. **Run:** `npm uninstall convex` then `rm -rf node_modules/.cache` to clean

### Pattern 3: Tailscale Network Binding
**What:** Bind Next.js to 0.0.0.0 so it's accessible from Tailscale without SSH tunneling.
**Steps:**
1. Update `package.json` scripts: `"start": "next start -H 0.0.0.0 -p 3001"`
2. Add UFW rule: `sudo ufw allow from 100.64.0.0/10 to any port 3001 proto tcp`
3. Access via: `http://100.72.143.9:3001`

### Pattern 4: RelativeTime Component (Hydration-Safe)
**What:** A client component that renders relative timestamps without hydration mismatches.
**Problem:** Server renders "2 minutes ago" at build time, client hydrates "3 minutes ago" -- mismatch.
**Solution:** Server renders a stable fallback (absolute date or empty), client replaces with relative time after mount via useEffect.

### Anti-Patterns to Avoid
- **Opening a new DB connection per request:** The existing `calendar-queries.ts` does this. Singleton connections are faster and safer with WAL mode.
- **Using `fileMustExist: true` without a pre-check:** better-sqlite3 throws an error if the file doesn't exist AND fileMustExist is true. Check existence first, return null.
- **Importing better-sqlite3 in client components:** It's a Node.js native module. Only use in API routes or server components. SWR fetches from API routes on the client.
- **Setting `readonly: true` then calling `pragma('journal_mode = WAL')`:** This will fail if the database hasn't been set to WAL mode before. The `-wal` file must already exist, or the DB was previously opened in read-write mode with WAL set. All 5 databases should already be in WAL mode since OpenClaw uses it. If not, open read-write once to set it, then read-only afterward.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative timestamps | Custom date math | date-fns `formatDistanceToNow` | Edge cases (DST, locale, "just now" vs "1 second ago") |
| Data polling | setInterval + fetch | SWR `refreshInterval` | Handles dedup, focus revalidation, error retry, caching |
| Component styling | Custom CSS classes | shadcn/ui primitives (Card, Badge, Table) | Consistent design tokens, accessible, dark-mode-ready |
| Service management | cron @reboot or init.d | systemd user service | Restart on crash, dependency ordering, journal logging |
| Process guarding | Custom watchdog scripts | systemd `Restart=on-failure` + `RestartSec=5` | Battle-tested, integrated with journalctl |

**Key insight:** This phase is infrastructure -- use proven system tools (systemd, UFW) and library primitives (shadcn, SWR, date-fns) to avoid building anything from scratch.

## Common Pitfalls

### Pitfall 1: better-sqlite3 WAL in Read-Only Mode
**What goes wrong:** Opening a database with `readonly: true` and then running `pragma('journal_mode = WAL')` fails if the database hasn't been opened in WAL mode before.
**Why it happens:** WAL mode requires creating a `-wal` file, which needs write access.
**How to avoid:** Check if the DB is already in WAL mode with `pragma('journal_mode', { simple: true })`. If it returns `'wal'`, skip the pragma set. If it returns `'delete'`, the connection layer should log a warning but continue in whatever mode the DB is in.
**Warning signs:** "attempt to write a readonly database" errors in the log.

### Pitfall 2: Next.js Hydration Mismatch with Timestamps
**What goes wrong:** Server renders "5 minutes ago", client hydrates "6 minutes ago" -- React throws hydration warning.
**Why it happens:** Server and client compute `new Date()` at different times. Especially bad when server is UTC and client is America/Los_Angeles.
**How to avoid:** Render a stable value on server (ISO string or empty string), replace with relative time in `useEffect` after mount. The existing codebase already has `suppressHydrationWarning` on the `<html>` tag.
**Warning signs:** Console warnings about text content mismatch.

### Pitfall 3: better-sqlite3 in Next.js Webpack Bundle
**What goes wrong:** `next build` tries to bundle better-sqlite3's native addon and fails.
**Why it happens:** Webpack doesn't know how to handle `.node` native binaries.
**How to avoid:** Next.js 14+ includes better-sqlite3 in its default `serverExternalPackages` list automatically. No config needed unless a custom webpack config interferes. Verify by running `next build` and checking for native module errors.
**Warning signs:** Build errors mentioning `.node` files or `better_sqlite3.node`.

### Pitfall 4: Wrong Database Paths
**What goes wrong:** Dashboard shows "not initialized" for databases that actually have data.
**Why it happens:** Multiple copies of databases exist at different paths. The `~/.openclaw/coordination.db` is 0 bytes, but `~/clawd/coordination.db` has 119 rows. Similarly, `~/clawd/agents/main/coordination.db` is 0 bytes.
**How to avoid:** Use the verified paths from schema discovery (see DB Paths section below).
**Warning signs:** All cards showing "not initialized" when data should exist.

### Pitfall 5: Memory Pressure on t3.small
**What goes wrong:** `next build` + `next start` uses too much RAM, OOM kills cascade.
**Why it happens:** t3.small has 2GB RAM. Gateway + Docker + Next.js compete for memory.
**How to avoid:** Use `next start` (production mode, ~80-120MB RSS) not `next dev` (~300-400MB). Set `OOMScoreAdjust=500` so the dashboard is killed before the gateway. The 2GB swap provides buffer.
**Warning signs:** `dmesg | grep -i oom` showing kills, or systemd service in "failed" state.

### Pitfall 6: Stale DB Connections After File Changes
**What goes wrong:** A singleton connection caches a reference to a DB that gets replaced or truncated by an agent.
**Why it happens:** better-sqlite3 caches the file descriptor. If an agent truncates/recreates the DB, the singleton still points to the old file.
**How to avoid:** For Phase 29 this is low risk (read-only dashboard, agents don't recreate DBs often). If it becomes an issue later, add a health-check that verifies the connection is still valid on each API call.

## Code Examples

### Database Path Registry
```typescript
// src/lib/db-paths.ts
// Verified paths from EC2 schema discovery (2026-02-20)

export const DB_NAMES = [
  "coordination",
  "observability",
  "content",
  "email",
  "health",
] as const;

export type DbName = (typeof DB_NAMES)[number];

// IMPORTANT: These are the ACTUAL paths with data.
// ~/.openclaw/*.db files are 0-byte stubs.
// ~/clawd/agents/main/coordination.db is also 0-byte.
// The REAL coordination.db is at ~/clawd/coordination.db.
export const DB_PATHS: Record<DbName, string> = {
  coordination: "/home/ubuntu/clawd/coordination.db",
  observability: "/home/ubuntu/clawd/agents/main/observability.db",
  content: "/home/ubuntu/clawd/agents/main/content.db",
  email: "/home/ubuntu/clawd/agents/main/email.db",
  health: "/home/ubuntu/clawd/agents/main/health.db",
};

// Display labels for the dashboard cards
export const DB_LABELS: Record<DbName, string> = {
  coordination: "Coordination",
  observability: "Observability",
  content: "Content Pipeline",
  email: "Email",
  health: "Health & Environment",
};
```

### RelativeTime Component
```typescript
// src/components/dashboard/relative-time.tsx
"use client";

import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";

interface RelativeTimeProps {
  date: string | Date;
  className?: string;
}

export function RelativeTime({ date, className }: RelativeTimeProps) {
  const [relative, setRelative] = useState<string | null>(null);

  useEffect(() => {
    const d = typeof date === "string" ? new Date(date) : date;
    setRelative(formatDistanceToNow(d, { addSuffix: true }));

    const interval = setInterval(() => {
      setRelative(formatDistanceToNow(d, { addSuffix: true }));
    }, 60_000);

    return () => clearInterval(interval);
  }, [date]);

  if (!relative) {
    // Server-side / pre-hydration fallback
    const d = typeof date === "string" ? new Date(date) : date;
    return <span className={className}>{d.toLocaleDateString()}</span>;
  }

  return <span className={className}>{relative}</span>;
}
```

### DB Status API Route
```typescript
// src/app/api/db-status/route.ts
import { NextResponse } from "next/server";
import { DB_NAMES } from "@/lib/db-paths";
import { getDbStatus } from "@/lib/db";

export const dynamic = "force-dynamic";

export function GET() {
  const statuses = DB_NAMES.map(getDbStatus);
  return NextResponse.json({ databases: statuses });
}
```

### systemd Service
```ini
# ~/.config/systemd/user/mission-control.service
[Unit]
Description=Mission Control Dashboard (Next.js)
After=network-online.target openclaw-gateway.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/clawd/mission-control
ExecStart=/usr/bin/node /home/ubuntu/clawd/mission-control/node_modules/.bin/next start -H 0.0.0.0 -p 3001
Restart=on-failure
RestartSec=5
OOMScoreAdjust=500
Environment=NODE_ENV=production
Environment=HOME=/home/ubuntu
Environment="PATH=/home/ubuntu/.nvm/current/bin:/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=default.target
```

**Enable and start:**
```bash
systemctl --user daemon-reload
systemctl --user enable mission-control.service
systemctl --user start mission-control.service
# Verify:
systemctl --user status mission-control.service
curl -s http://100.72.143.9:3001 | head -5
```

### Updated Providers (Convex Removed)
```typescript
// src/app/providers.tsx
// Convex removed. Simple passthrough for now.
// Can add SWRConfig here later for global SWR options.

export function Providers({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
```

### CSS Variables Update for Zinc + Blue
```css
/* Update to globals.css .dark block for zinc palette + blue primary accents */
.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  --card: 240 10% 3.9%;
  --card-foreground: 0 0% 98%;
  --popover: 240 10% 3.9%;
  --popover-foreground: 0 0% 98%;
  --primary: 217.2 91.2% 59.8%;       /* Blue accent */
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 240 3.7% 15.9%;
  --secondary-foreground: 0 0% 98%;
  --muted: 240 3.7% 15.9%;
  --muted-foreground: 240 5% 64.9%;
  --accent: 240 3.7% 15.9%;
  --accent-foreground: 0 0% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 0 0% 98%;
  --border: 240 3.7% 15.9%;
  --input: 240 3.7% 15.9%;
  --ring: 217.2 91.2% 59.8%;          /* Blue ring */
}
```

## Discovered Facts (from EC2 Inspection)

### Database Schemas and Locations

| Database | Path | Size | Tables | Total Rows | Status |
|----------|------|------|--------|------------|--------|
| coordination | `/home/ubuntu/clawd/coordination.db` | 640 KB | agent_tasks, agent_messages, agent_activity, user_calendar_tasks | 119 | Has data |
| observability | `/home/ubuntu/clawd/agents/main/observability.db` | 1.5 MB | llm_calls, agent_runs | 10,590 | Has data |
| health | `/home/ubuntu/clawd/agents/main/health.db` | 52 KB | health_snapshots, govee_readings, wyze_weight, receipts | 14 | Has data (sparse) |
| email | `/home/ubuntu/clawd/agents/main/email.db` | 32 KB | email_conversations | 0 | Schema exists, no rows |
| content | `/home/ubuntu/clawd/agents/main/content.db` | 0 bytes | (none) | 0 | Empty file, not initialized |

**Critical path notes:**
- `~/.openclaw/coordination.db`, `~/.openclaw/observability.db`, `~/.openclaw/health.db` are all 0-byte stubs -- DO NOT USE
- `~/clawd/agents/main/coordination.db` is also 0-byte -- DO NOT USE
- The REAL coordination.db is at `~/clawd/coordination.db` (640 KB, 4 tables)
- The existing `calendar-queries.ts` already points to `/home/ubuntu/clawd/coordination.db` (correct!)

### Existing Convex Footprint

| Item | Location | Action |
|------|----------|--------|
| `convex/` directory | project root | Delete (schema.ts, activities.ts, _generated/) |
| `convex.json` | project root | Delete |
| `"convex": "^1.24.4"` | package.json | Uninstall |
| `CONVEX_DEPLOYMENT` | .env.local | Remove |
| `NEXT_PUBLIC_CONVEX_URL` | .env.local | Remove |
| `NEXT_PUBLIC_CONVEX_SITE_URL` | .env.local | Remove |
| `NEXT_PUBLIC_CONVEX_URL=` | .env.example | Remove |
| `"@convex/*": ["convex/*"]` | tsconfig.json paths | Remove |
| `ConvexProvider` import | src/app/providers.tsx | Rewrite |
| `useQuery(api.activities.*)` | src/components/dashboard/activity-feed.tsx | Rewrite (stub for now, full impl Phase 30) |
| `useQuery(api.activities.search)` | src/components/dashboard/global-search.tsx | Rewrite (stub for now) |

### Existing shadcn/ui Components

| Component | Status | Notes |
|-----------|--------|-------|
| Card | Installed | Full component (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter) |
| Badge | Installed | Custom variants: default, secondary, outline, success, warning, error |
| Button | Installed | Standard shadcn |
| Input | Installed | Standard shadcn |
| Scroll Area | Installed | Radix-based |
| Separator | Installed | Radix-based |
| Table | **Missing** | Need to install |
| Chart | **Missing** | Need to install (required for Phase 32 VIZ-*) |

### Current Infrastructure State

| Item | Current | Target |
|------|---------|--------|
| Next.js bind | `127.0.0.1` (localhost only) | `0.0.0.0` (Tailscale-accessible) |
| Access method | SSH tunnel `-L 3001:127.0.0.1:3001` | Direct `http://100.72.143.9:3001` |
| Process management | Manual `npx next dev` | systemd `mission-control.service` |
| Build mode | Development (`next dev`) | Production (`next build` + `next start`) |
| UFW port 3001 | Not allowed | Allow from 100.64.0.0/10 |
| Node.js version | v22.22.0 | v22.22.0 (no change) |
| Disk usage | 64% (14GB free) | ~same after build artifacts |
| Memory | 1.9GB total, 760MB available | `next start` ~100MB RSS, leaves room |

### components.json Configuration
Current `baseColor` is `"slate"`. User wants `"zinc"`. This is configured in `components.json` and affects which CSS variables the CLI generates when adding new components. Changing it to `"zinc"` and re-running `npx shadcn@latest init` (or manually updating globals.css) will shift the palette.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Convex cloud DB | SQLite local reads | This phase | Removes external dependency, lower latency, works offline |
| SSH tunnel access | Direct Tailscale binding | This phase | One fewer step, bookmarkable URL |
| `next dev` in terminal | `next start` via systemd | This phase | Auto-start, crash recovery, journal logging |
| Manual component CSS | shadcn/ui CLI components | Already set up | `npx shadcn@latest add` for consistency |

**Deprecated/outdated:**
- `serverComponentsExternalPackages` in next.config.js: Renamed to `serverExternalPackages` in Next.js 14+. But better-sqlite3 is in the default auto-opted-out list, so no config needed.
- Convex: Being fully removed this phase.

## Open Questions

1. **WAL mode on read-only opened databases**
   - What we know: better-sqlite3 with `readonly: true` can read WAL-mode databases that were previously set to WAL by a write-mode connection. Setting WAL pragma in read-only mode may fail.
   - What's unclear: Whether all 5 databases are already in WAL mode from OpenClaw's usage.
   - Recommendation: Check `pragma('journal_mode', { simple: true })` on first connect. If already WAL, skip the set. If not WAL, skip it anyway (don't try to set it read-only). Log the actual journal mode.

2. **content.db schema**
   - What we know: The file at `~/clawd/agents/main/content.db` is 0 bytes. The quill agent's `content.db` has no tables either.
   - What's unclear: Whether a content pipeline exists that will populate this, or if it needs schema creation.
   - Recommendation: Show "Not Initialized" badge. This is expected -- the content pipeline may not be active yet. Phase 30 PIPE-01 will address this.

3. **`next build` on EC2 memory**
   - What we know: `next build` is memory-intensive. t3.small has 2GB RAM + 2GB swap. 760MB available.
   - What's unclear: Whether `next build` will complete without OOM on this instance.
   - Recommendation: Stop the dev server and any non-essential processes before building. If it OOMs, increase swap temporarily with `dd`.

## Sources

### Primary (HIGH confidence)
- Context7: `/wiselibs/better-sqlite3` -- connection options, pragma API, WAL mode, read-only mode
- Context7: `/shadcn-ui/ui` -- CLI installation, dark mode, components.json configuration
- Context7: `/vercel/swr-site` -- refreshInterval, useSWR API, polling behavior
- EC2 direct inspection (2026-02-20) -- all database schemas, file paths, sizes, row counts

### Secondary (MEDIUM confidence)
- [Next.js serverExternalPackages docs](https://nextjs.org/docs/app/api-reference/config/next-config-js/serverExternalPackages) -- better-sqlite3 auto-excluded from webpack bundling

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed or well-documented, verified via Context7
- Architecture: HIGH -- patterns verified against existing codebase, DB schemas inspected on EC2
- Pitfalls: HIGH -- WAL read-only behavior verified in Context7 docs, hydration mismatch is documented Next.js pattern
- Database paths: HIGH -- verified via SSH inspection, row counts confirmed

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable infrastructure, unlikely to change)
