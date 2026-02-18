# Phase 26: Agent Observability - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure LLM hooks to capture usage data across all 7 agents, store and summarize metrics, and surface an observability section in the morning briefing that flags anomalies. No new agent capabilities — this is instrumentation and reporting.

</domain>

<decisions>
## Implementation Decisions

### Metrics depth
- Track per-agent token usage (input + output), model distribution (Haiku/Sonnet/Opus), and turn counts for the last 24 hours
- Include estimated cost per agent — map tokens × model pricing to rough daily dollar cost
- Track error count + most recent error message per agent (not full error log)
- Track rate limit proximity — monitor rate limit headers from API responses, flag in briefing when approaching thresholds (>80% of limit)
- Track average latency (response time) per agent over 24h

### Anomaly logic
- Use 7-day rolling average as baseline per agent
- Warning flag at 2x rolling average, critical flag at 4x or on repeated errors
- Two severity levels in briefing: warning and critical (critical highlighted differently)
- Flag zero activity — if an agent that ran every day in the last 7 days has zero activity, surface as a warning
- System is new, no baseline data exists yet — first week of data collection will establish rolling averages before anomaly detection activates

### Claude's Discretion
- Briefing format and presentation style (follow existing morning briefing patterns)
- Agent granularity — per-agent totals for all 7 agents, with per-cron breakdown where it adds clarity
- Storage mechanism — where hook data lands, retention period, DB choice
- Hook implementation details — which OpenClaw hook events to use, payload structure
- How to handle the cold-start period before 7 days of data exist

</decisions>

<specifics>
## Specific Ideas

- Cost estimates don't need to be exact — rough order of magnitude from published Anthropic pricing is fine
- Rate limit tracking should use whatever headers the API naturally returns, not require extra API calls
- 2x threshold was chosen as the starting point; can tighten to 1.5x after a month of baseline data

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-agent-observability*
*Context gathered: 2026-02-18*
