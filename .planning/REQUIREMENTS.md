# Requirements: Pops-Claw v2.5

**Defined:** 2026-02-20
**Core Value:** Mission Control Dashboard as single pane of glass for the entire pops-claw system.

## v2.5 Requirements

### Infrastructure

- [x] **INFRA-01**: All 5 SQLite databases accessible via read-only WAL connections with busy_timeout
- [x] **INFRA-02**: Mission Control accessible directly via Tailscale (http://100.72.143.9:3001, no SSH tunnel)
- [x] **INFRA-03**: Mission Control runs as systemd service that auto-starts on boot with memory limits and OOMScoreAdjust
- [x] **INFRA-04**: Convex dependency fully removed and replaced with SQLite data layer
- [x] **INFRA-05**: shadcn/ui component library initialized with dashboard primitives (card, table, badge, chart)
- [x] **INFRA-06**: All timestamps render correctly without hydration mismatches (shared RelativeTime component)

### Dashboard

- [x] **DASH-01**: Dashboard shows status cards for agent health summary, cron success rates, content pipeline counts, and email quota/bounce stats
- [x] **DASH-02**: Dashboard shows chronological activity stream from coordination.db replacing Convex feed
- [x] **DASH-03**: Dashboard auto-refreshes data every 30 seconds via SWR polling with freshness indicator

### Agent Board

- [x] **AGNT-01**: Agent board page displays a card for each of the 7 agents
- [x] **AGNT-02**: Each agent card shows heartbeat status (alive/down, last seen timestamp)
- [x] **AGNT-03**: Each agent card shows token usage and model distribution (Haiku/Sonnet/Opus) from observability.db
- [x] **AGNT-04**: Each agent card shows recent error count

### Pipeline Metrics

- [x] **PIPE-01**: Content pipeline section shows article counts by status (researched, written, reviewed, published)
- [x] **PIPE-02**: Email metrics section shows sent/received counts, bounce rate, and quota usage from email.db

### Memory

- [x] **MEM-01**: Memory screen displays all agent memories from SQLite memory backend, browseable by agent
- [x] **MEM-02**: Global search across all agent memories and conversations

### Office

- [x] **OFFC-01**: Office view shows avatar for each of the 7 agents at virtual workstations
- [x] **OFFC-02**: Agent avatars reflect current status (working when active, idle when inactive)

### Visualization

- [ ] **VIZ-01**: Token usage displayed as area charts per agent via Recharts
- [ ] **VIZ-02**: Content pipeline displayed as bar chart by status
- [ ] **VIZ-03**: Email volume displayed as line chart over time
- [ ] **VIZ-04**: Cron success/failure displayed as donut chart

## Future Requirements

### Deferred from v2.4

- **DIST-01**: Resend Audience created with initial seed list of industry contacts
- **DIST-02**: Bob can add and remove contacts from subscriber list via skill command
- **DIST-03**: Weekly cron compiles articles published in the last 7 days from content.db
- **DIST-04**: Digest email includes article titles, summaries, and links to airspaceintegration.com
- **DIST-05**: Digest sent via Resend Broadcasts API to subscriber audience on a consistent weekly schedule

### Potential v2.6+

- **MC-01**: Cron detail page with execution history and log viewer
- **MC-02**: Content pipeline kanban view (drag-and-drop article status changes)
- **MC-03**: Time range selector for all metric views (24h, 7d, 30d)
- **MC-04**: Agent detail drill-down page with full session history
- **MC-05**: Anomaly highlighting (auto-flag unusual patterns in metrics)

## Out of Scope

| Feature | Reason |
|---------|--------|
| WebSocket real-time push | Polling sufficient for single user; avoids infrastructure complexity |
| Interactive agent control | Dashboard is read-only monitoring; control stays in Slack |
| User authentication | Tailscale IS the auth layer; no login page needed |
| Multi-user views | Single user (Andy); no role-based access needed |
| Notification system | Slack already handles all notifications |
| Historical data beyond 90 days | Unnecessary for operational monitoring |
| Dark mode toggle | Ship dark-only; no toggle complexity |
| External monitoring services | Privacy risk, overkill for single-user deployment |
| Drag-and-drop customization | Over-engineering for single-user dashboard |
| AI-powered dashboard insights | Bob already does this in morning briefing |
| OpenClaw gateway WebSocket connection | Dashboard reads SQLite directly; gateway is for agent communication |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 29 | Complete |
| INFRA-02 | Phase 29 | Complete |
| INFRA-03 | Phase 29 | Complete |
| INFRA-04 | Phase 29 | Complete |
| INFRA-05 | Phase 29 | Complete |
| INFRA-06 | Phase 29 | Complete |
| DASH-01 | Phase 30 | Complete |
| DASH-02 | Phase 30 | Complete |
| DASH-03 | Phase 30 | Complete |
| AGNT-01 | Phase 31 | Complete |
| AGNT-02 | Phase 31 | Complete |
| AGNT-03 | Phase 31 | Complete |
| AGNT-04 | Phase 31 | Complete |
| PIPE-01 | Phase 30 | Complete |
| PIPE-02 | Phase 30 | Complete |
| MEM-01 | Phase 32 | Complete |
| MEM-02 | Phase 32 | Complete |
| OFFC-01 | Phase 32 | Complete |
| OFFC-02 | Phase 32 | Complete |
| VIZ-01 | Phase 32 | Pending |
| VIZ-02 | Phase 32 | Pending |
| VIZ-03 | Phase 32 | Pending |
| VIZ-04 | Phase 32 | Pending |

**Coverage:**
- v2.5 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-02-20*
*Last updated: 2026-02-21 -- AGNT-01 through AGNT-04 verified complete (Phase 31)*
