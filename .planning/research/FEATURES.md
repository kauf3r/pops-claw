# Feature Landscape: Mission Control Dashboard v2.5

**Domain:** Single-user operational monitoring dashboard for a multi-agent AI system
**Researched:** 2026-02-20
**Confidence:** HIGH (features derived from existing infrastructure, known database schemas, and established dashboard design patterns)

## Context

Mission Control is a Next.js 14 + Tailwind + better-sqlite3 dashboard running on EC2 at `~/clawd/mission-control/`, accessed via SSH tunnel or Tailscale-direct binding. It currently has a Convex-backed activity feed, cron overview, search, and a calendar page. The v2.5 milestone replaces Convex with direct SQLite reads and builds the "single pane of glass" for the entire pops-claw system: 7 agents, 20 crons, 5 databases, 13 skills, and email/content infrastructure.

**Critical constraint:** This is a single-user operational dashboard. Andy is the only consumer. Features that make sense for multi-user SaaS dashboards (role-based views, granular permissions, team notifications, collaborative annotations) are anti-features here. Every feature must pass the test: "Does this help Andy understand what his system is doing right now?"

**Data sources available (all SQLite, all on EC2):**
- `coordination.db` -- agent_tasks, agent_messages, agent_activity
- `observability.db` -- llm_calls (tokens, model, cost per call), agent_runs (duration, success, errors)
- `content.db` -- topics, articles, social_posts, pipeline_activity
- `email.db` -- sent/received emails, bounce tracking, quota usage, conversations
- `health.db` -- Oura sleep/readiness/HRV data
- Cron JSONL logs at `~/.openclaw/cron/runs/*.jsonl`

---

## Table Stakes

Features users expect from any operational monitoring dashboard. Missing any of these makes the dashboard feel incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| System health overview on landing page | First thing an operator needs is "is everything OK?" -- a single glance answer | Low | 4-6 status cards at top of page: agents alive, crons healthy, content pipeline flowing, email quota OK. Green/yellow/red indicators. No clicking required for the answer |
| Agent heartbeat status | 7 agents running -- which ones responded recently? Which are silent? | Low | Query `agent_runs` in observability.db for most recent `created_at` per agent. Green = last heartbeat < 20 min ago, yellow = 20-60 min, red = > 60 min or never. Display as a compact card grid |
| Cron success/failure summary | 20 cron jobs -- are they all running? Any failing? | Med | Parse cron JSONL logs for last N runs per job. Show success rate (last 24h), last run time, next scheduled time. Red badge on any job with recent failures |
| Activity stream (chronological feed) | The existing Convex feed must be replaced -- it is the primary way Andy sees "what happened" | Med | Read from coordination.db (agent_activity), observability.db (agent_runs), content.db (pipeline_activity), email.db (sent/received). Merge into single reverse-chronological feed. This is the Convex replacement |
| Data freshness indicator | Stale data is worse than no data -- must know when data was last fetched | Low | Show "Last updated: X seconds ago" in the header or per-section. If using polling, show the poll interval. If data is > 5 min old, show a warning |
| Auto-refresh / polling | Dashboard data goes stale within minutes as agents run. Manual refresh defeats the purpose | Low | Client-side polling every 30-60 seconds via `setInterval` + fetch to API routes. Next.js Route Handlers return JSON from SQLite queries. No WebSocket needed for single-user low-frequency updates |
| Mobile-responsive layout | Andy may check the dashboard from his phone via Tailscale | Low | Tailwind responsive breakpoints. Cards stack vertically on mobile. Already built into Tailwind's grid system |

### Confidence: HIGH
All of these are standard patterns for operational dashboards. The data sources exist and have known schemas. No new infrastructure required.

---

## Differentiators

Features that make Mission Control genuinely valuable beyond a basic status page. Not expected, but each one turns the dashboard from "nice to glance at" into "I rely on this."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Token usage sparklines per agent | "How much is each agent consuming over the past 7 days?" as a visual trend, not just today's number | Med | Query observability.db `llm_calls` grouped by agent_id and DATE(created_at). Render as tiny sparkline charts in the agent board. Libraries: Recharts (already React-compatible) or CSS-only bar charts. Reveals patterns like "Quill spikes on Wednesdays" |
| Content pipeline kanban view | Articles moving through stages (researched, writing, review, approved, published) as a visual board | Med | Query content.db `articles` grouped by status. Render as columns with article cards. Not drag-and-drop (Bob manages transitions, not Andy via UI). Read-only visualization of pipeline health. Shows bottlenecks at a glance |
| Email health gauges | Bounce rate, quota usage, and delivery rate as visual meters -- not just numbers | Low | Query email.db for daily sent/bounced/received counts. Resend free tier: 100/day, 3000/month. Show as percentage gauges with threshold coloring (green < 80%, yellow 80-95%, red > 95%). Bounce rate gauge with industry threshold lines (< 2% good, 2-5% warning, > 5% critical) |
| Cost attribution breakdown | "How much would this system cost at API pricing?" per agent per day | Med | observability.db already stores `estimated_cost_usd` per LLM call. Aggregate by agent and time period. Show as stacked bar chart or table. Even though Andy is on Claude Pro 200 (flat rate), cost visibility reveals which agents are resource-heavy and informs model routing decisions |
| Anomaly highlighting in activity stream | Flag unusual events in the activity feed (errors, high token usage, unexpected agent activity) | Med | Apply the same anomaly detection logic from the morning briefing (2x/4x rolling average) to visually highlight entries in the feed. Red border or warning icon on anomalous entries. Turns passive scrolling into active anomaly discovery |
| Agent detail drill-down page | Click an agent card to see its full history: recent sessions, token usage over time, error log, cron run history | Med | Dynamic route `/agents/[id]`. Queries observability.db filtered by agent_id. Shows timeline of activity, cumulative token usage, error messages, model distribution pie chart. Single-agent deep dive without cluttering the overview |
| Cron job detail page | Click a cron to see its run history: last 30 runs, success/fail timeline, average duration, last output snippet | Med | Dynamic route `/crons/[id]`. Parse JSONL log files for the specific cron job. Show run history as a timeline with green/red dots. Duration trend line. Useful for spotting degrading performance (runs getting slower) |
| Time range selector | Switch between "last 1h / 6h / 24h / 7d" views for all metrics | Low | Client-side state that modifies API query parameters. All SQL queries already support `WHERE created_at >= datetime('now', '-N hours')`. Consistent across all dashboard sections |

### Confidence: HIGH for data availability, MEDIUM for specific visualization library choices (Recharts is well-established but version compatibility with Next.js 14 should be verified during implementation).

---

## Anti-Features

Features to explicitly NOT build. Each would add complexity without proportional value for a single-user operational dashboard.

| Anti-Feature | Why It Sounds Good | Why Avoid | What to Do Instead |
|--------------|-------------------|-----------|-------------------|
| Real-time WebSocket push | "See updates instantly without polling" | WebSocket server adds infrastructure complexity (separate process, reconnection logic, state management). For a single user checking every few minutes, polling every 30-60 seconds is indistinguishable from real-time | Client-side polling via `setInterval` + fetch. Simpler, stateless, no new server process |
| Interactive cron/agent control | "Pause crons, restart agents from the dashboard" | Write operations from a web UI into OpenClaw's config create a second control plane alongside the CLI. Risk of conflicting state. OpenClaw CLI is the canonical control interface | Dashboard is read-only. Show status and link to SSH commands if action is needed. "View-only mission control" |
| User authentication / login page | "Secure the dashboard" | Already behind Tailscale -- only reachable from Andy's devices. Adding auth adds a login step to every dashboard check, and requires session management, password storage, or OAuth setup | Tailscale IS the auth layer. Bind to tailnet IP only. No login needed |
| Multi-user views / role-based access | "Different views for different people" | Andy is the only user. Building role infrastructure, permission checks, and view customization for a single operator is pure overhead | One view, one user, one dashboard. Optimize for Andy's workflow |
| Notification system (alerts, toasts, sounds) | "Alert me when something goes wrong" | Bob already delivers alerts via Slack and morning briefing. The dashboard duplicating this creates notification fatigue and a second alert channel to manage | Dashboard shows current state. Slack is the notification channel. No duplication |
| Historical data beyond 90 days | "Long-term trend analysis" | observability.db retains 90 days (by design -- disk space on t3.small). Building archive/export infrastructure for a personal dashboard is over-engineering | 90-day rolling window is sufficient. If historical analysis is needed, export to CSV on demand |
| Dark mode toggle | "Personal preference" | Adds CSS complexity and a preference storage mechanism. For a single user, pick one theme and ship it | Choose dark mode (operational dashboards are conventionally dark -- easier on eyes during extended monitoring). Ship it as the only mode |
| External data source integration (Grafana, Datadog) | "Enterprise-grade monitoring" | Adds API key management, network egress, OTEL configuration, and monthly costs. The data already lives in 5 local SQLite files | Read SQLite directly. Zero external dependencies. Full data access without any third-party coupling |
| Drag-and-drop dashboard customization | "Let users arrange widgets" | Layout persistence, widget registry, drag-and-drop library, serialization/deserialization. Months of UI work for a single user who won't reconfigure after initial setup | Fixed layout optimized for Andy's priorities. Status cards at top, activity stream center, details on drill-down pages |
| AI-powered dashboard insights | "Claude analyzes your dashboard data" | LLM calls from the dashboard add latency, token costs, and API dependency to every page load. Bob already does this analysis in the morning briefing | Bob IS the AI insight layer via morning briefing and Slack. The dashboard presents raw data; Bob provides interpretation |

---

## Feature Dependencies

```
Convex removal
    |-- Activity stream must replace it (reads coordination.db, observability.db, content.db, email.db)
    |-- Convex npm dependency can be removed after migration

Status cards (landing page)
    |-- Agent health: requires observability.db reads (agent_runs table)
    |-- Cron health: requires JSONL log parsing OR a new cron_runs SQLite table
    |-- Content pipeline: requires content.db reads (articles by status)
    |-- Email metrics: requires email.db reads (sent/received/bounced counts)

Activity stream
    |-- requires: coordination.db read access (agent_activity)
    |-- requires: observability.db read access (agent_runs)
    |-- requires: content.db read access (pipeline_activity)
    |-- requires: email.db read access (emails sent/received)
    |-- all 4 DBs must be accessible from Next.js server process via better-sqlite3

Agent board
    |-- requires: observability.db (llm_calls for token usage, agent_runs for heartbeat)
    |-- requires: coordination.db (agent_tasks for work queue)
    |-- optional: sparklines require a charting library (Recharts)

Content pipeline view
    |-- requires: content.db (topics and articles tables)
    |-- independent of other dashboard sections

Email metrics
    |-- requires: email.db (sent/received/bounced counts, quota tracking)
    |-- independent of other dashboard sections

Drill-down pages (/agents/[id], /crons/[id])
    |-- requires: Activity stream and status cards built first (provides navigation context)
    |-- /agents/[id]: observability.db filtered queries
    |-- /crons/[id]: JSONL log parsing for specific job

Database access (cross-cutting)
    |-- All databases are on EC2 at known paths
    |-- Next.js server runs on EC2 -- direct filesystem access via better-sqlite3
    |-- Read-only connections sufficient for all dashboard features
    |-- DB files: ~/clawd/agents/main/observability.db, ~/clawd/content.db,
    |   ~/clawd/agents/main/email.db, ~/clawd/coordination.db (verify exact paths)
```

### Dependency Notes

- **Convex removal is the prerequisite for everything.** The current dashboard has a hard dependency on Convex for the activity feed. Replacing it with SQLite reads is the first architectural change that must land before any new features make sense.
- **All databases are already on the same machine.** No network I/O, no connection strings, no credentials. `better-sqlite3` opens files directly. This is the simplest possible data access pattern.
- **Cron JSONL parsing is the one non-SQLite data source.** Consider whether to parse JSONL files in API routes (simple but per-request I/O) or build a cron that periodically imports JSONL data into a SQLite table (cleaner but more infrastructure). Recommendation: parse JSONL directly in API routes for v2.5, migrate to SQLite import if performance becomes an issue.
- **Charting library (Recharts) is optional.** Status cards and tables can ship without it. Add Recharts only for sparklines and trend charts. It adds ~45KB gzipped to the client bundle.

---

## MVP Recommendation

### Must-ship for v2.5 (the dashboard becomes useful)

1. **Convex removal + SQLite data layer** -- Replace Convex with direct better-sqlite3 reads. Open all 4+ databases read-only from Next.js Route Handlers. This is the architectural foundation for everything else.

2. **Status cards on landing page** -- 4-6 cards showing system health at a glance:
   - Agent health (N/7 alive, any warnings)
   - Cron health (N/20 healthy, last failure)
   - Content pipeline (articles by status counts)
   - Email metrics (quota %, bounce rate)
   - Token usage today (total across agents)
   - (Optional) System uptime / last gateway restart

3. **Activity stream** -- Chronological feed replacing Convex. Reads from coordination.db + observability.db + content.db + email.db. Reverse chronological, paginated, filterable by source type (agent activity, cron runs, content pipeline, email).

4. **Agent board** -- Per-agent cards showing:
   - Last heartbeat time (green/yellow/red)
   - 24h token usage
   - Model distribution (Haiku/Sonnet/Opus)
   - Error count
   - Link to detail page

5. **Auto-refresh polling** -- 30-second client-side polling for all dashboard data. "Last updated" indicator.

6. **Tailscale-direct binding** -- Bind Next.js to tailnet IP instead of requiring SSH tunnel. Direct access at `http://100.72.143.9:3001`.

### Defer to v2.6 or later

- **Content pipeline kanban** -- Useful but not critical for initial monitoring. The status card count covers the basic need. Full kanban is a polish feature.
- **Agent/cron detail drill-down pages** -- Valuable but requires additional routes and more complex queries. Overview is sufficient for v2.5.
- **Sparklines and trend charts** -- Requires Recharts, adds bundle size. Tables with numbers are sufficient for v2.5.
- **Time range selector** -- Nice but "last 24h" as a hardcoded default covers the primary use case.
- **Email health gauges** -- Status card with numbers covers the need. Visual gauges are polish.
- **Cost attribution breakdown** -- Interesting but not operationally critical. The morning briefing already surfaces this.

### Why this order

1. **Convex removal first** because it is blocking. The current Convex dependency is a liability (external service, separate account, data not owned locally). Every other feature depends on the SQLite data layer.
2. **Status cards second** because they deliver the "single pane of glass" promise immediately. Andy opens the dashboard and knows system health in 2 seconds.
3. **Activity stream third** because it replaces the primary interaction pattern (scrolling through what happened).
4. **Agent board fourth** because it provides the agent monitoring depth that status cards summarize.
5. **Auto-refresh and Tailscale binding** are infrastructure that make the dashboard usable day-to-day instead of a one-time-check tool.

---

## Page Structure Recommendation

```
/ (Dashboard - Landing Page)
    |-- Status cards row (agent health, cron health, content counts, email metrics)
    |-- Activity stream (scrollable, paginated, filterable)
    |-- Agent board (7 agent cards in a grid)

/calendar (existing - keep as-is)
    |-- Week/month cron schedule visualization
    |-- User tasks from coordination.db

/agents/[id] (future - v2.6)
    |-- Agent detail: token timeline, error log, session history

/crons/[id] (future - v2.6)
    |-- Cron detail: run history, duration trends, failure analysis
```

---

## Behavioral Notes

### What "Single Pane of Glass" Means for This System

For enterprise SPOG, the challenge is aggregating data from dozens of disparate systems via APIs and adapters. For pops-claw, the data is already consolidated: 5 SQLite databases on one machine. The challenge is not aggregation but **presentation** -- turning raw SQL rows into an at-a-glance understanding of system health.

The practical implication: no ETL pipeline, no data warehouse, no API gateway. Just `better-sqlite3.open(dbPath, { readonly: true })` five times and query directly. This is architecturally trivial compared to enterprise SPOG, which means the implementation effort can focus entirely on UI quality.

### Polling vs WebSocket vs SSE for Refresh

- **WebSocket:** Requires a persistent connection, reconnection logic, and a server-side event emitter tied to database changes. Over-engineered for one user checking a dashboard.
- **Server-Sent Events (SSE):** Simpler than WebSocket but still requires a persistent connection and server-side event stream. Marginal benefit over polling for 30-second intervals.
- **Polling:** `setInterval(() => fetch('/api/status'), 30000)` in a `useEffect`. Zero infrastructure. Works with Next.js Route Handlers out of the box. If the page is backgrounded, polling pauses naturally (browser tab throttling). This is the correct choice.

### Why Read-Only Dashboard

Every operational dashboard that adds "control" features (restart service, pause cron, modify config) becomes a second control plane. For pops-claw, the canonical control plane is `openclaw` CLI via SSH. Adding write operations from the dashboard means:
- Two ways to change state, which can conflict
- Security surface increases (a dashboard bug could modify production config)
- Testing burden doubles (must verify CLI and dashboard produce identical results)

Read-only eliminates this entire problem class. The dashboard answers "what is happening?" and Slack + CLI answer "what should I do about it?"

### Dark Mode by Default

Operational dashboards are conventionally dark-themed because:
- Monitoring sessions can be extended; dark backgrounds reduce eye strain
- Status indicators (green/yellow/red) pop more on dark backgrounds
- It looks professional and ops-y (social proof: Grafana, Datadog, New Relic all default dark)
- Single user = no accessibility concerns about contrast preferences

Ship dark mode only. No toggle.

---

## Sources

### Dashboard Design Patterns
- [UXPin: Dashboard Design Principles for 2025](https://www.uxpin.com/studio/blog/dashboard-design-principles/) -- MEDIUM confidence (general principles, applied to this context)
- [PatternFly Dashboard Guidelines](https://www.patternfly.org/patterns/dashboard/design-guidelines/) -- HIGH confidence (Red Hat's open source design system, operationally focused)
- [DataCamp: Dashboard Design Best Practices](https://www.datacamp.com/tutorial/dashboard-design-tutorial) -- MEDIUM confidence (general principles)

### AI Agent Monitoring
- [UptimeRobot: AI Agent Monitoring Best Practices](https://uptimerobot.com/knowledge-hub/monitoring/ai-agent-monitoring-best-practices-tools-and-metrics/) -- MEDIUM confidence (general patterns adapted to single-user context)
- [Microsoft Azure: Agent Observability Best Practices](https://azure.microsoft.com/en-us/blog/agent-factory-top-5-agent-observability-best-practices-for-reliable-ai/) -- MEDIUM confidence (enterprise patterns, selectively applied)

### Single Pane of Glass Monitoring
- [Interlink Software: SPOG Monitoring Guide](https://www.interlinksoftware.com/what-is-single-pane-of-glass-monitoring-and-how-can-enterprises-leverage-it-for-enhanced-visibility) -- MEDIUM confidence (enterprise framing, concept applied to personal infra)
- [SigNoz: Single Pane of Glass Monitoring](https://signoz.io/blog/single-pane-of-glass-monitoring/) -- MEDIUM confidence (open source perspective)
- [Cloudi-fi: Complete Guide to Unified Monitoring](https://www.cloudi-fi.com/blog/single-pane-of-glass-complete-guide) -- MEDIUM confidence

### Cron Monitoring
- [Cronitor: Cron Job Monitoring](https://cronitor.io/cron-job-monitoring) -- HIGH confidence (purpose-built tool, feature set is the industry baseline)
- [Healthchecks.io](https://healthchecks.io/) -- HIGH confidence (open source reference for cron monitoring features)
- [Better Stack: Cron Job Monitoring Tools Comparison](https://betterstack.com/community/comparisons/cronjob-monitoring-tools/) -- MEDIUM confidence

### Email Metrics
- [Improvado: Email Dashboard Metrics](https://improvado.io/blog/email-marketing-dashboard) -- MEDIUM confidence (marketing context adapted to operational monitoring)
- [WarmForge: Monitor Email Bounce Rates](https://www.warmforge.ai/blog/monitor-email-bounce-rates-effectively?via=dangai) -- MEDIUM confidence

### Content Pipeline
- [Zapier: Kanban Editorial Calendar](https://zapier.com/blog/kanban-editorial-calendar/) -- MEDIUM confidence (editorial workflow patterns)

### Next.js + SQLite
- [Next.js Learn: Fetching Data](https://nextjs.org/learn/dashboard-app/fetching-data) -- HIGH confidence (official Next.js tutorial)
- [Next.js SSR with SQLite](https://nextjs-devanshblog.vercel.app/posts/nextjs-ssr) -- MEDIUM confidence (community example)

### Internal Sources (HIGH confidence)
- Phase 26 Research: observability.db schema (llm_calls, agent_runs tables with indexes)
- Phase 12 Summary: content.db schema (topics, articles, social_posts, pipeline_activity tables)
- Phase 21 Research: email.db schema (email_conversations, rate limiting, bounce tracking)
- PROJECT.md: Full system inventory (7 agents, 20 crons, 13 skills, 5 databases)

---

*Feature research for: Mission Control Dashboard v2.5 -- single pane of glass for pops-claw multi-agent system*
*Researched: 2026-02-20*
*Replaces: previous FEATURES.md covering content distribution + security hardening (v2.3/v2.4 milestones, now shipped/in-progress)*
