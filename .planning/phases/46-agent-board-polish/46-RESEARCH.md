# Phase 46: Agent Board Polish - Research

**Researched:** 2026-03-01
**Domain:** Dashboard UI -- agent card metrics + visual polish (Next.js 14 / Tailwind / better-sqlite3)
**Confidence:** HIGH

## Summary

Phase 46 combines two carried-forward items from v2.5: context usage indicators (Phase 31.1) and agent board visual polish (Phase 31.2). All required data already exists in `observability.db` (`llm_calls` table) -- no new data collection or schema changes needed. The implementation is a query extension + UI modification to the existing `/agents` page.

The prior research from Phase 31.1 (2026-02-21) has been re-verified against current production data and remains accurate. The key insight is unchanged: `input_tokens` alone is NOT context window usage -- you must sum `input_tokens + cache_read_tokens + cache_write_tokens` for actual context consumption. Cache hit rates are uniformly very high (>99%) in normal operation. The CONTEXT.md decisions call for a horizontal bar showing relative token usage (agent vs max across all agents) rather than the Phase 31.1 approach of context window percentage -- this changes the visualization strategy.

**Primary recommendation:** Extend `getAgentBoardData()` with three new aggregate queries, add utility functions, update AgentCard with a token usage bar + cache rate + cost display, and apply uniform card height/spacing fixes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Usage indicator = horizontal bar showing relative token usage (agent vs. max across all agents)
- Add 24h cost display (data already collected, just hidden)
- Cache hit rate indicator (cache_read / (cache_read + input) %)
- Visual polish: uniform card height, better spacing, refined typography

### Claude's Discretion
- (none specified -- all decisions locked)

### Deferred Ideas (OUT OF SCOPE)
- (none specified)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGENT-01 | Agent cards show context/token usage indicators (visual bar or percentage) | Token data already in `llm_calls` table. Usage bar shows each agent's 24h tokens relative to the highest agent. Cache hit rate and cost data also available. All queries verified against production. |
| AGENT-02 | Agent board has consistent visual styling and spacing | Current cards have variable height due to conditional model breakdown and task badges. Fix with min-height, consistent section spacing, and uniform typography. |
</phase_requirements>

## Standard Stack

### Core (already installed -- no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | ^12.6.2 | Query observability.db | Already used for all DB access |
| Tailwind CSS | ^3.4.10 | Progress bar + spacing fixes | Already used for all UI |
| React | 18.3.1 | AgentCard is already "use client" | Existing pattern |
| SWR | ^2.4.0 | Auto-refresh on /agents (30s polling) | Already wired up |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| class-variance-authority | ^0.7.1 | Variant styling if needed | Already available via Badge |
| clsx + tailwind-merge | via cn() | Conditional class merging | Already imported in agent-card.tsx |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tailwind div progress bar | shadcn Progress component | Not installed; would need `npx shadcn@latest add progress` + Radix dependency. Tailwind div is simpler. |
| Hardcoded model limits | Config file | Overkill -- only 2 models in use (claude-sonnet-4-5, claude-haiku-4-5) |

**Installation:** None needed. Zero new dependencies.

## Architecture Patterns

### Files to Modify

```
src/
├── lib/
│   ├── constants.ts          # ADD: MODEL_CONTEXT_LIMITS map
│   ├── utils.ts              # ADD: formatCost(), getContextColor(), getCacheColor()
│   └── queries/
│       └── agents.ts         # EXTEND: AgentBoardData type + getAgentBoardData() queries
├── components/
│   └── agents/
│       └── agent-card.tsx    # EXTEND: usage bar, cache, cost + visual polish
└── app/
    └── agents/
        └── page.tsx          # MINOR: adjust grid gap / loading skeleton height if needed
```

### Pattern 1: Relative Token Usage Bar

**What:** Horizontal bar showing each agent's 24h token total relative to the max across all agents. The API returns raw totals; the client computes relative widths.
**When to use:** When comparing agents to each other rather than against a fixed limit.

```typescript
// In agents page or card: compute max across all agents
const maxTokens = Math.max(...agents.map(a => a.tokens24h.total), 1);

// Per card: relative width
const relativeWidth = Math.round((agent.tokens24h.total / maxTokens) * 100);
```

This differs from Phase 31.1's approach (context window %) -- the user's CONTEXT.md explicitly chose "relative token usage (agent vs. max across all agents)" which is simpler and more useful for at-a-glance comparison.

### Pattern 2: Extend AgentBoardData Type

**What:** Add cache hit rate and 24h cost to existing interface.

```typescript
// In agents.ts -- extend existing interface
export interface AgentBoardData {
  // ... existing fields (id, name, system, lastSeen, status, tokens24h, errors24h, tasks) ...
  cacheHitRate: number | null;   // 0-100, null if no calls in 24h
  cost24h: number;               // USD, 0 if no calls
}
```

Note: `tokens24h.total` already exists and provides the data for the relative usage bar -- no new field needed for that.

### Pattern 3: Tailwind-Only Progress Bar

**What:** Pure div-based progress bar using Tailwind classes.

```tsx
// Relative usage bar in agent-card.tsx
<div className="h-1.5 w-full rounded-full bg-secondary">
  <div
    className="h-full rounded-full bg-blue-500 transition-all"
    style={{ width: `${relativeWidth}%` }}
  />
</div>
```

Uses a single accent color (blue-500) since this is a relative comparison, not a threshold indicator. The bar width IS the information -- no color coding needed.

### Pattern 4: Visual Polish Fixes

**What:** Uniform card height and consistent spacing.

```tsx
// Card: ensure minimum height for consistency
<Card className={`border-l-4 ${STATUS_BORDER[agent.status]} min-h-[220px] flex flex-col`}>
  <CardContent className="p-4 space-y-3 flex-1 flex flex-col">
    {/* Fixed sections */}
    <div>...</div>  {/* Name */}
    <div>...</div>  {/* Status */}
    <div>...</div>  {/* Tokens */}
    {/* Spacer pushes bottom section down */}
    <div className="flex-1" />
    {/* Bottom section: usage bar + cache + cost + badges */}
    <div>...</div>
  </CardContent>
</Card>
```

### Anti-Patterns to Avoid
- **Using `input_tokens` alone for any context metric:** Would show near-zero values. Must include `cache_read_tokens` and `cache_write_tokens` for meaningful numbers.
- **Adding a new API route:** Unnecessary. The existing `/api/agents` route already calls `getAgentBoardData()`.
- **Hardcoding relative bar max on server:** The max should be computed client-side from the full agents array, so it always reflects current data.
- **Using `cache_write_tokens` in cache hit rate:** Cache writes are NOT hits. Formula is `cache_read / (cache_read + input)`.
- **Computing relative widths on server:** Would require passing maxTokens alongside agents. Simpler to compute in the page component.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress bar | Custom React component | Inline Tailwind `<div>` pair | 2 divs, 3 classes. Single usage, no abstraction needed. |
| Color thresholds | Complex conditionals in JSX | Utility functions in `utils.ts` | Keeps component clean |
| Model context limits | Dynamic lookup | Hardcoded `MODEL_CONTEXT_LIMITS` in constants.ts | Only 2 models, values change rarely |
| Cost formatting | `Intl.NumberFormat` | `$${n.toFixed(2)}` | Single-user, USD-only |

## Common Pitfalls

### Pitfall 1: input_tokens Is NOT Context Window Usage
**What goes wrong:** Using `input_tokens` alone shows near-zero for all agents
**Why it happens:** Anthropic API splits input into `input_tokens` (uncached, often 24-57 tokens), `cache_read_tokens` (cached prompt, often 20K-100K+), and `cache_write_tokens` (newly cached)
**How to avoid:** For any token-related metric, use `input_tokens + cache_read_tokens + cache_write_tokens` as total context. However for this phase's relative bar, we use the already-computed `tokens24h.total` (which is `input_tokens + output_tokens`), so this pitfall applies mainly to the cache hit rate denominator.
**Warning signs:** All agents showing 0% or near-zero values

### Pitfall 2: Division by Zero in Cache Hit Rate
**What goes wrong:** Agent with zero LLM calls in 24h causes divide-by-zero
**Why it happens:** `sum(cache_read_tokens)` and `sum(input_tokens)` both return NULL/0 for inactive agents
**How to avoid:** Check `total > 0` before dividing. Return `null` for agents with no data.
**Warning signs:** NaN or Infinity in the UI

### Pitfall 3: Bob/Main Agent ID Split
**What goes wrong:** Missing data for Bob because some records use `agent_id = 'bob'` and others use `agent_id = 'main'`
**Why it happens:** Historical naming convention
**How to avoid:** Follow existing pattern: `const agentIds = agent.id === "main" ? ["main", "bob"] : [agent.id]`
**Warning signs:** Bob showing lower-than-expected metrics

### Pitfall 4: Variable Card Height
**What goes wrong:** Cards jump around or have uneven heights across the 4-column grid
**Why it happens:** Token breakdown line is conditional (`Object.keys(byModel).length > 0`), task badge line is conditional (`totalActive > 0`), creating variable content height
**How to avoid:** Use `min-h-[Xpx]` on the Card and flexbox with a spacer to push the bottom section down consistently
**Warning signs:** Cards in the same row having different heights, text jumping when data updates

### Pitfall 5: Cache Hit Rates Are Always >99%
**What goes wrong:** Not a bug, but the amber/red thresholds (<20%, <50%) may never trigger
**Why it happens:** Claude's prompt caching is extremely effective -- verified from production data showing >99.9% hit rates for all active agents
**How to avoid:** This is expected. The indicator confirms healthy caching. If rates drop below 99%, it signals a real problem worth investigating. Keep the thresholds -- they serve as anomaly detection.

## Code Examples

### Query Extensions for agents.ts

```typescript
// Inside the AGENTS.map() loop in getAgentBoardData(), after existing token/error queries:

// --- Cache hit rate (24h) ---
let cacheHitRate: number | null = null;
if (obsDb) {
  try {
    const agentIds = agent.id === "main" ? ["main", "bob"] : [agent.id];
    const placeholders = agentIds.map(() => "?").join(",");
    const row = obsDb.prepare(`
      SELECT sum(cache_read_tokens) as cache_read,
             sum(input_tokens + cache_read_tokens) as total_input
      FROM llm_calls
      WHERE agent_id IN (${placeholders})
        AND created_at > datetime('now', '-24 hours')
    `).get(...agentIds) as { cache_read: number; total_input: number } | undefined;
    if (row && row.total_input > 0) {
      cacheHitRate = Math.round((row.cache_read / row.total_input) * 100);
    }
  } catch { /* table may not exist */ }
}

// --- 24h cost ---
let cost24h = 0;
if (obsDb) {
  try {
    const agentIds = agent.id === "main" ? ["main", "bob"] : [agent.id];
    const placeholders = agentIds.map(() => "?").join(",");
    const row = obsDb.prepare(`
      SELECT sum(estimated_cost_usd) as cost
      FROM llm_calls
      WHERE agent_id IN (${placeholders})
        AND created_at > datetime('now', '-24 hours')
    `).get(...agentIds) as { cost: number } | undefined;
    if (row?.cost) cost24h = row.cost;
  } catch { /* table may not exist */ }
}
```

### Utility Functions for utils.ts

```typescript
export function getContextColor(pct: number | null): string {
  if (pct === null) return "text-muted-foreground";
  if (pct > 80) return "text-rose-400";
  if (pct > 60) return "text-amber-400";
  return "text-emerald-400";
}

export function getCacheColor(rate: number | null): string {
  if (rate === null) return "text-muted-foreground";
  if (rate < 20) return "text-rose-400";
  if (rate < 50) return "text-amber-400";
  return "text-emerald-400";
}

export function formatCost(usd: number): string {
  return `$${usd.toFixed(2)}`;
}
```

### AgentCard Context Section

```tsx
{/* Usage Metrics */}
<div className="space-y-2 border-t border-border pt-3">
  {/* Relative Usage Bar */}
  <div>
    <div className="flex items-center justify-between text-xs mb-1">
      <span className="text-muted-foreground">Usage</span>
      <span className="text-foreground">{formatTokens(agent.tokens24h.total)}</span>
    </div>
    <div className="h-1.5 w-full rounded-full bg-secondary">
      <div
        className="h-full rounded-full bg-blue-500 transition-all"
        style={{ width: `${relativeWidth}%` }}
      />
    </div>
  </div>

  {/* Cache + Cost row */}
  <div className="flex items-center justify-between text-xs">
    <div className="flex items-center gap-3">
      <span className="text-muted-foreground">Cache</span>
      <span className={getCacheColor(agent.cacheHitRate)}>
        {agent.cacheHitRate !== null ? `${agent.cacheHitRate}%` : "\u2014"}
      </span>
    </div>
    <span className="text-muted-foreground">{formatCost(agent.cost24h)}</span>
  </div>
</div>
```

### Visual Polish -- Uniform Card Height

```tsx
// agent-card.tsx: wrap in flex column with spacer
<Card className={`border-l-4 ${STATUS_BORDER[agent.status]} flex flex-col`}>
  <CardContent className="p-4 space-y-3 flex-1 flex flex-col">
    {/* Top sections: name, status, tokens -- fixed content */}
    <div>...</div>
    <div>...</div>
    <div>...</div>

    {/* Spacer: pushes bottom content to card bottom */}
    <div className="flex-1" />

    {/* Bottom sections: usage metrics, badges -- always at card bottom */}
    <div className="space-y-2 border-t border-border pt-3">...</div>
    <div className="flex items-center gap-2">...</div>
  </CardContent>
</Card>
```

### Relative Width Computation in Page

```tsx
// In agents/page.tsx, compute max after SWR data arrives:
const maxTokens = data ? Math.max(...data.agents.map(a => a.tokens24h.total), 1) : 1;

// Pass to each card:
<AgentCard key={agent.id} agent={agent} maxTokens={maxTokens} />
```

## Data Profile (Verified from Production -- 2026-03-01)

### Current 24h Data
| Agent | Model | Calls | Input Tokens | Cache Read | Cache Write | Cost |
|-------|-------|-------|-------------|------------|-------------|------|
| Bob (main) | sonnet-4-5 | 568 | 18,959 | 61,567,597 | 4,245,719 | $5.17 |
| Vector (rangeos) | haiku-4-5 | 184 | 6,667 | 20,889,998 | 184,827 | $0.43 |
| Scout (landos) | haiku-4-5 | 184 | 5,462 | 16,389,772 | 148,486 | $0.39 |
| Sentinel (ops) | haiku-4-5 | 184 | 4,570 | 15,203,642 | 177,137 | $0.35 |
| Bob (main) | haiku-4-5 | 2 | 443 | 1,213,804 | 36,765 | $0.09 |
| Sentinel (ops) | sonnet-4-5 | 2 | 48 | 45,928 | 10,635 | $0.03 |
| Quill/Sage/Ezra | -- | 0 | 0 | 0 | 0 | $0.00 |

### Cache Hit Rates (Computed)
| Agent | Hit Rate |
|-------|----------|
| Bob | >99.9% |
| Vector | >99.9% |
| Scout | >99.9% |
| Sentinel | >99.9% |
| Quill/Sage/Ezra | null (no calls) |

### Key Observations
- Token totals (for relative bar): Bob ~375K dominates, others cluster around 75-90K
- Cache hit rates are uniformly >99% -- the threshold colors serve as anomaly detection
- Cost range: $0 to ~$5/day
- The `tokens24h.total` field already exists in the data (input_tokens + output_tokens sum) and will drive the relative bar

### DB Schema (Confirmed)
```sql
CREATE TABLE llm_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  session_key TEXT,
  model TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'anthropic',
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_read_tokens INTEGER DEFAULT 0,
  cache_write_tokens INTEGER DEFAULT 0,
  estimated_cost_usd REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
```

### Available UI Components (shadcn)
badge, button, card, chart, input, scroll-area, separator, table
(No Progress component -- use Tailwind div approach)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 31.1 context window % | Relative token usage bar (agent vs max) | CONTEXT.md decision | Simpler, more useful for comparison |
| Hidden cost data | Visible per-agent 24h cost | This phase | Already tracked, just needs display |
| No cache visibility | Cache hit rate percentage | This phase | Confirms healthy caching, detects anomalies |

## Open Questions

1. **Relative bar: include or exclude output_tokens?**
   - What we know: `tokens24h.total` already sums `input_tokens + output_tokens`. This is displayed as "375.5k tokens" on cards. The CONTEXT.md says "relative token usage" which naturally maps to this existing total.
   - Recommendation: Use the existing `tokens24h.total` -- it's already computed and displayed, and represents the agent's overall token footprint. No query changes needed for the bar data.

2. **Card height min-h value**
   - What we know: Current cards are ~160-200px depending on content. Adding the usage section adds ~80px.
   - What's unclear: Exact pixel height won't be known until rendering with real data.
   - Recommendation: Start with `min-h-[260px]` and adjust during implementation. The flexbox spacer approach handles height variance gracefully.

## Sources

### Primary (HIGH confidence)
- EC2 observability.db direct inspection via SSH (2026-03-01) -- schema, fresh 24h data, all queries verified
- EC2 Mission Control codebase via SSH (2026-03-01) -- all 8 source files read directly
- Phase 31.1 Research (2026-02-21) -- prior investigation of same domain, re-verified

### Secondary (MEDIUM confidence)
- Phase 31 Plan 02 Summary -- established patterns for agent card layout and styling conventions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, extending existing patterns
- Architecture: HIGH -- all files read from production, data verified, patterns established
- Pitfalls: HIGH -- production data profiled, token semantics verified from prior research + Anthropic docs

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable domain -- model limits and DB schema change infrequently)
