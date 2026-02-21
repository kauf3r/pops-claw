# Stack Research

**Domain:** Mission Control Dashboard — real-time SQLite dashboards, agent monitoring, data visualization + OpenClaw VPS deployment patterns
**Researched:** 2026-02-20
**Confidence:** HIGH (UI/charting stack), HIGH (SQLite data layer), MEDIUM (SSE real-time), MEDIUM (OpenClaw latest deployment patterns)

---

## v2.5 Stack Additions

This document covers NEW stack additions for v2.5 Mission Control Dashboard. The existing stack (Next.js 14.2.15, Tailwind CSS, better-sqlite3, cron-parser v5) remains unchanged. Only deltas are documented below.

---

## 1. Data Layer: SQLite Read Access Pattern

### Singleton Database Manager for Multiple DBs

The dashboard reads from 5 SQLite databases (coordination.db, observability.db, content.db, email.db, health.db) that OpenClaw agents write to. The dashboard is read-only — it never writes to these databases.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `better-sqlite3` | 12.6.2 (already installed) | Synchronous read-only SQLite access | Already proven in the project. Synchronous API is perfect for Next.js server components — no async overhead. v12.6.2 is latest stable |

**Architecture Pattern: WAL Mode + Read-Only Connections**

All 5 databases should be opened in WAL (Write-Ahead Logging) mode with read-only connections. WAL allows concurrent readers without blocking the OpenClaw agents that write to these databases. This is the critical pattern — without WAL mode, the dashboard could lock the databases and block cron jobs.

```javascript
// lib/db.js — singleton pattern for Next.js
import Database from 'better-sqlite3';
import path from 'path';

const DB_DIR = process.env.DB_DIR || '/home/ubuntu/clawd/agents/main';

// Cache database instances to avoid re-opening on every request
const dbCache = globalThis.__dbCache || (globalThis.__dbCache = {});

function getDb(name) {
  if (!dbCache[name]) {
    const dbPath = path.join(DB_DIR, `${name}.db`);
    dbCache[name] = new Database(dbPath, { readonly: true });
    dbCache[name].pragma('journal_mode = WAL');
  }
  return dbCache[name];
}

export const coordination = () => getDb('coordination');
export const observability = () => getDb('observability');
export const content = () => getDb('content');
export const email = () => getDb('email');
export const health = () => getDb('health');
```

**Why `globalThis` singleton:** Next.js hot-reloads modules in development, which would otherwise create new database connections on every reload. The `globalThis` pattern is the canonical Next.js approach for singletons (confirmed from Vercel's own examples and community discussion).

**Confidence:** HIGH — better-sqlite3 WAL mode, readonly connections, and globalThis singleton are all well-documented patterns.

**Sources:**
- [better-sqlite3 npm](https://www.npmjs.com/package/better-sqlite3) — v12.6.2 latest
- [SQLite WAL mode documentation](https://sqlite.org/wal.html) — readers don't block writers
- [Next.js singleton discussion](https://github.com/vercel/next.js/discussions/68572) — globalThis pattern

---

## 2. Real-Time Data: SSE Polling Hybrid

### Why NOT WebSockets, Why NOT Convex

The existing Convex integration is being replaced. Convex requires an external service, adds latency through cloud roundtrips, and is overkill for a single-user Tailscale-private dashboard reading local SQLite files.

WebSockets are also overkill here. The dashboard only needs server-to-client updates (unidirectional). The data source is SQLite files on disk, not a push-capable system.

### Recommended: Server-Sent Events with Interval Polling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js Route Handler SSE | Built-in (Next.js 14) | Stream real-time updates to client | Native to Next.js App Router. No additional dependencies. Uses ReadableStream API. One-way server-to-client — perfect for dashboard feeds |
| `setInterval` polling in SSE handler | Built-in (Node.js) | Poll SQLite for changes every N seconds | SQLite has no native change notifications. Polling at 5-10s intervals is efficient for a single-user dashboard on local disk |

**Implementation Pattern:**

```javascript
// app/api/activity-stream/route.js
import { coordination } from '@/lib/db';

export async function GET(request) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const send = (data) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };

      // Initial data burst
      const db = coordination();
      const recent = db.prepare(
        'SELECT * FROM activity ORDER BY created_at DESC LIMIT 50'
      ).all();
      send({ type: 'initial', items: recent });

      // Poll for new data every 5 seconds
      let lastId = recent[0]?.id || 0;
      const interval = setInterval(() => {
        const newer = db.prepare(
          'SELECT * FROM activity WHERE id > ? ORDER BY id ASC'
        ).all(lastId);
        if (newer.length > 0) {
          lastId = newer[newer.length - 1].id;
          send({ type: 'update', items: newer });
        }
      }, 5000);

      // Cleanup on disconnect
      request.signal.addEventListener('abort', () => {
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
```

**Why NOT `use-next-sse` library:** It exists (alexanderkasten/use-next-sse on GitHub) but adds a dependency for something achievable in ~30 lines of native code. The SSE pattern above is straightforward, and the client-side `EventSource` API is built into all browsers.

**Why 5-second polling is fine:** Single user, local disk reads, SQLite indexed queries return in <1ms. Even 1-second polling would be negligible load on the t3.small instance.

**Confidence:** HIGH on SSE implementation pattern (multiple production guides, Next.js 14/15 support confirmed). The App Router's Route Handlers support ReadableStream natively.

**Sources:**
- [SSE in Next.js Complete Guide](https://medium.com/@ammarbinshakir557/implementing-server-sent-events-sse-in-node-js-with-next-js-a-complete-guide-1adcdcb814fd)
- [SSE vs WebSockets in Next.js 15](https://hackernoon.com/streaming-in-nextjs-15-websockets-vs-server-sent-events)
- [use-next-sse library](https://github.com/alexanderkasten/use-next-sse) — evaluated, not recommended for this use case

---

## 3. UI Component Layer: shadcn/ui

### Why shadcn/ui

The dashboard needs cards, tables, badges, tabs, and other UI primitives. shadcn/ui is the standard choice for Next.js + Tailwind projects because it copies component source code into your project (no npm dependency lock-in), uses Radix UI primitives (accessibility built-in), and integrates with Tailwind's theming.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `shadcn/ui` | Latest (CLI-based, no version lock) | Card, Table, Badge, Tabs, Select, Separator | Copy-paste components you own. Built on Radix UI + Tailwind. Official chart components built on Recharts |
| `class-variance-authority` | ^0.7 | Component variant definitions | Required by shadcn/ui for type-safe variant props |
| `clsx` | ^2.1 | Conditional class merging | Required by shadcn/ui `cn()` utility |
| `tailwind-merge` | ^3.0 | Intelligent Tailwind class dedup | Required by shadcn/ui — prevents `p-4 p-2` conflicts |
| `lucide-react` | ^0.469 | Icon library | Used by shadcn/ui components. Consistent icon set for status indicators, navigation |

**Installation:**

```bash
# Initialize shadcn/ui in existing Next.js project
npx shadcn-ui@latest init

# Add specific components needed for dashboard
npx shadcn-ui@latest add card table badge tabs select separator skeleton
npx shadcn-ui@latest add chart  # Installs Recharts-based chart primitives
```

**Dependencies installed by shadcn init:**
```bash
npm install class-variance-authority clsx tailwind-merge lucide-react tw-animate-css
```

**Confidence:** HIGH — shadcn/ui is the dominant component approach for Next.js + Tailwind in 2025-2026. Official Vercel templates use it. Fully compatible with Next.js 14.

**Sources:**
- [shadcn/ui installation for Next.js](https://ui.shadcn.com/docs/installation/next)
- [shadcn/ui charts documentation](https://ui.shadcn.com/charts/area)
- [Vercel Next.js + shadcn admin template](https://vercel.com/templates/next.js/next-js-and-shadcn-ui-admin-dashboard)

---

## 4. Charting: Recharts (via shadcn/ui)

### Why Recharts

shadcn/ui's official chart components are built on Recharts. Using Recharts directly (via shadcn chart primitives) means zero additional charting dependencies and automatic theming/dark mode support.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `recharts` | ^3.7.0 | Line charts, bar charts, area charts, pie charts | Latest stable. shadcn/ui chart components wrap it. Declarative React API. D3-powered but without D3 complexity |

**Dashboard Chart Use Cases:**

| Chart Type | Data Source | Purpose |
|------------|------------|---------|
| Area chart | observability.db | Token usage over time (by agent, by model) |
| Bar chart | content.db | Articles by pipeline status (researched/written/reviewed/published) |
| Line chart | email.db | Email volume trends (sent/received/bounced per day) |
| Donut/Pie | coordination.db | Cron job success/failure rates |
| Sparkline | health.db | HRV/sleep score mini-trends in health card |

**Why NOT Tremor:** Tremor is built on Recharts (meta-library). Adding it on top of shadcn/ui's Recharts integration would be redundant — two abstraction layers over the same underlying library.

**Why NOT Nivo:** Nivo is more feature-rich (Canvas rendering, advanced animations) but heavier and less popular. For this dashboard's chart needs (time series, bars, pies), Recharts covers everything with less complexity.

**Confidence:** HIGH — Recharts 3.7.0 is latest stable, shadcn/ui's chart primitives are built on it, npm shows 3,500+ downstream projects.

**Sources:**
- [Recharts npm](https://www.npmjs.com/package/recharts) — v3.7.0
- [shadcn/ui charts](https://ui.shadcn.com/docs/components/radix/chart) — built on Recharts
- [React chart library comparison](https://blog.logrocket.com/best-react-chart-libraries-2025/) — Recharts recommended for dashboards

---

## 5. Date/Time Formatting: date-fns

### Why date-fns Over dayjs

The dashboard needs relative time display ("3 hours ago"), date formatting for timestamps, and duration calculations. date-fns is the better choice here because: (1) it uses tree-shakeable ESM exports — import only the functions you need, (2) it works with native Date objects (no wrapper), and (3) shadcn/ui's date-picker components use date-fns.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `date-fns` | ^4.1 | Relative time, date formatting, durations | Tree-shakeable (import only what you use). Works with native Date. shadcn/ui ecosystem standard |

**Key Functions Needed:**

```javascript
import { formatDistanceToNow } from 'date-fns/formatDistanceToNow';
import { format } from 'date-fns/format';
import { differenceInMinutes } from 'date-fns/differenceInMinutes';

// "3 hours ago"
formatDistanceToNow(new Date(row.created_at), { addSuffix: true });

// "Feb 20, 2:15 PM"
format(new Date(row.created_at), 'MMM d, h:mm a');

// Heartbeat staleness check
const minutesSince = differenceInMinutes(new Date(), new Date(row.last_heartbeat));
const isStale = minutesSince > 15;
```

**Why NOT dayjs:** dayjs is smaller total size (2KB vs 6KB gzipped), but date-fns tree-shakes better — you only ship the functions you import. For a server-rendered Next.js dashboard, bundle size matters less anyway (most date logic runs server-side). date-fns aligns with the shadcn/ui ecosystem.

**Hydration Warning:** Date formatting MUST happen client-side or use consistent timezone handling. The EC2 server is UTC, the user is PT. Use `useEffect` for any `new Date()` calls that affect rendering (already learned in v2.5 hydration fix).

**Confidence:** HIGH — date-fns v4 is latest stable, well-documented, standard in React ecosystem.

**Sources:**
- [date-fns vs dayjs comparison](https://www.dhiwise.com/post/date-fns-vs-dayjs-the-battle-of-javascript-date-libraries)
- [shadcn/ui date-picker uses date-fns](https://github.com/shadcn-ui/ui/discussions/4817)

---

## 6. Tailscale-Direct Access: Network Binding

### Bind Next.js to Tailnet IP

Currently, Mission Control runs on `127.0.0.1:3001` and requires an SSH tunnel. For direct Tailscale access, Next.js needs to bind to the tailnet IP or `0.0.0.0`.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js `-H` flag | Built-in | Bind dev server to specific host | `npx next dev -H 0.0.0.0 -p 3001` or `-H 100.72.143.9` |
| `tailscale serve` | Built-in (Tailscale) | Optional: serve Next.js via Tailscale HTTPS | Provides automatic HTTPS cert via Tailscale. Maps tailnet hostname to local port. Alternative to direct IP binding |

**Option A: Direct IP Binding (Recommended)**

```bash
# In systemd service or startup script
npx next dev -H 100.72.143.9 -p 3001
# Or for production:
npx next start -H 100.72.143.9 -p 3001
```

Access at: `http://100.72.143.9:3001` from any device on the tailnet.

**Option B: Tailscale Serve (If HTTPS Needed)**

```bash
# Serve Next.js through Tailscale with auto-HTTPS
tailscale serve --bg 3001
```

Access at: `https://ec2-instance.tail-net-name.ts.net` with valid TLS cert.

**Recommendation:** Start with Option A (direct IP binding). It matches the gateway pattern (gateway binds to 100.72.143.9:18789). Add `tailscale serve` later if HTTPS is needed for any reason.

**Security:** Both options are safe — traffic only reaches the EC2 instance via Tailscale VPN. No public internet exposure.

**Confidence:** HIGH — Next.js `-H` flag and `tailscale serve` are both well-documented. This is the same pattern used for the gateway.

**Sources:**
- [Next.js host binding](https://github.com/vercel/next.js/issues/4025)
- [Tailscale serve docs](https://tailscale.com/kb/1242/tailscale-serve/)

---

## 7. OpenClaw VPS Deployment Patterns (2026)

### Current State: v2026.2.17, Latest Available: v2026.2.19-2

| Aspect | Current (pops-claw) | Latest Available | Notes |
|--------|---------------------|------------------|-------|
| OpenClaw version | v2026.2.17 | v2026.2.19-2 | 2 minor releases behind. Not urgent — no security patches in .18/.19 |
| Install method | Bare metal (`npm install -g`) | Docker recommended by community | Bare metal is fine for this deployment — already working, no migration benefit |
| Node.js | 18.x on EC2 | 20.x+ recommended | Node.js 18 LTS is still supported. Upgrade to 20 is nice-to-have, not blocking |

### v2026.2.19 New Features (Released Feb 19, 2026)

| Feature | Relevance to pops-claw |
|---------|----------------------|
| Apple Watch companion MVP | NOT relevant — no Apple Watch integration planned |
| iOS APNs wake-before-invoke | NOT relevant — no iOS app |
| Runtime path containment security | GOOD — hardens plugin/hook security. Worth updating for |
| Token Usage Dashboard layout fix | RELEVANT — fixes clipped cost figures in built-in dashboard |
| `/check-updates` command | NICE — quick update check without full install |

### v2026.2.18 Features (Inferred from version gap)

Could not directly verify v2026.2.18 changelog. LOW confidence on this version's contents.

### Community Deployment Best Practices (2026)

| Practice | Status in pops-claw | Action Needed |
|----------|-------------------|---------------|
| Docker Compose deployment | Using bare metal npm | None — bare metal works, Docker migration is optional |
| UFW firewall + SG restriction | Done (v2.0) | None |
| Non-root execution | Done (ubuntu user) | None |
| Gateway token auth | Done | None |
| Systemd service with watchdog | Done (v2.0) | None |
| Swap file for OOM prevention | Done (2GB, v2.0) | None |
| Regular version updates | v2026.2.17 (2 behind) | Consider updating to v2026.2.19 for path containment security |
| Observability hooks + SQLite | Done (v2.4, observability.db) | None — dashboard will read from this |
| Plugin security audit | Done (SecureClaw v2.1) | None |

### OpenClaw Studio / Community Dashboards

Several community dashboard projects exist for OpenClaw:

| Project | What It Does | Relevance |
|---------|-------------|-----------|
| **openclaw-studio** (grp06) | Web UI for gateway — agents, chat, approvals, cron config | Different purpose. Studio manages agents; Mission Control monitors metrics. Could complement, not replace |
| **openclaw-dashboard** (tugcantopaloglu) | Auth + TOTP MFA, cost tracking, live feed, memory browser | Overlaps with Mission Control. But it's generic — doesn't know about this deployment's 5 databases, 7 agents, content pipeline |
| **openclaw-mission-control** (manish-raana) | Convex + React task tracking dashboard | Uses Convex (which we're removing). Different architecture |

**Recommendation:** Continue building custom Mission Control. The community dashboards are generic monitoring tools. The pops-claw Mission Control is purpose-built for this specific multi-agent system with 5 databases, content pipeline tracking, email metrics, and health data — none of the community tools provide this.

### Update Recommendation

**Do NOT update OpenClaw as part of v2.5 dashboard work.** The dashboard reads SQLite databases — it has zero dependency on the OpenClaw version. Update OpenClaw separately when the path containment security feature (v2026.2.19) is desired, following the established update procedure in findings.md.

**Confidence:** MEDIUM on v2026.2.19 features (WebSearch summaries, not official changelog directly read). HIGH on deployment best practices (multiple guides agree). HIGH on "don't update as part of dashboard work" recommendation.

**Sources:**
- [OpenClaw npm](https://www.npmjs.com/package/openclaw) — v2026.2.19-2 latest
- [OpenClaw releases](https://github.com/openclaw/openclaw/releases)
- [OpenClaw v2026.2.17 security coverage](https://cybersecuritynews.com/openclaw-ai-framework-v2026-2-17/)
- [OpenClaw v2026.2.19 release](https://github.com/openclaw/openclaw/releases/tag/v2026.2.19)
- [OpenClaw Docker docs](https://docs.openclaw.ai/install/docker)
- [OpenClaw VPS hosting guide](https://docs.openclaw.ai/vps)
- [Self-host OpenClaw guide](https://cognio.so/clawdbot/self-hosting)
- [DigitalOcean OpenClaw tutorial](https://www.digitalocean.com/community/tutorials/how-to-run-openclaw)
- [openclaw-studio](https://github.com/grp06/openclaw-studio)
- [openclaw-dashboard](https://github.com/tugcantopaloglu/openclaw-dashboard)

---

## Full Installation Plan

```bash
# From ~/clawd/mission-control/ on EC2

# 1. Initialize shadcn/ui (interactive setup)
npx shadcn-ui@latest init

# 2. Add dashboard components
npx shadcn-ui@latest add card table badge tabs select separator skeleton
npx shadcn-ui@latest add chart

# 3. Install date-fns
npm install date-fns

# 4. shadcn init will install these automatically, but verify:
# class-variance-authority, clsx, tailwind-merge, lucide-react, tw-animate-css

# 5. Recharts is installed by `shadcn-ui add chart`

# NO new database packages needed — better-sqlite3 already installed
# NO SSE library needed — built-in ReadableStream
# NO Convex — REMOVE @convex/react and convex from package.json
```

**Packages to REMOVE:**

```bash
npm uninstall convex @convex/react
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| shadcn/ui | Tremor | If you want zero-config analytics dashboard components. Tremor is higher-level but less flexible |
| shadcn/ui | Material UI / Chakra UI | If you need an opinionated design system. shadcn/ui is better for custom designs with Tailwind |
| Recharts (via shadcn) | Nivo | If you need Canvas rendering for large datasets (10k+ data points). Nivo is heavier but more powerful |
| Recharts (via shadcn) | Chart.js via react-chartjs-2 | If you're already familiar with Chart.js. Recharts is more React-idiomatic |
| SSE polling | WebSocket (ws) | If you need bidirectional communication. Dashboard is read-only, so SSE is sufficient |
| SSE polling | Convex (current) | Never — removing Convex is a v2.5 goal |
| date-fns | dayjs | If total bundle size is the primary concern and you don't need tree-shaking. dayjs is 2KB total |
| Direct IP binding | tailscale serve | If you need HTTPS or want cleaner URLs via tailnet hostnames |

---

## What NOT to Add in v2.5

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Convex / any external real-time database | Goal is to eliminate external dependencies. SQLite files are already on disk | better-sqlite3 reads + SSE polling |
| WebSocket library (ws, socket.io) | Dashboard is read-only — no client-to-server data flow needed | Server-Sent Events (native) |
| Prisma / Drizzle ORM | Adds abstraction over 5 read-only databases with simple queries. better-sqlite3's prepared statements are cleaner for this use case | Direct better-sqlite3 queries |
| TanStack Query (react-query) | Overkill for SSE streams. The `EventSource` API + `useState` is sufficient for a single-user dashboard | Native EventSource + React state |
| Next.js 15 upgrade | Next.js 14.2.15 is stable and working. Upgrading framework during feature work adds risk | Stay on 14.2.15 for v2.5 |
| Docker for Mission Control | Dashboard is a simple Next.js dev server. Containerizing adds complexity for no benefit on a single-user system | Direct `npx next dev` or `npx next start` |
| Grafana / Prometheus | External monitoring stack is overkill for a personal dashboard reading local SQLite files | Custom Next.js dashboard reading SQLite directly |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `better-sqlite3@12.6.2` | Node.js 18.x, 20.x, 22.x | Already installed. Confirmed compatible with EC2's Node.js 18.x |
| `recharts@3.7.0` | React 18.x (Next.js 14) | Latest stable. React 18 is minimum required |
| `shadcn/ui` (latest) | Next.js 14+, Tailwind CSS 3.x | Works with existing Tailwind setup. Will also work with Tailwind v4 if upgraded later |
| `date-fns@4.1` | ESM/CJS, any React version | Pure JS library, no framework constraints |
| `lucide-react@0.469` | React 18+ | Installed by shadcn init |
| `cron-parser@5.x` | Already installed | No changes needed |

---

## Platform Constraints Reminder (Updated for v2.5)

| Constraint | Impact on Dashboard |
|-----------|-------------------|
| EC2 is t3.small (2GB RAM + 2GB swap) | Next.js dev server uses ~150MB. Production build (`next start`) uses less. 5 SQLite readonly connections are negligible. Comfortable with existing headroom |
| 5 SQLite databases on host filesystem | Dashboard must read from host paths, NOT Docker-internal paths. DB_DIR env var should point to `/home/ubuntu/clawd/agents/main/` (or wherever each DB lives) |
| Gateway binds tailnet (100.72.143.9:18789) | Dashboard should follow same pattern — bind to 100.72.143.9:3001 for Tailscale-direct access |
| Server is UTC, user is PT | All date formatting must use client-side rendering (useEffect) to avoid hydration mismatches. Learned from existing cron page hydration fix |
| Non-interactive SSH for management | Dashboard systemd service (if created) needs same patterns as gateway service |

---

## Sources Summary

| Source | Confidence | What It Informs |
|--------|-----------|-----------------|
| [better-sqlite3 npm](https://www.npmjs.com/package/better-sqlite3) | HIGH | v12.6.2 latest, readonly + WAL pattern |
| [SQLite WAL documentation](https://sqlite.org/wal.html) | HIGH | Concurrent readers don't block writers |
| [Next.js singleton pattern](https://github.com/vercel/next.js/discussions/68572) | HIGH | globalThis for database instances |
| [shadcn/ui Next.js install](https://ui.shadcn.com/docs/installation/next) | HIGH | Component installation procedure |
| [shadcn/ui charts](https://ui.shadcn.com/docs/components/radix/chart) | HIGH | Recharts integration, chart primitives |
| [Recharts npm](https://www.npmjs.com/package/recharts) | HIGH | v3.7.0 latest stable |
| [SSE in Next.js guide](https://medium.com/@ammarbinshakir557/implementing-server-sent-events-sse-in-node-js-with-next-js-a-complete-guide-1adcdcb814fd) | MEDIUM | ReadableStream SSE pattern |
| [SSE vs WebSockets in Next.js](https://hackernoon.com/streaming-in-nextjs-15-websockets-vs-server-sent-events) | MEDIUM | SSE sufficient for unidirectional feeds |
| [date-fns vs dayjs](https://www.dhiwise.com/post/date-fns-vs-dayjs-the-battle-of-javascript-date-libraries) | HIGH | Tree-shaking advantage, ecosystem fit |
| [Next.js host binding](https://github.com/vercel/next.js/issues/4025) | HIGH | -H flag for non-localhost binding |
| [Tailscale serve docs](https://tailscale.com/kb/1242/tailscale-serve/) | HIGH | Alternative HTTPS access pattern |
| [OpenClaw npm](https://www.npmjs.com/package/openclaw) | HIGH | v2026.2.19-2 latest version info |
| [OpenClaw releases](https://github.com/openclaw/openclaw/releases) | MEDIUM | v2026.2.19 feature summary |
| [OpenClaw VPS docs](https://docs.openclaw.ai/vps) | HIGH | Deployment best practices |
| [openclaw-studio](https://github.com/grp06/openclaw-studio) | MEDIUM | Community dashboard comparison |
| [React chart library comparison](https://blog.logrocket.com/best-react-chart-libraries-2025/) | MEDIUM | Recharts vs alternatives |

---

*Stack research for: pops-claw v2.5 Mission Control Dashboard*
*Researched: 2026-02-20*
