# Roadmap: Proactive Daily Companion

## Milestones

- ✅ **v2.0 Proactive Daily Companion** — Phases 1-11 (shipped 2026-02-09)
- ✅ **v2.1 Content Marketing Pipeline** — Phases 12-18 (shipped 2026-02-09)
- ✅ **v2.2 Resend Email Integration** — Phases 19-23 (shipped 2026-02-17)
- ✅ **v2.3 Security & Platform Hardening** — Merged into v2.4 (0 phases executed)
- ✅ **v2.4 Content Distribution & Platform Hardening** — Phases 24-28 (shipped 2026-02-21, Phase 29 dropped)
- 🚧 **v2.5 Mission Control Dashboard** — Phases 29-32 (in progress)

## Phases

<details>
<summary>✅ v2.0 Proactive Daily Companion (Phases 1-11) — SHIPPED 2026-02-09</summary>

- [x] Phase 1: Update, Memory & Security (2/2 plans) — completed 2026-02-07
- [x] Phase 2: Oura Ring Integration (1/1 plan) — completed 2026-02-08
- [x] Phase 3: Daily Briefing & Rate Limits (3/3 plans) — completed 2026-02-08
- [x] Phase 4: MCP Servers (1/1 plan) — completed 2026-02-08
- [x] Phase 5: Govee & Wyze Integrations (2/2 plans) — completed 2026-02-08
- [x] Phase 6: Multi-Agent Gateway (2/2 plans) — completed 2026-02-08
- [x] Phase 7: Multi-Agent Slack Channels (1/1 plan) — completed 2026-02-09
- [x] Phase 8: Multi-Agent Automation (2/2 plans) — completed 2026-02-09
- [x] Phase 9: Proactive Agent Patterns (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Agentic Coding Workflow (2/2 plans) — completed 2026-02-09
- [x] Phase 11: Document Processing (2/2 plans) — completed 2026-02-09

Full details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)

</details>

<details>
<summary>✅ v2.1 Content Marketing Pipeline (Phases 12-18) — SHIPPED 2026-02-09</summary>

- [x] Phase 12: Content DB + Agent Setup (3/3 plans) — completed 2026-02-09
- [x] Phase 13: Topic Research (2/2 plans) — completed 2026-02-09
- [x] Phase 14: Writing Pipeline (2/2 plans) — completed 2026-02-09
- [x] Phase 15: Review Pipeline (2/2 plans) — completed 2026-02-09
- [x] Phase 16: WordPress Publishing (2/2 plans) — completed 2026-02-09
- [x] Phase 17: Social Promotion (1/1 plan) — completed 2026-02-09
- [x] Phase 18: Pipeline Monitoring (2/2 plans) — completed 2026-02-09

Full details: [milestones/v2.1-ROADMAP.md](milestones/v2.1-ROADMAP.md)

</details>

<details>
<summary>✅ v2.2 Resend Email Integration (Phases 19-23) — SHIPPED 2026-02-17</summary>

- [x] Phase 19: Outbound Email Foundation (2/2 plans) — completed 2026-02-16
- [x] Phase 20: Inbound Email Infrastructure (2/2 plans) — completed 2026-02-17
- [x] Phase 21: Inbound Email Processing (2/2 plans) — completed 2026-02-17
- [x] Phase 22: Domain Warmup & Production Hardening (1/1 plan) — completed 2026-02-17
- [x] Phase 23: Email Integration Gap Closure (1/1 plan) — completed 2026-02-17

Full details: [milestones/v2.2-ROADMAP.md](milestones/v2.2-ROADMAP.md)

</details>

<details>
<summary>✅ v2.4 Content Distribution & Platform Hardening (Phases 24-28) — SHIPPED 2026-02-21</summary>

- [x] Phase 24: Critical Security Update (2/2 plans) — completed 2026-02-18
- [x] Phase 25: Post-Update Audit (2/2 plans) — completed 2026-02-18
- [x] Phase 26: Agent Observability (2/2 plans) — completed 2026-02-19
- [x] Phase 27: Email Domain Hardening (1/1 plan) — completed 2026-02-19
- [x] Phase 28: Platform Cleanup (2/2 plans) — completed 2026-02-21

Full details: [milestones/v2.4-ROADMAP.md](milestones/v2.4-ROADMAP.md)

</details>

### 🚧 v2.5 Mission Control Dashboard (In Progress)

**Milestone Goal:** Build Mission Control into the single pane of glass for the entire pops-claw system -- live data feeds from all 5 SQLite databases, agent health/work/usage oversight, content pipeline and email metrics, memory browsing, office visualization, and charts -- accessible directly via Tailscale.

- [ ] **Phase 29: Infrastructure & Database Foundation** - WAL-mode database layer, Convex removal, shadcn/ui, systemd service, Tailscale binding
- [ ] **Phase 30: Dashboard & Metrics** - Status cards, activity feed, pipeline counts, email stats, auto-refresh polling
- [ ] **Phase 31: Agent Board** - Per-agent cards with heartbeat status, token usage, model distribution, errors
- [ ] **Phase 32: Memory, Office & Visualization** - Memory browser, office view, Recharts area/bar/line/donut charts

## Phase Details

### Phase 29: Infrastructure & Database Foundation
**Goal**: Mission Control has a solid foundation -- all 5 databases accessible read-only, Convex removed, UI components ready, service running on Tailscale, timestamps hydrate correctly
**Depends on**: Nothing (first phase of v2.5)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):
  1. Opening http://100.72.143.9:3001 from any Tailscale device loads Mission Control without SSH tunneling
  2. All 5 SQLite databases (coordination.db, observability.db, content.db, email.db, health.db) are connected read-only with WAL mode and busy_timeout, and a missing database shows a "not initialized" state instead of crashing
  3. Convex is fully gone -- no Convex imports, no @convex/ packages in node_modules, no ConvexProvider in the component tree
  4. shadcn/ui components (card, table, badge, chart) are installed and a test card renders on the landing page
  5. Mission Control auto-starts on boot via systemd, restarts on crash, has OOMScoreAdjust=500 so the gateway survives if memory runs low
**Plans**: 2 plans

Plans:
- [ ] 29-01-PLAN.md -- Convex removal, SWR install, shadcn table/chart, zinc+blue CSS palette, RelativeTime component
- [ ] 29-02-PLAN.md -- Database connection layer (5 WAL singletons), landing page with DB status cards, systemd service, Tailscale bind + UFW rule

### Phase 30: Dashboard & Metrics
**Goal**: The landing page answers "is everything OK?" at a glance -- status cards for all major subsystems, a live activity feed replacing Convex, pipeline and email metrics, all auto-refreshing
**Depends on**: Phase 29
**Requirements**: DASH-01, DASH-02, DASH-03, PIPE-01, PIPE-02
**Success Criteria** (what must be TRUE):
  1. Dashboard shows status cards for agent health (N/7 alive), cron success rate, content pipeline counts (by status), and email quota/bounce stats -- all sourced from SQLite
  2. Chronological activity stream displays recent agent actions, cron runs, emails, and content pipeline moves merged from coordination.db, observability.db, content.db, and email.db
  3. All dashboard data auto-refreshes every 30 seconds via SWR polling, with a visible "last updated X seconds ago" indicator
  4. Content pipeline section shows article counts broken down by status (researched, written, reviewed, published)
  5. Email metrics section shows sent/received counts, bounce rate, and quota usage
**Plans**: TBD

Plans:
- [ ] 30-01: API route handlers (agents, activity, content, email, crons) + SWR polling + status cards
- [ ] 30-02: Activity feed (cross-DB merge, chronological, paginated) + pipeline counts + email metrics

### Phase 31: Agent Board
**Goal**: A dedicated agent board page shows the health, workload, and resource usage of all 7 agents at a glance
**Depends on**: Phase 30
**Requirements**: AGNT-01, AGNT-02, AGNT-03, AGNT-04
**Success Criteria** (what must be TRUE):
  1. /agents page displays a card for each of the 7 agents (Andy, Scout, Vector, Sentinel, Quill, Sage, Ezra)
  2. Each agent card shows heartbeat status with color coding (green = active, yellow = stale, red = down) and last-seen timestamp
  3. Each agent card shows 24-hour token usage and model distribution (Haiku/Sonnet/Opus counts) from observability.db
  4. Each agent card shows recent error count from observability.db, with visual highlighting when errors are non-zero
**Plans**: TBD

Plans:
- [ ] 31-01: Agent board page -- 7-agent card grid, heartbeat status from coordination.db, observability.db connection with caching + higher busy_timeout
- [ ] 31-02: Token usage, model distribution, and error counts per agent from observability.db

### Phase 32: Memory, Office & Visualization
**Goal**: Memory is browseable, agent status is fun to look at, and charts make trends visible across tokens, content, email, and crons
**Depends on**: Phase 31
**Requirements**: MEM-01, MEM-02, OFFC-01, OFFC-02, VIZ-01, VIZ-02, VIZ-03, VIZ-04
**Success Criteria** (what must be TRUE):
  1. /memory page displays agent memories from the SQLite memory backend, filterable by agent, with timestamps and content previewed
  2. Global search on the memory page returns results across all agents' memories and conversations
  3. /office page shows avatars for all 7 agents at virtual workstations, with status reflecting current activity (working vs idle based on recent heartbeat/action data)
  4. Token usage is displayed as area charts per agent, content pipeline as bar chart by status, email volume as line chart over time, and cron success/failure as donut chart -- all powered by Recharts
**Plans**: TBD

Plans:
- [ ] 32-01: Memory browser page (SQLite memory backend queries, agent filter, search)
- [ ] 32-02: Office view (agent avatars, workstation layout, activity-based status)
- [ ] 32-03: Recharts visualization (token area charts, content bar chart, email line chart, cron donut chart)

## Progress

**Execution Order:**
Phases execute in numeric order: 29 -> 30 -> 31 -> 32

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Update, Memory & Security | v2.0 | 2/2 | Complete | 2026-02-07 |
| 2. Oura Ring Integration | v2.0 | 1/1 | Complete | 2026-02-08 |
| 3. Daily Briefing & Rate Limits | v2.0 | 3/3 | Complete | 2026-02-08 |
| 4. MCP Servers | v2.0 | 1/1 | Complete | 2026-02-08 |
| 5. Govee & Wyze Integrations | v2.0 | 2/2 | Complete | 2026-02-08 |
| 6. Multi-Agent Gateway | v2.0 | 2/2 | Complete | 2026-02-08 |
| 7. Multi-Agent Slack Channels | v2.0 | 1/1 | Complete | 2026-02-09 |
| 8. Multi-Agent Automation | v2.0 | 2/2 | Complete | 2026-02-09 |
| 9. Proactive Agent Patterns | v2.0 | 3/3 | Complete | 2026-02-08 |
| 10. Agentic Coding Workflow | v2.0 | 2/2 | Complete | 2026-02-09 |
| 11. Document Processing | v2.0 | 2/2 | Complete | 2026-02-09 |
| 12. Content DB + Agent Setup | v2.1 | 3/3 | Complete | 2026-02-09 |
| 13. Topic Research | v2.1 | 2/2 | Complete | 2026-02-09 |
| 14. Writing Pipeline | v2.1 | 2/2 | Complete | 2026-02-09 |
| 15. Review Pipeline | v2.1 | 2/2 | Complete | 2026-02-09 |
| 16. WordPress Publishing | v2.1 | 2/2 | Complete | 2026-02-09 |
| 17. Social Promotion | v2.1 | 1/1 | Complete | 2026-02-09 |
| 18. Pipeline Monitoring | v2.1 | 2/2 | Complete | 2026-02-09 |
| 19. Outbound Email Foundation | v2.2 | 2/2 | Complete | 2026-02-16 |
| 20. Inbound Email Infrastructure | v2.2 | 2/2 | Complete | 2026-02-17 |
| 21. Inbound Email Processing | v2.2 | 2/2 | Complete | 2026-02-17 |
| 22. Domain Warmup & Hardening | v2.2 | 1/1 | Complete | 2026-02-17 |
| 23. Email Integration Gap Closure | v2.2 | 1/1 | Complete | 2026-02-17 |
| 24. Critical Security Update | v2.4 | 2/2 | Complete | 2026-02-18 |
| 25. Post-Update Audit | v2.4 | 2/2 | Complete | 2026-02-18 |
| 26. Agent Observability | v2.4 | 2/2 | Complete | 2026-02-19 |
| 27. Email Domain Hardening | v2.4 | 1/1 | Complete | 2026-02-19 |
| 28. Platform Cleanup | v2.4 | 2/2 | Complete | 2026-02-21 |
| 29. Infrastructure & Database Foundation | 1/2 | In Progress|  | - |
| 30. Dashboard & Metrics | v2.5 | 0/2 | Not started | - |
| 31. Agent Board | v2.5 | 0/2 | Not started | - |
| 32. Memory, Office & Visualization | v2.5 | 0/3 | Not started | - |

---
*Updated: 2026-02-20 -- v2.5 roadmap created (4 phases, 9 plans, 24 requirements)*
