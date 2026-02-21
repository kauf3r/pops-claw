# Requirements: Pops-Claw v2.5

**Defined:** 2026-02-20
**Core Value:** Mission Control Dashboard as single pane of glass for the entire pops-claw system.

## v2.5 Requirements

### Infrastructure

- [ ] **INFRA-01**: All 5 SQLite databases accessible via read-only WAL connections with busy_timeout
- [ ] **INFRA-02**: Mission Control accessible directly via Tailscale (http://100.72.143.9:3001, no SSH tunnel)
- [ ] **INFRA-03**: Mission Control runs as systemd service that auto-starts on boot with memory limits and OOMScoreAdjust
- [ ] **INFRA-04**: Convex dependency fully removed and replaced with SQLite data layer
- [ ] **INFRA-05**: shadcn/ui component library initialized with dashboard primitives (card, table, badge, chart)
- [ ] **INFRA-06**: All timestamps render correctly without hydration mismatches (shared RelativeTime component)

### Dashboard

- [ ] **DASH-01**: Dashboard shows status cards for agent health summary, cron success rates, content pipeline counts, and email quota/bounce stats
- [ ] **DASH-02**: Dashboard shows chronological activity stream from coordination.db replacing Convex feed
- [ ] **DASH-03**: Dashboard auto-refreshes data every 30 seconds via SWR polling with freshness indicator

### Agent Board

- [ ] **AGNT-01**: Agent board page displays a card for each of the 7 agents
- [ ] **AGNT-02**: Each agent card shows heartbeat status (alive/down, last seen timestamp)
- [ ] **AGNT-03**: Each agent card shows token usage and model distribution (Haiku/Sonnet/Opus) from observability.db
- [ ] **AGNT-04**: Each agent card shows recent error count

### Pipeline Metrics

- [ ] **PIPE-01**: Content pipeline section shows article counts by status (researched, written, reviewed, published)
- [ ] **PIPE-02**: Email metrics section shows sent/received counts, bounce rate, and quota usage from email.db

### Memory

- [ ] **MEM-01**: Memory screen displays all agent memories from SQLite memory backend, browseable by agent
- [ ] **MEM-02**: Global search across all agent memories and conversations

### Office

- [ ] **OFFC-01**: Office view shows avatar for each of the 7 agents at virtual workstations
- [ ] **OFFC-02**: Agent avatars reflect current status (working when active, idle when inactive)

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
| INFRA-01 | TBD | Pending |
| INFRA-02 | TBD | Pending |
| INFRA-03 | TBD | Pending |
| INFRA-04 | TBD | Pending |
| INFRA-05 | TBD | Pending |
| INFRA-06 | TBD | Pending |
| DASH-01 | TBD | Pending |
| DASH-02 | TBD | Pending |
| DASH-03 | TBD | Pending |
| AGNT-01 | TBD | Pending |
| AGNT-02 | TBD | Pending |
| AGNT-03 | TBD | Pending |
| AGNT-04 | TBD | Pending |
| PIPE-01 | TBD | Pending |
| PIPE-02 | TBD | Pending |
| VIZ-01 | TBD | Pending |
| VIZ-02 | TBD | Pending |
| VIZ-03 | TBD | Pending |
| MEM-01 | TBD | Pending |
| MEM-02 | TBD | Pending |
| OFFC-01 | TBD | Pending |
| OFFC-02 | TBD | Pending |
| VIZ-04 | TBD | Pending |

**Coverage:**
- v2.5 requirements: 24 total
- Mapped to phases: 0
- Unmapped: 24

---
*Requirements defined: 2026-02-20*
*Last updated: 2026-02-20 after initial definition*
