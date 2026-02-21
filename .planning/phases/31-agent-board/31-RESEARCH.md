# Phase 31: Agent Board - Research

**Researched:** 2026-02-21
**Domain:** Next.js agent monitoring page, observability.db token/error queries, coordination.db heartbeat queries, agent card grid UI
**Confidence:** HIGH

## Summary

Phase 31 adds a dedicated `/agents` page to Mission Control that displays a card per agent (7 total) showing heartbeat status, 24-hour token usage by model, and error counts. The data layer already exists partially -- Phase 30 built `getAgentHealth()` in `src/lib/queries/agents.ts` that queries both coordination.db and observability.db for last-seen timestamps. Phase 31 needs to extend this with new queries against observability.db for per-agent token usage (grouped by model) and error counts within a 24-hour window.

The codebase is well-established: NavBar component with a `links` array (currently Dashboard + Calendar), SWR global polling at 30s, `getDb()` singleton factory, shadcn Card/Badge/Button/ScrollArea installed, Sora font, dark zinc theme. The `/agents` page will follow the same pattern as the dashboard: a "use client" page.tsx using `useSWR` to fetch from a new API route that returns per-agent detail data.

EC2 inspection (2026-02-21) confirmed real data: observability.db has 8,912 agent_runs across 5 agents and 2,208 llm_calls using 2 models (claude-haiku-4-5, claude-sonnet-4-5). In the last 24 hours alone: 1,023 LLM calls with significant token volume. coordination.db has 240 agent_activity entries with heartbeats every ~15 minutes for ops, rangeos, and landos. Sage and Ezra have zero data in both databases.

**Primary recommendation:** Build one new API route (`/api/agents`) returning per-agent detail (heartbeat status + 24h tokens by model + 24h error count), create the `/agents/page.tsx` with a 7-card responsive grid using status-colored left borders, and add "Agents" to the NavBar links array.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Uniform grid: all 7 cards same size, no hero/featured card
- Responsive columns: 4 on desktop (2 rows), 2 on tablet, 1 on mobile
- All info visible on each card -- no expand/collapse, no hover-to-reveal
- Subtle bordered cards with rounded corners
- Status color as thick left border accent (Linear-style)
- Page header: "Agents" title with fleet summary subtitle ("5 active . 1 stale . 1 down")
- Green = active (seen in last 5 min), Yellow = stale (5-30 min), Red = down (30+ min)
- Relative timestamps ("2m ago", "1h ago") with absolute timestamp on hover tooltip
- Color + text label ("Active" / "Stale" / "Down") for accessibility
- Total 24h token count as single number (e.g., "12.4k tokens")
- Model breakdown line below: "H: 8k . S: 3k . O: 1.4k" -- compact, no charts
- Error count as badge/pill: gray when 0, red when non-zero
- "Last 24 hours" label at page level, not repeated per card
- Sort by status priority: Down -> Stale -> Active, then alphabetical within group
- Agent name shown prominently, role/system as subtitle (e.g., "Scout -- landos")
- Uniform card styling -- only left border color varies by status, no per-agent accent colors

### Claude's Discretion
- Exact spacing, typography, and card dimensions
- Loading state design
- How to handle agents with no data yet (never seen)
- Dark/neutral background treatment

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-01 | Agent board page displays a card for each of the 7 agents | New `/agents/page.tsx` rendering 7 cards from AGENTS constant. API route returns array of 7 agent detail objects. NavBar updated with "Agents" link. |
| AGNT-02 | Each agent card shows heartbeat status (alive/down, last seen timestamp) | Extend existing agent health query to use 5-min/30-min thresholds (replacing 1-hour). coordination.db `agent_activity` has heartbeats every ~15 min. RelativeTime component for relative timestamps, native `title` attribute or shadcn Tooltip for absolute hover. |
| AGNT-03 | Each agent card shows token usage and model distribution (Haiku/Sonnet/Opus) from observability.db | New query against `llm_calls` table: `SELECT model, count(*), sum(input_tokens+output_tokens+cache_read_tokens+cache_write_tokens) ... WHERE agent_id=? AND created_at > datetime('now', '-24 hours') GROUP BY model`. Two models in current data: claude-haiku-4-5, claude-sonnet-4-5. |
| AGNT-04 | Each agent card shows recent error count | New query against `agent_runs` table: `SELECT count(*) FROM agent_runs WHERE agent_id=? AND success=0 AND created_at > datetime('now', '-24 hours')`. Currently 0 errors in last 24h (20 total historical for main). |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | ^12.6.2 | SQLite queries via existing `getDb()` singleton factory | Already in use, read-only WAL, busy_timeout=5000 |
| swr | ^2.4.0 | Client-side data fetching with 30s polling (global SWRConfig) | Already configured in providers.tsx |
| next | 14.2.15 | App Router, API routes, Link navigation | Running in production |
| date-fns | ^3.6.0 | Relative timestamps via existing RelativeTime component | Already installed and used |
| lucide-react | ^0.475.0 | Icons (Bot, AlertTriangle, etc.) | Already installed |
| tailwindcss | ^3.4.10 | Styling, responsive grid, left-border accent | Already configured |

### shadcn/ui Components (already installed)
| Component | Status | Use In Phase 31 |
|-----------|--------|-----------------|
| Card | Installed | Agent cards (with custom left-border override) |
| Badge | Installed (success/warning/error variants) | Error count pill, status label |
| Button | Installed | Potential future use |
| ScrollArea | Installed | Not needed (7 cards fits without scroll) |

### New Component Needed
| Component | How to Add | Purpose |
|-----------|-----------|---------|
| Tooltip (shadcn/ui) | `npx shadcn-ui@latest add tooltip` | Absolute timestamp on hover per CONTEXT.md requirement. Alternatively: use native HTML `title` attribute to avoid adding a dependency. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shadcn Tooltip | Native `title` attribute | Native title is zero-dependency, ugly but functional. Tooltip is prettier but requires `@radix-ui/react-tooltip` install. Recommend native `title` -- simpler, sufficient for single-user dashboard. |
| Separate `/api/agents` route | Extend existing `/api/dashboard/agents` | Extending would change the existing route's contract. Prefer a new route to keep dashboard data lean and agent board data detailed. |

### No Major New Packages Needed
The only potential addition is `@radix-ui/react-tooltip` for shadcn Tooltip. Using native `title` avoids this entirely.

## Architecture Patterns

### Recommended Project Structure (New/Modified Files)
```
src/
├── app/
│   ├── agents/
│   │   └── page.tsx              # NEW: agent board page
│   ├── api/
│   │   └── agents/
│   │       └── route.ts          # NEW: detailed per-agent data API
│   └── ...existing...
├── components/
│   ├── NavBar.tsx                 # MODIFY: add "Agents" link
│   └── agents/
│       └── agent-card.tsx         # NEW: individual agent card component
├── lib/
│   ├── queries/
│   │   └── agents.ts             # MODIFY: add getAgentBoardData() for detailed per-agent stats
│   └── constants.ts              # MODIFY: add agent system/role mapping if needed
```

### Pattern 1: Agent Board API Route
**What:** A single API route that returns all 7 agents with heartbeat status, 24h token usage by model, and 24h error count.
**Why single route:** 7 agents with 3 data points each = small payload. One fetch is simpler than 7 individual agent fetches.
**Pattern:**
```typescript
// GET /api/agents
// Returns: { agents: AgentBoardData[], summary: { active: N, stale: N, down: N } }

interface AgentBoardData {
  id: string;
  name: string;
  system: string;           // "main", "landos", "rangeos", etc.
  lastSeen: string | null;  // ISO timestamp
  status: "active" | "stale" | "down";
  tokens24h: {
    total: number;           // sum of all token types
    byModel: Record<string, number>;  // e.g., {"claude-haiku-4-5": 8000, "claude-sonnet-4-5": 3000}
  };
  errors24h: number;
}
```

### Pattern 2: Status-Colored Left Border (Linear-Style)
**What:** Each agent card has a thick left border whose color reflects status (green/yellow/red). All other card styling is identical.
**How:** Override shadcn Card's border-left with Tailwind classes dynamically:
```typescript
const STATUS_BORDER: Record<string, string> = {
  active: "border-l-emerald-500",
  stale: "border-l-amber-500",
  down: "border-l-rose-500",
};

// On the Card component:
<Card className={`border-l-4 ${STATUS_BORDER[agent.status]}`}>
```

### Pattern 3: Status Thresholds (User-Locked)
**What:** 3-tier status based on time since last seen.
**Thresholds:**
- Green/Active: last seen within 5 minutes
- Yellow/Stale: last seen 5-30 minutes ago
- Red/Down: last seen 30+ minutes ago OR never seen
**Note:** Phase 30 used a 1-hour threshold. Phase 31 CONTEXT.md explicitly locks 5-min/30-min thresholds. The agent board query must use these new thresholds.

### Pattern 4: Fleet Summary Header
**What:** Page header shows "Agents" title with subtitle summarizing fleet status.
**Format:** "5 active . 1 stale . 1 down" -- counts derived from the same API response.
**Pattern:** Compute from agents array in the client component, no separate API call needed.

### Pattern 5: Token Count Formatting
**What:** Display large token numbers in compact format (e.g., "12.4k", "1.2M").
**Pattern:**
```typescript
function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
```
**Model abbreviation:** Map model names to short labels: "claude-haiku-4-5" -> "H", "claude-sonnet-4-5" -> "S", "claude-opus-4" -> "O".

### Pattern 6: Sort Order (User-Locked)
**What:** Cards sorted by status priority: Down first, Stale second, Active last. Alphabetical within each group.
**Why Down first:** Problems surface to the top -- you see what needs attention first.
**Pattern:**
```typescript
const STATUS_ORDER: Record<string, number> = { down: 0, stale: 1, active: 2 };
agents.sort((a, b) => {
  const statusDiff = STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
  if (statusDiff !== 0) return statusDiff;
  return a.name.localeCompare(b.name);
});
```

### Pattern 7: Never-Seen Agents (Claude's Discretion)
**Recommendation:** Agents with no data in either database (sage, ezra currently) should show as "Down" status with a "Never seen" label instead of a relative timestamp. They get the red left border and sort to the top. This is more honest than "idle" -- if you've never heard from an agent, you should know about it. The Phase 30 decision to show them as "idle" was for the dashboard summary card. The agent board, being a detail view, should be more explicit.

### Anti-Patterns to Avoid
- **Per-agent API calls:** Don't make 7 separate fetch calls. One API route returns all 7.
- **Querying token totals without time window:** Always use `WHERE created_at > datetime('now', '-24 hours')`. Without this, numbers grow indefinitely and become meaningless.
- **Hardcoding model names in display:** Use a mapping function. New models may appear as OpenClaw updates.
- **Ignoring "bob" vs "main" agent_id inconsistency:** coordination.db has some entries with agent_id="bob" instead of "main". The query should handle both: `WHERE agent_id IN ('main', 'bob')` for the main agent.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative timestamps | Custom "X min ago" logic | Existing `RelativeTime` component (date-fns `formatDistanceToNow`) | Already handles hydration, auto-updates every 60s |
| Token formatting | Inline formatting per card | Shared `formatTokens()` utility function | Consistent formatting, testable, reusable |
| Model name mapping | Inline string manipulation | Constants map `MODEL_LABELS` | New models won't break display, single update point |
| Agent sorting | Ad-hoc sort in component | Shared sort function or server-side sort | Consistent ordering, no client-side flicker |
| Data polling | Custom setInterval | SWR global polling (already configured at 30s) | Error retry, dedup, stale-while-revalidate |
| Status computation | Client-side timestamp math | Server-side in API route (timestamps relative to server time) | Server has consistent clock, avoids client timezone issues |

**Key insight:** Phase 31 is the second page using the established data layer. Follow the exact patterns from Phase 30 (query module -> API route -> SWR hook -> components). Don't invent new patterns.

## Common Pitfalls

### Pitfall 1: Agent ID "bob" vs "main" Inconsistency
**What goes wrong:** Queries for agent_id="main" miss entries where agent_id="bob" in coordination.db.
**Why it happens:** coordination.db has 7 entries with agent_id="bob" (cron and session types) alongside 1 entry with agent_id="main". The gateway uses different IDs depending on context.
**How to avoid:** For the main agent, query both: `WHERE agent_id IN ('main', 'bob')`. Or normalize in the query module: map "bob" -> "main" in results.
**Warning signs:** Main/Bob shows as having no recent activity when it clearly does.

### Pitfall 2: Token Count Type -- Total vs Input+Output Only
**What goes wrong:** Displaying input_tokens + output_tokens as "total tokens" when cache_read_tokens and cache_write_tokens are orders of magnitude larger.
**Why it happens:** observability.db tracks 4 token types: input_tokens, output_tokens, cache_read_tokens, cache_write_tokens. Cache tokens dominate (e.g., main/sonnet 24h: input=18k, output=440k, cache_read=46.5M, cache_write=5.7M).
**How to avoid:** Decision needed: show input+output only (meaningful usage) OR include cache tokens (true API token count). Recommendation: show input+output as the headline "token usage" number, since cache tokens represent context reuse rather than new generation. If cache tokens are included, the numbers become enormous and less actionable.
**Warning signs:** Agent showing "52M tokens" in 24h when actual generation was ~460k.

### Pitfall 3: Heartbeat Agents vs LLM-Only Agents
**What goes wrong:** Agents that send heartbeats (ops, rangeos, landos) show as "active" even when they haven't done real work, while main/Bob (which does all the LLM work) might show as "stale" if it hasn't sent a heartbeat recently.
**Why it happens:** ops/rangeos/landos send heartbeats every ~15 minutes via agent_activity. main/Bob's activity is recorded in observability.db agent_runs but not always in coordination.db.
**How to avoid:** Check BOTH databases for "last seen" (existing logic in agents.ts does this correctly). The current `getAgentHealth()` already checks both coordination and observability for last activity.
**Warning signs:** Bob showing as "stale" when it ran an LLM call 2 minutes ago.

### Pitfall 4: Status Threshold Mismatch with Phase 30
**What goes wrong:** Phase 30 dashboard agent health card uses 1-hour active threshold, but Phase 31 CONTEXT.md locks 5-min/30-min thresholds. If shared, they'll conflict.
**Why it happens:** Different use cases: dashboard summary vs detailed agent board.
**How to avoid:** Phase 31 should have its own status computation in its query/API, NOT reuse Phase 30's `getAgentHealth()` threshold logic. Either add new functions or pass threshold parameters.
**Warning signs:** Agent board showing different status than dashboard for the same agent.

### Pitfall 5: Observability Timestamps vs Coordination Timestamps
**What goes wrong:** 24-hour window query produces inconsistent results because databases use different timestamp formats.
**Why it happens:** observability.db uses ISO 8601 with milliseconds ("2026-02-21T16:36:09.812Z"), coordination.db uses SQLite datetime format ("2026-02-21 16:36:06"). The SQLite `datetime('now', '-24 hours')` comparison works with the coordination format but may not correctly compare with ISO+Z format.
**How to avoid:** For observability.db queries, the ISO format with datetime() comparison works because SQLite's text comparison handles it. Verified: `WHERE created_at > datetime('now', '-24 hours')` returns correct results for both formats. But be aware of timezone: observability uses UTC (Z suffix), coordination uses UTC (no suffix, but datetime('now') is UTC).
**Warning signs:** Query returns 0 results when data clearly exists.

### Pitfall 6: No Tooltip Component Installed
**What goes wrong:** CONTEXT.md requires "absolute timestamp on hover tooltip" but shadcn Tooltip is not installed.
**How to avoid:** Either install shadcn Tooltip (`npx shadcn-ui@latest add tooltip`) or use native HTML `title` attribute. Recommend native `title` for simplicity -- it shows the browser's default tooltip with the absolute timestamp. Install shadcn Tooltip only if the native tooltip feels too ugly.
**Warning signs:** No hover behavior on timestamps.

## Code Examples

### Agent Board Query (New)
```typescript
// src/lib/queries/agents.ts -- ADD to existing file

interface AgentTokens {
  total: number;
  byModel: Record<string, number>;
}

export interface AgentBoardData {
  id: string;
  name: string;
  system: string;
  lastSeen: string | null;
  status: "active" | "stale" | "down";
  tokens24h: AgentTokens;
  errors24h: number;
}

export interface AgentBoardSummary {
  agents: AgentBoardData[];
  summary: { active: number; stale: number; down: number };
}

export function getAgentBoardData(): AgentBoardSummary {
  const coordDb = getDb("coordination");
  const obsDb = getDb("observability");

  const now = Date.now();
  const FIVE_MIN = 5 * 60 * 1000;
  const THIRTY_MIN = 30 * 60 * 1000;

  const agents: AgentBoardData[] = AGENTS.map((agent) => {
    // --- Last seen (from both DBs) ---
    let lastSeen: string | null = null;

    if (coordDb) {
      try {
        // Handle "bob" alias for "main"
        const ids = agent.id === "main" ? ["main", "bob"] : [agent.id];
        const placeholders = ids.map(() => "?").join(",");
        const row = coordDb
          .prepare(
            `SELECT created_at FROM agent_activity
             WHERE agent_id IN (${placeholders})
             ORDER BY created_at DESC LIMIT 1`
          )
          .get(...ids) as { created_at: string } | undefined;
        if (row) lastSeen = row.created_at;
      } catch { /* table may not exist */ }
    }

    if (obsDb) {
      try {
        const row = obsDb
          .prepare(
            `SELECT created_at FROM agent_runs
             WHERE agent_id = ?
             ORDER BY created_at DESC LIMIT 1`
          )
          .get(agent.id) as { created_at: string } | undefined;
        if (row && (!lastSeen || new Date(row.created_at) > new Date(lastSeen))) {
          lastSeen = row.created_at;
        }
      } catch { /* table may not exist */ }
    }

    // --- Status with 5-min / 30-min thresholds ---
    let status: "active" | "stale" | "down" = "down";
    if (lastSeen) {
      const elapsed = now - new Date(lastSeen).getTime();
      if (elapsed < FIVE_MIN) status = "active";
      else if (elapsed < THIRTY_MIN) status = "stale";
      // else remains "down"
    }

    // --- 24h token usage by model ---
    let tokens24h: AgentTokens = { total: 0, byModel: {} };
    if (obsDb) {
      try {
        const rows = obsDb
          .prepare(
            `SELECT model,
                    sum(input_tokens + output_tokens) as tokens
             FROM llm_calls
             WHERE agent_id = ?
               AND created_at > datetime('now', '-24 hours')
             GROUP BY model`
          )
          .all(agent.id) as Array<{ model: string; tokens: number }>;

        let total = 0;
        const byModel: Record<string, number> = {};
        for (const row of rows) {
          byModel[row.model] = row.tokens;
          total += row.tokens;
        }
        tokens24h = { total, byModel };
      } catch { /* table may not exist */ }
    }

    // --- 24h error count ---
    let errors24h = 0;
    if (obsDb) {
      try {
        const row = obsDb
          .prepare(
            `SELECT count(*) as cnt FROM agent_runs
             WHERE agent_id = ?
               AND success = 0
               AND created_at > datetime('now', '-24 hours')`
          )
          .get(agent.id) as { cnt: number } | undefined;
        if (row) errors24h = row.cnt;
      } catch { /* table may not exist */ }
    }

    return {
      id: agent.id,
      name: agent.name,
      system: agent.id,
      lastSeen: lastSeen ? new Date(lastSeen).toISOString() : null,
      status,
      tokens24h,
      errors24h,
    };
  });

  // Sort: down -> stale -> active, then alphabetical
  const ORDER: Record<string, number> = { down: 0, stale: 1, active: 2 };
  agents.sort((a, b) => {
    const d = ORDER[a.status] - ORDER[b.status];
    return d !== 0 ? d : a.name.localeCompare(b.name);
  });

  const summary = {
    active: agents.filter((a) => a.status === "active").length,
    stale: agents.filter((a) => a.status === "stale").length,
    down: agents.filter((a) => a.status === "down").length,
  };

  return { agents, summary };
}
```

### Token Formatting Utility
```typescript
// src/lib/utils.ts -- ADD to existing file

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export const MODEL_LABELS: Record<string, string> = {
  "claude-haiku-4-5": "H",
  "claude-sonnet-4-5": "S",
  "claude-opus-4": "O",
};

export function formatModelBreakdown(byModel: Record<string, number>): string {
  return Object.entries(byModel)
    .sort(([, a], [, b]) => b - a) // highest first
    .map(([model, tokens]) => `${MODEL_LABELS[model] ?? model}: ${formatTokens(tokens)}`)
    .join(" . ");
}
```

### Agent Card Component
```typescript
// src/components/agents/agent-card.tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RelativeTime } from "@/components/dashboard/relative-time";
import { formatTokens, formatModelBreakdown } from "@/lib/utils";
import type { AgentBoardData } from "@/lib/queries/agents";

const STATUS_BORDER: Record<string, string> = {
  active: "border-l-emerald-500",
  stale: "border-l-amber-500",
  down: "border-l-rose-500",
};

const STATUS_LABEL: Record<string, { text: string; className: string }> = {
  active: { text: "Active", className: "text-emerald-400" },
  stale: { text: "Stale", className: "text-amber-400" },
  down: { text: "Down", className: "text-rose-400" },
};

export function AgentCard({ agent }: { agent: AgentBoardData }) {
  const label = STATUS_LABEL[agent.status];

  return (
    <Card className={`border-l-4 ${STATUS_BORDER[agent.status]}`}>
      <CardContent className="p-4 space-y-3">
        {/* Name + System */}
        <div>
          <h3 className="text-base font-semibold text-foreground">{agent.name}</h3>
          <p className="text-xs text-muted-foreground">{agent.system}</p>
        </div>

        {/* Status + Last Seen */}
        <div className="flex items-center justify-between">
          <span className={`text-xs font-medium ${label.className}`}>{label.text}</span>
          {agent.lastSeen ? (
            <span title={new Date(agent.lastSeen).toLocaleString()}>
              <RelativeTime date={agent.lastSeen} className="text-xs text-muted-foreground" />
            </span>
          ) : (
            <span className="text-xs text-muted-foreground">Never seen</span>
          )}
        </div>

        {/* Token Usage */}
        <div>
          <p className="text-sm font-medium text-foreground">
            {formatTokens(agent.tokens24h.total)} tokens
          </p>
          {Object.keys(agent.tokens24h.byModel).length > 0 && (
            <p className="text-xs text-muted-foreground">
              {formatModelBreakdown(agent.tokens24h.byModel)}
            </p>
          )}
        </div>

        {/* Error Count */}
        <div>
          <Badge variant={agent.errors24h > 0 ? "destructive" : "secondary"}>
            {agent.errors24h} error{agent.errors24h !== 1 ? "s" : ""}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
```

### NavBar Update
```typescript
// src/components/NavBar.tsx -- MODIFY links array
const links = [
  { href: "/", label: "Dashboard" },
  { href: "/agents", label: "Agents" },   // ADD
  { href: "/calendar", label: "Calendar" },
];
```

### API Route
```typescript
// src/app/api/agents/route.ts
import { NextResponse } from "next/server";
import { getAgentBoardData } from "@/lib/queries/agents";

export const dynamic = "force-dynamic";

export function GET() {
  try {
    return NextResponse.json(getAgentBoardData());
  } catch (error) {
    return NextResponse.json(
      { agents: [], summary: { active: 0, stale: 0, down: 0 }, error: String(error) },
      { status: 500 }
    );
  }
}
```

## Discovered Facts (from EC2 Inspection 2026-02-21)

### Observability.db Schema (VERIFIED)
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

CREATE TABLE agent_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  session_key TEXT,
  success INTEGER DEFAULT 1,
  error TEXT,
  duration_ms INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
```

### Coordination.db Schema (VERIFIED)
```sql
CREATE TABLE agent_activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  summary TEXT,
  created_at TEXT
);

CREATE TABLE agent_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_id TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT DEFAULT "pending",
  priority INTEGER DEFAULT 2,
  beads_issue_id TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE agent_messages (...);
CREATE TABLE user_calendar_tasks (...);
```

### Real 24-Hour LLM Data (2026-02-21)
| Agent | Model | Calls | Input | Output | Cache Read | Cache Write |
|-------|-------|-------|-------|--------|------------|-------------|
| main | claude-sonnet-4-5 | 523 | 18,057 | 440,033 | 46,464,507 | 5,740,099 |
| ops | claude-haiku-4-5 | 166 | 6,055 | 93,254 | 22,481,351 | 235,461 |
| landos | claude-haiku-4-5 | 165 | 5,862 | 79,204 | 18,170,824 | 173,574 |
| rangeos | claude-haiku-4-5 | 163 | 5,283 | 95,975 | 21,470,135 | 236,769 |
| quill | claude-sonnet-4-5 | 3 | 30 | 1,561 | 7,263 | 31,430 |
| ops | claude-sonnet-4-5 | 2 | 48 | 2,695 | 45,928 | 10,796 |
| rangeos | claude-sonnet-4-5 | 1 | 183 | 5,929 | 386,877 | 29,024 |

### Agent ID Inconsistency (coordination.db)
| agent_id | activity_type | count |
|----------|---------------|-------|
| landos | heartbeat | 77 |
| ops | heartbeat | 77 |
| rangeos | heartbeat | 76 |
| **bob** | cron | 6 |
| **bob** | session | 1 |
| **main** | coordination | 1 |
| ops | cron | 1 |
| quill | cron | 1 |

**Important:** "bob" is an alias for "main". Queries for main agent must check both IDs.

### Timestamp Formats (VERIFIED)
| Database | Format | Example |
|----------|--------|---------|
| observability.db llm_calls | ISO 8601 + Z | 2026-02-21T16:36:09.812Z |
| observability.db agent_runs | ISO 8601 + Z | 2026-02-21T16:36:09.788Z |
| coordination.db agent_activity | SQLite datetime | 2026-02-21 16:36:06 |

### Existing Code to Reuse
| File | Exports/Patterns | Reuse In Phase 31 |
|------|------------------|-------------------|
| `src/lib/constants.ts` | AGENTS array, StatusLevel type | Agent list, status type |
| `src/lib/db.ts` | getDb() singleton factory | Database access |
| `src/lib/db-paths.ts` | DB_PATHS, DbName type | Database paths |
| `src/lib/queries/agents.ts` | getAgentHealth() | Extend with getAgentBoardData() |
| `src/components/dashboard/relative-time.tsx` | RelativeTime component | Timestamp display |
| `src/components/dashboard/freshness-indicator.tsx` | FreshnessIndicator | Page freshness |
| `src/components/NavBar.tsx` | NavBar with links array | Add "Agents" link |
| `src/app/providers.tsx` | SWRConfig (30s polling) | Auto-refresh |

### Models in Use
Only 2 models observed in production data:
- `claude-haiku-4-5` (used by ops, landos, rangeos primarily)
- `claude-sonnet-4-5` (used by main/Bob primarily, plus quill)
- No `claude-opus-4` usage observed, but include "O" mapping for future-proofing

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 1-hour active threshold (Phase 30) | 5-min/30-min/30+ thresholds (Phase 31) | Phase 31 CONTEXT.md | More granular agent health visibility |
| Dashboard summary card only | Dedicated agent board page | Phase 31 | Per-agent detail at a glance |
| No token tracking display | 24h token usage with model breakdown | Phase 31 | Cost visibility per agent |

## Open Questions

1. **Token count: input+output only vs including cache tokens?**
   - What we know: Cache tokens (read+write) are 10-100x larger than input+output tokens. Main/Bob 24h: input+output = ~458k, cache = ~52M.
   - Recommendation: **Use input_tokens + output_tokens only** as the headline number. Cache tokens represent context window reuse and are not directly meaningful for workload monitoring. If needed later, add a hover tooltip showing cache breakdown.

2. **Should the agent board reuse /api/dashboard/agents or have its own route?**
   - What we know: /api/dashboard/agents returns {total, alive, detail, agents[{id, name, lastSeen, status}]}. Phase 31 needs additional token and error data.
   - Recommendation: **Create a new /api/agents route** with the extended payload. Don't modify the existing dashboard route -- it serves a different purpose and changing its contract could break the dashboard.

3. **How to handle the dashboard's Agent Health card after Phase 31?**
   - What we know: Dashboard shows "Agent Health" status card with Phase 30's 1-hour threshold. Agent board uses 5-min/30-min.
   - Recommendation: Leave the dashboard card as-is for now. It serves a different purpose (quick fleet overview vs detailed monitoring). The thresholds can be aligned in a future phase if needed.

## Sources

### Primary (HIGH confidence)
- EC2 direct inspection (2026-02-21) -- all database schemas, table contents, row counts, timestamp formats, agent IDs, model names
- Phase 30 RESEARCH.md, 30-01-PLAN.md, 30-02-PLAN.md -- established patterns, component library, API routes
- Phase 29 29-02-SUMMARY.md -- database connection layer, systemd service, infrastructure foundation
- Actual source code on EC2 -- constants.ts, agents.ts, db.ts, db-paths.ts, NavBar.tsx, page.tsx, status-card.tsx, relative-time.tsx, activity-feed.tsx, providers.tsx

### Secondary (MEDIUM confidence)
- None needed -- all findings verified directly on EC2

### Tertiary (LOW confidence)
- None -- all findings verified against live code and databases

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified working in Phase 29-30
- Architecture: HIGH -- follows exact patterns established in Phase 30 (query module -> API route -> SWR hook -> components), all building blocks exist
- Database queries: HIGH -- schemas confirmed via EC2 Python inspection, 24h token query tested live, timestamp formats verified
- Pitfalls: HIGH -- agent ID "bob" vs "main" inconsistency discovered via real data, token count types documented with real numbers, heartbeat patterns verified

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable infrastructure, schemas unlikely to change)
