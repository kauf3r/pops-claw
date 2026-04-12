# Phase 58: Insights & Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 58-insights-dashboard
**Areas discussed:** Dashboard location, Correlation engine, Journal themes, Visualization design

---

## Dashboard Location

| Option | Description | Selected |
|--------|-------------|----------|
| Mission Control (EC2) | Build /growth on EC2 Mission Control. Reads local SQLite, fetches goals/journal from andyOS API. | |
| andyOS Dashboard | Build /growth on andyOS (Vercel + PostgreSQL). Goals/journal already there. Needs EC2 data sync. | ✓ |
| Hybrid | Growth overview on MC, interactive on andyOS. Two views. | |

**User's choice:** andyOS Dashboard
**Notes:** User wants to unify all tools into the andyOS hub long-term. "I need to start unifying all these tools into that hub."

### Follow-up: Data Bridge

| Option | Description | Selected |
|--------|-------------|----------|
| Sync cron | EC2 cron pushes data to andyOS API hourly. andyOS stores in PostgreSQL. | ✓ |
| Live API proxy | andyOS calls EC2 APIs at render time over Tailscale. | |
| Hybrid: sync + proxy | Sync Oura, proxy habits live. | |

**User's choice:** Sync cron
**Notes:** Hourly frequency selected. All /growth queries hit local PostgreSQL.

### Follow-up: MC Migration Scope

| Option | Description | Selected |
|--------|-------------|----------|
| /growth only + defer MC | Phase 58 builds /growth + sync cron. MC migration deferred. | ✓ |
| /growth + agents page | Add agent board migration alongside /growth. | |
| All four pages | Full migration — /growth + agents + yolo + tools. | |

**User's choice:** /growth only + defer MC
**Notes:** User initially wanted agents + yolo + tools migration too (1, 3, 4) but agreed to defer after scope discussion. Sync pattern established here becomes the blueprint for future migration.

---

## Correlation Engine

| Option | Description | Selected |
|--------|-------------|----------|
| SQL date-matching | Simple SQL joins by date. Avg sleep on habit-complete days vs not. | ✓ |
| LLM-powered analysis | Claude finds patterns from raw data. More nuanced but uses tokens. | |
| Statistical correlation | Pearson/Spearman coefficients. Rigorous but overkill for personal use. | |

**User's choice:** SQL date-matching

### Follow-up: Cadence

| Option | Description | Selected |
|--------|-------------|----------|
| Weekly review only | Bundle into Sunday 8am cron. Natural 7-day cadence. | ✓ |
| Daily in briefing | Morning briefing includes yesterday's correlations. | |
| On-demand + weekly | Weekly cron + Bob DM anytime. | |

**User's choice:** Weekly review only

---

## Journal Themes

| Option | Description | Selected |
|--------|-------------|----------|
| LLM summarization | Send 4 weeks of entries to Claude for theme extraction. | ✓ |
| Keyword frequency | Count recurring words/phrases. Simple but shallow. | |
| Category tracking | Track which categories correlate with mood. Minimal new work. | |

**User's choice:** LLM summarization

### Follow-up: Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Part of weekly review | Themes added to Sunday 8am cron. | ✓ |
| Separate cron | Dedicated Friday cron for themes. | |
| You decide | Claude picks during planning. | |

**User's choice:** Part of weekly review

---

## Visualization Design

| Option | Description | Selected |
|--------|-------------|----------|
| Hub-style cards | Card grid: Habits, Goals, Journal, Oura, Insights. Sparklines, links to detail pages. | ✓ |
| Full dashboard | Full-width charts, data-dense analytics page. | |
| Timeline view | Chronological feed of all growth activity. | |

**User's choice:** Hub-style cards

### Follow-up: Chart Library

| Option | Description | Selected |
|--------|-------------|----------|
| Recharts | Already in andyOS. React-native, good for sparklines. | ✓ |
| Tremor | Tailwind-native. New dependency. | |
| You decide | Claude picks during planning. | |

**User's choice:** Recharts

### Follow-up: Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Link to existing pages | /growth links to /goals, /journal. Lightweight hub. | ✓ |
| Inline drill-down | Cards expand in-place. Single-page experience. | |
| You decide | Claude picks. | |

**User's choice:** Link to existing pages

### Follow-up: Habits Page

| Option | Description | Selected |
|--------|-------------|----------|
| Summary on /growth only | Habits card shows streaks, consistency. No /habits page. | ✓ |
| Build /habits page | Full page with calendar heatmap, per-habit history. | |
| You decide | Claude decides during planning. | |

**User's choice:** Summary on /growth only

---

## Claude's Discretion

- PostgreSQL schema for synced tables
- Sync cron implementation (Python vs shell)
- API endpoint design for sync
- Sparkline chart config and card sizing
- Error/loading/empty states
- SWR refresh interval
- Exact correlation query SQL

## Deferred Ideas

- MC → andyOS migration (agents, yolo, tools pages) — future phase/milestone
- /habits detail page with calendar heatmap — future phase
- Real-time sync (webhooks) — future optimization
- Monthly/quarterly retrospective (ADV-03)
- Adaptive prompt difficulty (ADV-01)
