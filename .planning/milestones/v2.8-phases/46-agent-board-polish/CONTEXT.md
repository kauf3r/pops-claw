# Phase 46: Agent Board Polish — Context

## Goal
Agent cards convey resource usage at a glance and the board looks polished.

## Requirements
- **AGENT-01**: Context/token usage indicator on each agent card
- **AGENT-02**: Consistent spacing, alignment, and visual styling across all 7 cards

## Success Criteria
1. Each agent card shows a visual context/token usage indicator (bar, percentage, or similar)
2. Agent board has consistent spacing, alignment, and visual styling across all 7 cards
3. Usage indicators update on SWR refresh cycle

## Current State

### What Exists
- `/agents` page with 7 agent cards in responsive grid (1/2/4 col)
- Each card shows: name, status, last seen, 24h token total, model breakdown, tasks, errors
- `observability.db` tracks: `llm_calls` (input/output/cache tokens, cost), `agent_runs` (success, duration)
- Token formatting: `formatTokens()` for display, `formatModelBreakdown()` for model labels
- Status-based left border colors (emerald/amber/blue/rose)
- SWR auto-refresh already in place

### Data Available But Not Displayed
- `estimated_cost_usd` — tracked per LLM call, not shown anywhere
- `cache_read_tokens` / `cache_write_tokens` — stored, never queried
- `session_key` — exists in llm_calls but unused in queries
- Per-agent call counts and duration_ms

### Key Files (on EC2 ~/clawd/mission-control/)
| File | Purpose |
|------|---------|
| `src/app/agents/page.tsx` | Main page, SWR fetch |
| `src/components/agents/agent-card.tsx` | Agent card component |
| `src/components/agents/task-board.tsx` | Task board below cards |
| `src/app/api/agents/route.ts` | API route |
| `src/lib/queries/agents.ts` | SQL queries (getAgentBoardData) |
| `src/lib/utils.ts` | formatTokens, formatModelBreakdown |
| `src/lib/constants.ts` | AGENTS registry |
| `src/lib/chart-constants.ts` | Agent colors |

### Current Card Layout
1. Name + system ID
2. Status badge + RelativeTime "last seen"
3. Token total (e.g. "375.5k tokens") + model breakdown (e.g. "S: 337.7k . H: 18.5k")
4. Error count badge + active task count

### Live Data (typical 24h)
| Agent | Tokens | Cost | Model |
|-------|--------|------|-------|
| Bob | 375k | $5.22 | Sonnet |
| Vector | 90k | $0.43 | Haiku |
| Scout | 83k | $0.39 | Haiku |
| Sentinel | 75k | $0.38 | Haiku |
| Quill/Sage/Ezra | scheduled, intermittent | — | varies |

## Decisions
- Usage indicator = horizontal bar showing relative token usage (agent vs. max across all agents)
- Add 24h cost display (data already collected, just hidden)
- Cache hit rate indicator (cache_read / (cache_read + input) %)
- Visual polish: uniform card height, better spacing, refined typography
