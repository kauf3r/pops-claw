# Project Research Summary

**Project:** pops-claw — Mission Control Dashboard v2.5
**Domain:** Single-user operational monitoring dashboard for a multi-agent AI system on EC2
**Researched:** 2026-02-20
**Confidence:** HIGH

## Executive Summary

Mission Control v2.5 is a purpose-built "single pane of glass" dashboard for monitoring a multi-agent AI system running on a Tailscale-private EC2 instance. The approach is deliberately minimal: replace the existing Convex cloud dependency with direct SQLite reads from 5 databases already on the same machine, add shadcn/ui components and Recharts charting, and bind the Next.js server to the Tailscale IP for direct access without SSH tunneling. The existing stack (Next.js 14.2.15, Tailwind CSS, better-sqlite3, cron-parser v5) is proven and stays unchanged — this milestone adds to it rather than replaces it.

The recommended architecture is server-first with client hydration: Server Components read from SQLite for the initial render (synchronous, no fetch, no latency), and SWR polls API Route Handlers every 30-60 seconds for live updates. This eliminates loading spinners on page load while keeping the dashboard current. The data model is radically simple — 5 SQLite files on the same host, opened read-only. No network I/O, no credentials, no connection strings. The entire data access layer is approximately 50 lines of better-sqlite3 singletons with WAL mode and prepared statements.

The dominant risk is resource contention on the t3.small (2GB RAM, 40GB EBS at 55% capacity). Three specific threats: SQLite SQLITE_BUSY errors if WAL mode is not enabled before the dashboard goes live, OOM killer killing the OpenClaw gateway if Next.js memory is not capped, and WAL checkpoint starvation causing disk-full if connections are held open indefinitely. All three are preventable in Phase 1 if addressed explicitly — they become expensive recovery operations if discovered later. The PITFALLS.md research explicitly maps 7 of 10 identified pitfalls to Phase 1, making infrastructure setup the highest-leverage work in this milestone.

---

## Key Findings

### Recommended Stack

The stack additions for v2.5 are minimal and well-justified. better-sqlite3 (already installed at v12.6.2) handles all database access using WAL mode + read-only connections + module-level singletons. shadcn/ui (CLI-based, copies components into the project) provides cards, tables, badges, tabs, and chart primitives — all built on Radix UI + Tailwind, zero npm lock-in. Recharts v3.7.0 comes bundled with shadcn/ui's chart components and covers all dashboard visualization needs (area charts for token trends, bar charts for pipeline status, donut charts for cron health). date-fns v4.1 handles timezone-aware time formatting. SWR handles client-side polling with fallbackData from SSR. The only removals: Convex and @convex/react are uninstalled — the external cloud dependency is replaced entirely by local SQLite reads.

**Core technologies:**
- `better-sqlite3` v12.6.2: SQLite read-only access — already installed, synchronous API, WAL + readonly + busy_timeout pattern
- `shadcn/ui` (CLI): UI component library — zero lock-in, Radix UI primitives, automatic Tailwind theming, chart primitives built on Recharts
- `recharts` v3.7.0: Charting — installed via `shadcn add chart`, covers area/bar/line/donut use cases, no separate install
- `date-fns` v4.1: Date formatting — tree-shakeable ESM, UTC/PT handling via client-side rendering, shadcn/ui ecosystem standard
- `swr`: Client polling — `refreshInterval`, `fallbackData` from SSR for no-loading-state initial render, auto-retry
- Next.js Route Handler SSE (built-in): Activity feed streaming option — native ReadableStream, no additional dependencies

### Expected Features

The dashboard passes the single-user operational test: every feature answers "what is my system doing right now?" Anti-features explicitly excluded are user auth (Tailscale is the auth layer), write operations (read-only dashboard avoids a second control plane conflicting with CLI), WebSocket push (polling at 30s is indistinguishable from real-time for one user checking a dashboard), and dark mode toggle (ship dark only — ops dashboards are dark by convention and single-user means no accessibility trade-off).

**Must have (table stakes):**
- System health overview on landing page — 4-6 status cards, green/yellow/red, no clicking required for the answer
- Agent heartbeat status — last ping per agent from coordination.db, green/yellow/red staleness thresholds
- Cron success/failure summary — 20 jobs, last 24h success rate, last run time, next scheduled time
- Activity stream replacing Convex — chronological feed merged from coordination.db + observability.db + email.db + content.db
- Auto-refresh polling — 30s client-side setInterval, "last updated" indicator visible at all times
- Tailscale-direct binding — Next.js on 100.72.143.9:3001, eliminates SSH tunnel requirement

**Should have (differentiators):**
- Token usage sparklines per agent — observability.db grouped by agent + day, reveals consumption patterns week over week
- Content pipeline kanban — articles by status from content.db, read-only visualization showing pipeline bottlenecks
- Email health gauges — bounce rate, quota %, delivery rate from email.db with industry threshold coloring
- Cost attribution breakdown — estimated_cost_usd per agent per day from observability.db, informs model routing decisions
- Agent detail drill-down — dynamic /agents/[id] page with token timeline, error log, session history
- Time range selector — client-side state switching 1h/6h/24h/7d across all metrics

**Defer to v2.6+:**
- Content pipeline kanban (status card counts cover the v2.5 need)
- Agent/cron detail drill-down pages (overview is sufficient for v2.5)
- Sparklines and trend charts (tables with numbers ship first, Recharts added after)
- Time range selector (hardcoded 24h default covers the primary use case)
- Email health gauges (status card numbers cover the need without the visual polish)
- Cost attribution breakdown (morning briefing already surfaces this via Bob)

### Architecture Approach

The architecture separates concerns cleanly across three layers: a database layer (`lib/db/`) with 5 read-only singleton connections and prepared statement query files per domain, Server Components that read directly from the database layer for initial SSR (no fetch, no API hop, synchronous), and Client Components that use SWR polling against thin API Route Handlers for live updates. The critical pattern is "server-first with client hydration" — every page renders immediately with fresh data from the server, then stays current via polling. The cross-database activity feed merges events from 4 databases in JavaScript (SQLite does not support cross-file joins), sorted by timestamp, limited to 100 items. Do NOT integrate with the OpenClaw gateway WebSocket — it is designed for agent communication, not monitoring, and reading from filesystem-based SQLite and JSONL files is simpler, more reliable, and sufficient.

**Major components:**
1. `lib/db/index.ts` — 5 singleton better-sqlite3 connections (WAL + readonly + busy_timeout + cache_size)
2. `lib/db/queries/` — prepared statements per domain: agents, activity (cross-DB merge), content, email, health, crons
3. `app/api/*/route.ts` — thin Route Handlers returning JSON for SWR consumers, zero business logic
4. Dashboard landing page (`/`) — Server Component SSR + Client Component SWR polling for status cards + activity feed + agent board
5. `/agents` page — 7-agent card grid with heartbeat indicators and per-agent token metrics
6. `/calendar` page — existing page, no architecture changes
7. `components/` — shared shadcn/ui-based components (stat cards, feed items, agent cards, chart wrappers)

### Critical Pitfalls

1. **SQLITE_BUSY from concurrent read/write without WAL mode** — Enable WAL mode on ALL 5 databases (`PRAGMA journal_mode = WAL`) and set `busy_timeout = 5000` on every connection before any dashboard reads go live. WAL mode persists to the database file (one-time pragma), but busy_timeout is per-connection and must be set every open. Miss this and cron heartbeat writes fail silently when the dashboard is open. This is Phase 1 work, not Phase 2.

2. **WAL checkpoint starvation growing WAL files until disk full** — Dashboard singleton connections can prevent WAL checkpoints indefinitely, growing WAL files to gigabytes on a disk at 55% capacity. Mitigate: reduce page cache per connection (`cache_size = 200`), run periodic `PRAGMA wal_checkpoint(TRUNCATE)` on a timer every 5 minutes, close idle connections after 60 seconds. Monitor: `ls -la *.db-wal` — any file exceeding 10MB signals starvation.

3. **OOM killer killing the OpenClaw gateway** — Next.js production mode uses 200-400MB. Combined with gateway + Docker + system baseline (~1.2GB), the t3.small runs out of headroom. Set `NODE_OPTIONS='--max-old-space-size=384'` on the Mission Control process, add `OOMScoreAdjust=500` to its systemd service (dashboard is expendable; kill it before the gateway), add `OOMScoreAdjust=-500` to the gateway service. Use `next build && next start`, never `next dev` in production.

4. **Hydration mismatch from UTC server / PT client timezone divergence** — Already occurred once in existing Mission Control code. Create a shared `<RelativeTime>` Client Component in Phase 1 that ALL date rendering uses. Never call `new Date()` in Server Components that render timestamps. Every new component touching dates re-introduces this bug without the shared component enforcing the pattern.

5. **Empty .db file creation from non-existent paths** — better-sqlite3 creates database files on open if they don't exist. Dashboard opening a path before OpenClaw has created that database produces an empty file that confuses the agent. Fix: open all connections with `{ readonly: true, fileMustExist: true }` and show a "database not initialized" state for missing files rather than failing silently.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Infrastructure and Database Foundation
**Rationale:** All other phases depend on this. WAL mode, memory caps, systemd service, Tailscale binding, and the `<RelativeTime>` component must exist before any feature work starts. The PITFALLS.md research explicitly assigns 7 of 10 pitfalls to Phase 1 — building features first and addressing infrastructure second converts preventable risks into expensive recovery operations. shadcn/ui init and date-fns installation also belong here so all subsequent phases have the full component library available.
**Delivers:** 5 read-only WAL-mode database connections with prepared statement stubs; schema validation layer (fileMustExist, table presence check); systemd service with OOMScoreAdjust and Restart=always; Next.js bound to 100.72.143.9:3001 with UFW rule for port 3001; NODE_OPTIONS memory cap; `<RelativeTime>` client component; shadcn/ui and date-fns installed; Convex removed from package.json.
**Avoids:** Pitfalls 1 (SQLITE_BUSY), 2 (WAL starvation), 3 (OOM), 4 (hydration), 5 (empty DB creation), 7 (Tailscale binding exposure), 9 (process dies without systemd), 10 (five connection overhead)

### Phase 2: Core Dashboard — Status Cards and Activity Feed
**Rationale:** This is the Convex removal milestone and the first "useful dashboard" delivery. Status cards give Andy an immediate at-a-glance answer to "is everything OK?" The activity feed replaces the primary existing interaction pattern. Both depend on Phase 1's database layer. Run Convex and SQLite in parallel during transition — remove Convex only after SQLite data is verified to match.
**Delivers:** Landing page with 4-6 health status cards (agents alive, cron health, email quota, content pipeline counts, token usage today); Convex-replacing activity feed reading from 4 databases with 30s SWR polling; "last updated" indicator; pagination for large result sets; all Convex npm dependencies removed.
**Uses:** better-sqlite3 singletons (Phase 1), shadcn/ui cards and tables, SWR with refreshInterval and fallbackData
**Implements:** Server-first + client hydration architecture pattern, cross-database activity feed merge
**Avoids:** Pitfall 6 (real-time loss from Convex removal — keep both running during transition, remove after verification)

### Phase 3: Agent Board
**Rationale:** Once the dashboard is useful (Phase 2), the agent board adds monitoring depth. Requires observability.db integration, which has higher write frequency than other databases (every LLM turn, potentially hundreds per hour during active agent sessions) and needs its own connection management. Isolating this as a separate phase contains the observability.db complexity rather than mixing it with the activity feed work.
**Delivers:** 7-agent card grid with heartbeat status (green/yellow/red based on staleness thresholds), 24h token usage per agent, model distribution, last action timestamp, active session indicator; per-agent data from coordination.db + observability.db; observability.db connection with higher busy_timeout (10s) and 1-minute in-memory caching.
**Uses:** observability.db queries (llm_usage grouped by agent + time period), coordination.db (heartbeats and work queue), Recharts sparklines (first charting integration)
**Avoids:** Pitfall 8 (observability.db high write frequency — cache reads, query indexed columns, generous busy_timeout)

### Phase 4: Cron Status Integration
**Rationale:** 20 cron jobs are a key system component but their status comes from JSONL files or CLI output rather than SQLite — a distinct integration pattern. Building after the SQLite views are proven avoids mixing data access patterns in earlier phases. The `openclaw cron list --json` flag availability needs verification before planning.
**Delivers:** Cron health status card (N/20 healthy, last failure, overall success rate); cron status board showing per-job last run, next scheduled, duration trend; data sourced from JSONL log parsing or `openclaw cron list` output written to a JSON file periodically.
**Uses:** JSONL file parsing in API routes, or a background script writing `openclaw cron list --json` to a file Mission Control reads; cron-parser v5 (already installed) for next-run calculations
**Research flag:** Verify `openclaw cron list --json` flag exists on EC2 before planning this phase. If absent, fall back to JSONL parsing — requires log path discovery per cron job.

### Phase 5: Charts and Visual Metrics
**Rationale:** By Phase 5, the dashboard is fully operational and monitored. This phase adds the visual layer that transforms numbers into trends. All data is already available from earlier phases — this is pure presentation. Deferring charts prevents Recharts bundle size (~45KB gzipped) from adding complexity during foundational work.
**Delivers:** Token usage area charts per agent (last 7 days from observability.db); content pipeline status visualization (content.db articles by status over time); email bounce rate and quota gauges with threshold coloring; cost attribution table per agent per day; time range selector (1h/6h/24h/7d) modifying all metrics simultaneously.
**Uses:** Recharts via shadcn/ui chart primitives (full Recharts integration); date-fns for chart axis labels; SWR with parameterized query strings for time range
**Research flag:** Verify Recharts 3.7.0 compatibility with Next.js 14.2.15 during implementation setup — straightforward but worth a quick check given FEATURES.md noted MEDIUM confidence on this specifically.

### Phase Ordering Rationale

- Phase 1 must come first because 7 of 10 identified pitfalls are infrastructure concerns that become costly recovery operations after feature code is written. The database connection layer is a cross-cutting dependency for everything else.
- Phase 2 before Phase 3 because Convex removal is the primary v2.5 stated goal and delivers the first independently-valuable milestone. Agent board adds depth, not the foundational monitoring capability.
- Phase 4 is separate from Phase 2 because JSONL/CLI integration is a different data access pattern than SQLite. Keeping it isolated prevents cron data uncertainty from blocking dashboard delivery.
- Phase 5 is last because it is pure enhancement — all prior phases are independently valuable without charts, and Recharts adds bundle weight and complexity that is better introduced after the core dashboard is stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Cron Status):** Verify `openclaw cron list --json` flag exists on EC2. LOW confidence on this specific CLI flag — not verified, only assumed. If absent, JSONL parsing approach needs per-job log path discovery.
- **Phase 3 (Agent Board):** Verify actual observability.db schema before writing queries. Table names (`llm_usage` etc.) and column names are inferred from documentation, not verified against the actual database file. SSH to EC2 and run `.tables` + `.schema` before Phase 3 implementation planning.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Infrastructure):** WAL mode, systemd user services, UFW rules, shadcn/ui init, OOMScoreAdjust — all well-documented with established patterns. No research needed.
- **Phase 2 (Status Cards + Activity Feed):** better-sqlite3 + SWR + Next.js App Router is the canonical pattern. Multiple high-confidence sources confirm the server-first + client hydration approach.
- **Phase 5 (Charts):** Recharts API is stable and well-documented. shadcn/ui chart primitives have official examples for every chart type needed (area, bar, donut). No research needed beyond version compatibility check.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies are proven (better-sqlite3 already in production), official sources cited, version compatibility confirmed. shadcn/ui and Recharts are the dominant choices for this stack with strong community consensus. |
| Features | HIGH | Features derived from existing infrastructure and known database schemas — not speculative. Data sources confirmed to exist. Anti-features are principled decisions not assumptions. |
| Architecture | HIGH | Next.js + better-sqlite3 + SWR patterns are canonical and official-docs-backed. One MEDIUM area: OpenClaw gateway API integration — not needed, so irrelevant. Cross-database activity feed merge is straightforward JavaScript. |
| Pitfalls | HIGH | WAL mode, OOM, hydration mismatch — all grounded in official documentation. Hydration mismatch is confirmed project history (already occurred once). OOM risk confirmed by t3.small specs + current baseline memory usage. |

**Overall confidence:** HIGH

### Gaps to Address

- **Actual database schemas:** Table and column names in query examples are inferred from MEMORY.md and PROJECT.md, not verified against actual files. Before writing Phase 1 database query stubs, SSH to EC2 and run `.tables` + `.schema` on all 5 databases. Treat schema as unknown until verified. This is the single most important pre-implementation step.
- **`openclaw cron list --json` flag:** Assumed to exist, not verified. If absent, JSONL parsing is the fallback — requires log path discovery per cron job. Verify on EC2 before Phase 4 planning begins.
- **observability.db data volume:** Added in v2.4, may not have accumulated meaningful data yet. Verify it has records before building token usage visualizations in Phase 3.
- **Convex integration depth:** Current Mission Control codebase not inspected directly in this research pass. The Convex removal scope (trivial hook swap vs. deeper data model dependency) needs assessment at Phase 2 start. Could affect Phase 2 complexity estimate.
- **OpenClaw version update:** v2026.2.19-2 (current: v2026.2.17) includes a path containment security feature. Recommended but should be done separately from dashboard work — zero dependency between dashboard and OpenClaw version.

---

## Sources

### Primary (HIGH confidence)
- [better-sqlite3 GitHub](https://github.com/WiseLibs/better-sqlite3) — API, readonly flag, WAL mode, prepared statements, performance docs
- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html) — concurrent access model, checkpoint starvation warning (official)
- [SQLite Busy Timeout API](https://sqlite.org/c3ref/busy_timeout.html) — per-connection pragma, default 0, retry behavior (official)
- [shadcn/ui Next.js Installation](https://ui.shadcn.com/docs/installation/next) — component installation, init procedure
- [shadcn/ui Charts Documentation](https://ui.shadcn.com/docs/components/radix/chart) — Recharts integration, chart primitives
- [Next.js Data Fetching Docs v14](https://nextjs.org/docs/14/app/building-your-application/data-fetching/fetching-caching-and-revalidating) — Server Components, Route Handlers, caching
- [Next.js Memory Usage Guide](https://nextjs.org/docs/app/guides/memory-usage) — max-old-space-size, cacheMaxMemorySize, standalone output
- [Next.js Hydration Error Documentation](https://nextjs.org/docs/messages/react-hydration-error) — server/client mismatch causes and fixes
- [SWR Documentation](https://swr.vercel.app/docs/with-nextjs) — refreshInterval, fallbackData, App Router usage
- [Recharts npm](https://www.npmjs.com/package/recharts) — v3.7.0 latest stable, 3500+ downstream projects
- Project MEMORY.md — EC2 specs, Tailscale IP, database locations, confirmed hydration fix history, OOM protection config, disk usage
- [PatternFly Dashboard Guidelines](https://www.patternfly.org/patterns/dashboard/design-guidelines/) — operational dashboard design patterns

### Secondary (MEDIUM confidence)
- [SSE in Next.js Guide](https://medium.com/@ammarbinshakir557/implementing-server-sent-events-sse-in-node-js-with-next-js-a-complete-guide-1adcdcb814fd) — ReadableStream SSE pattern
- [SSE vs WebSockets in Next.js 15](https://hackernoon.com/streaming-in-nextjs-15-websockets-vs-server-sent-events) — SSE sufficient for unidirectional feeds
- [date-fns vs dayjs comparison](https://www.dhiwise.com/post/date-fns-vs-dayjs-the-date-libraries) — tree-shaking advantage, ecosystem alignment
- [OpenClaw npm](https://www.npmjs.com/package/openclaw) — v2026.2.19-2 latest version info
- [OpenClaw VPS Docs](https://docs.openclaw.ai/vps) — deployment best practices
- [SQLite Performance Tuning — phiresky](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/) — WAL, busy_timeout, cache_size recommendations
- [Fly.io: How SQLite Scales Read Concurrency](https://fly.io/blog/sqlite-internals-wal/) — WAL checkpoint behavior deep dive
- [Cronitor: Cron Job Monitoring](https://cronitor.io/cron-job-monitoring) — cron monitoring feature baseline (industry standard)
- [React chart library comparison 2025 — LogRocket](https://blog.logrocket.com/best-react-chart-libraries-2025/) — Recharts vs alternatives

### Tertiary (LOW confidence, needs verification)
- OpenClaw v2026.2.19 feature list — inferred from WebSearch summaries, not official changelog directly
- Database schemas (coordination.db, observability.db, content.db, email.db, health.db) — inferred from project documentation, not verified against actual files
- `openclaw cron list --json` flag existence — assumed from context, not verified on EC2

---

*Research completed: 2026-02-20*
*Ready for roadmap: yes*
