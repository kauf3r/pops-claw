# Phase 32: Memory, Office & Visualization - Research

**Researched:** 2026-02-21
**Domain:** Dashboard pages (memory browser, office view, analytics charts), SQLite memory backend, Recharts visualization
**Confidence:** HIGH

## Summary

Phase 32 adds three new pages to the existing Mission Control dashboard: a memory browser (`/memory`), a virtual office (`/office`), and an analytics page (`/analytics`). The project already has Recharts 2.15.4 installed along with the shadcn/ui `chart.tsx` wrapper component (ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend). The existing codebase provides clear patterns for API routes, SWR data fetching, page layout, and card-based UI.

The memory backend uses per-agent SQLite files in `~/.openclaw/memory/` with FTS5 full-text search already built in. Only 4 of 7 agents have memory databases (main, landos, ops, rangeos -- quill/sage/ezra have none). The memory schema stores chunks (embedded text fragments from markdown files) not individual "memory" records, so the UI needs to present chunks grouped by their source file path as the browseable unit.

**Primary recommendation:** Build all three pages following the exact patterns from the existing `/agents` page -- SWR polling, skeleton loaders, API routes calling query modules, Card components. Use the existing shadcn chart wrapper for Recharts. Memory search uses FTS5 `MATCH` directly (already indexed). Office view is pure CSS/SVG with data from the existing agent heartbeat queries.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Memory Browser (/memory):** Card grid layout, each memory as card with agent name + timestamp + 2-3 line content preview (truncated with ellipsis, click to expand). Agent filtering via tabs across top ("All" + one tab per agent). Search bar at top filters cards live, works with active agent tab filter, highlights matching text. Cards should feel scannable like Notion's database view.
- **Office View (/office):** Top-down office floorplan, bird's-eye view with desks arranged in office layout, isometric-lite feel. Illustrated character avatars, unique cartoon/illustrated avatar per agent. Animated green pulse when working, gray/dim when idle. Small badge shows current task type. Idle threshold: 5 minutes without heartbeat/action.
- **Analytics (/analytics):** All 4 chart types on one /analytics page. Token usage: area charts per agent. Content pipeline: bar chart by status. Email volume: line chart over time. Cron success/failure: donut chart. Color palette from existing Tailwind theme, each agent gets distinct color. Default 7 days with range picker (24h / 7d / 30d). Hover tooltips + time range buttons, no zoom/pan.
- **Navigation:** Add Memory, Office, Analytics to sidebar. Order: Dashboard, Agents, Memory, Office, Analytics, Calendar. Consistent page structure with same header pattern. Skeleton loaders while data fetches.

### Claude's Discretion
- Exact card spacing and typography for memory grid
- Office floorplan desk arrangement and spacing
- Specific Recharts configuration and chart sizing
- Skeleton loader shape details per page
- Empty state messaging

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MEM-01 | Memory screen displays all agent memories from SQLite memory backend, browseable by agent | Memory stored in per-agent SQLite files at `~/.openclaw/memory/{agent_id}.sqlite`. Schema uses `chunks` table with FTS5 index. 4 agents have memory DBs (main, landos, ops, rangeos). Group chunks by `path` (source file) for card display. |
| MEM-02 | Global search across all agent memories and conversations | FTS5 `chunks_fts` virtual table already exists in each memory DB. Use `MATCH` operator for full-text search. Query all 4 agent DBs and merge results. |
| OFFC-01 | Office view shows avatar for each of 7 agents at virtual workstations | Pure CSS/SVG layout. All 7 agents defined in `AGENTS` constant. Avatar illustrations can be inline SVG or static images. |
| OFFC-02 | Agent avatars reflect current status (working when active, idle when inactive) | Reuse heartbeat/lastSeen logic from `getAgentBoardData()` in agents queries. 5-minute idle threshold matches existing "active" status window. |
| VIZ-01 | Token usage displayed as area charts per agent via Recharts | `observability.db` `llm_calls` table has `agent_id`, `input_tokens`, `output_tokens`, `created_at`. Group by date + agent_id. Recharts AreaChart with gradient fills per agent. |
| VIZ-02 | Content pipeline displayed as bar chart by status | `content.db` currently 0-byte (no articles table yet). Chart must handle empty state gracefully. When populated, query `articles` table `GROUP BY status`. |
| VIZ-03 | Email volume displayed as line chart over time | `email.db` `email_conversations` table has `direction` and `created_at`. Currently 0 rows. Chart must handle empty state. When populated, group by date + direction. |
| VIZ-04 | Cron success/failure displayed as donut chart | Cron data from `~/.openclaw/cron/jobs.json` file (not database). 20 jobs total. Parse `state.lastStatus` for ok/error/null counts. Use Recharts PieChart with innerRadius for donut. |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | 2.15.4 | All chart types (Area, Bar, Line, Pie/Donut) | Already installed, shadcn chart wrapper exists |
| better-sqlite3 | 12.6.2 | Read memory SQLite databases | Already used for all other DB access |
| swr | 2.4.0 | Client-side data fetching with polling | Already configured with 30s refresh |
| next | 14.2.15 | App router, API routes | Existing framework |
| lucide-react | 0.475.0 | Icons for tabs, search, status badges | Already installed |
| date-fns | 3.6.0 | Date formatting for chart axes and timestamps | Already installed |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn chart.tsx | N/A | ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend | Wrap all Recharts components for consistent styling |
| tailwindcss-animate | 1.0.7 | Pulse animation for active status, skeleton loaders | Office view green pulse, loading states |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Recharts | Victory, Nivo | Recharts already installed with shadcn wrapper; no reason to switch |
| Per-agent SQLite opens | Single merged view | Per-agent DBs are separate files; must open each individually |
| SVG office layout | Canvas/WebGL | SVG is simpler, accessible, animatable with CSS -- right choice for static floorplan |

**Installation:**
```bash
# Nothing new to install -- all dependencies already present
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── app/
│   ├── memory/page.tsx            # Memory browser page
│   ├── office/page.tsx            # Office view page
│   ├── analytics/page.tsx         # Analytics/charts page
│   ├── api/
│   │   ├── memory/route.ts        # Memory chunks + search API
│   │   ├── office/route.ts        # Agent status for office view
│   │   └── analytics/
│   │       ├── tokens/route.ts    # Token time series
│   │       ├── pipeline/route.ts  # Content pipeline counts
│   │       ├── email/route.ts     # Email volume time series
│   │       └── crons/route.ts     # Cron success/failure counts
├── components/
│   ├── memory/
│   │   ├── memory-card.tsx        # Individual memory card (expandable)
│   │   └── memory-search.tsx      # Search bar with debounce
│   ├── office/
│   │   ├── office-floor.tsx       # SVG floorplan layout
│   │   └── agent-desk.tsx         # Individual desk + avatar + status
│   └── analytics/
│       ├── token-chart.tsx        # Area chart wrapper
│       ├── pipeline-chart.tsx     # Bar chart wrapper
│       ├── email-chart.tsx        # Line chart wrapper
│       └── cron-chart.tsx         # Donut chart wrapper
├── lib/
│   └── queries/
│       ├── memory.ts              # Memory DB queries (multi-DB)
│       └── analytics.ts           # Analytics aggregation queries
```

### Pattern 1: Multi-Database Memory Access
**What:** Open multiple per-agent SQLite files, query each, merge results
**When to use:** Memory page -- each agent has a separate `.sqlite` file

The memory backend stores data in `~/.openclaw/memory/{agent_id}.sqlite`. Unlike the 5 shared databases (coordination, observability, content, email, health) which are singletons in `db.ts`, memory databases are per-agent. Need a new access pattern.

```typescript
// Source: EC2 filesystem inspection 2026-02-21
import Database from "better-sqlite3";
import path from "path";

const MEMORY_DIR = "/home/ubuntu/.openclaw/memory";

// Agent IDs that have memory databases (verified on EC2)
const MEMORY_AGENTS = ["main", "landos", "ops", "rangeos"];

function getMemoryDb(agentId: string): Database.Database | null {
  const dbPath = path.join(MEMORY_DIR, `${agentId}.sqlite`);
  try {
    return new Database(dbPath, { readonly: true, fileMustExist: true });
  } catch {
    return null;
  }
}
```

**Key schema facts (verified):**
- Table: `chunks` -- id (TEXT PK), path (TEXT), source (TEXT), start_line (INT), end_line (INT), text (TEXT), updated_at (INT ms epoch)
- Table: `files` -- path (TEXT PK), source (TEXT), hash, mtime, size
- FTS: `chunks_fts` -- full-text index on `text` column, with unindexed id/path/source columns
- `updated_at` is Unix milliseconds (not ISO string)
- `path` values look like `memory/2026-02-12.md` (relative paths)
- `source` is always `"memory"` for agent memories

### Pattern 2: FTS5 Search Across Multiple DBs
**What:** Run FTS5 MATCH queries against each agent's chunks_fts, merge and sort results
**When to use:** MEM-02 global search

```typescript
// Source: Verified FTS5 working on EC2 2026-02-21
function searchMemory(query: string, agentFilter?: string) {
  const agents = agentFilter ? [agentFilter] : MEMORY_AGENTS;
  const results = [];

  for (const agentId of agents) {
    const db = getMemoryDb(agentId);
    if (!db) continue;
    try {
      const rows = db.prepare(`
        SELECT c.id, c.path, c.text, c.start_line, c.end_line, c.updated_at
        FROM chunks_fts f
        JOIN chunks c ON c.id = f.id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT 20
      `).all(query);
      // Add agent_id to each row
      results.push(...rows.map(r => ({ ...r, agent_id: agentId })));
    } finally {
      db.close();
    }
  }
  return results;
}
```

**FTS5 MATCH syntax notes:**
- Simple words: `MATCH 'email'` -- works
- Phrases: `MATCH '"email monitor"'` -- double-quoted phrase
- Boolean: `MATCH 'email AND calendar'` -- AND/OR/NOT
- The FTS index returns results ranked by relevance via `rank` column

### Pattern 3: Existing Page/API Pattern
**What:** Follow the exact pattern from `/agents` page
**When to use:** All three new pages

```
1. Query module in src/lib/queries/ (server-side SQLite access)
2. API route in src/app/api/ (calls query module, returns JSON)
3. Page component with useSWR hook (client-side data fetching)
4. FreshnessIndicator for staleness display
5. Skeleton loaders during isLoading
```

### Pattern 4: shadcn Chart Wrapper for Recharts
**What:** Use ChartContainer from chart.tsx instead of raw ResponsiveContainer
**When to use:** All 4 analytics charts

```typescript
// Source: Existing chart.tsx in codebase
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from "recharts";

const chartConfig = {
  main: { label: "Bob", color: "hsl(217, 91%, 60%)" },
  landos: { label: "Scout", color: "hsl(142, 71%, 45%)" },
  // ...per agent
};

function TokenChart({ data }) {
  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tickFormatter={formatDate} />
        <YAxis tickFormatter={formatTokens} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area type="monotone" dataKey="main" stackId="1" />
      </AreaChart>
    </ChartContainer>
  );
}
```

### Anti-Patterns to Avoid
- **Opening memory DBs globally:** Unlike the 5 shared DBs in `db.ts` (cached in Map), memory DBs should be opened per-request and closed. They're per-agent files and less frequently accessed.
- **Querying FTS with raw user input:** FTS5 MATCH syntax can throw on malformed queries. Always wrap in try/catch and sanitize (strip special FTS operators) or fall back to `LIKE` search.
- **Using `updated_at` directly:** Memory chunks store Unix milliseconds, but observability/coordination DBs store ISO strings. Must handle both formats.
- **Hardcoding 7 agents for memory:** Only 4 agents (main, landos, ops, rangeos) have memory databases. Quill, sage, ezra have no memory files. The memory tab list should only show agents that actually have data.
- **Blocking on content.db/email.db:** Both are currently empty (0-byte content.db, 0 rows in email.db). Charts MUST render meaningful empty states, not crash.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-text search | Custom text matching | FTS5 MATCH (already indexed) | FTS5 handles ranking, stemming, tokenization |
| Chart tooltips | Custom hover overlays | shadcn ChartTooltipContent | Already styled, handles edge cases |
| Responsive charts | Manual resize handlers | ChartContainer (wraps ResponsiveContainer) | Built into shadcn chart wrapper |
| Debounced search | setTimeout logic | useDeferredValue or simple useState + useEffect with timeout | Standard React pattern |
| Agent status logic | New heartbeat queries | Reuse getAgentBoardData pattern from agents queries | Same data source, same thresholds |
| Donut chart | Custom SVG arcs | Recharts PieChart with innerRadius | Handles label placement, tooltips, animations |

**Key insight:** The project already has all the building blocks. This phase is assembly, not invention. Every library needed is installed, every pattern is established, every data source is verified.

## Common Pitfalls

### Pitfall 1: Memory DB Connection Leaks
**What goes wrong:** Opening memory SQLite files per-request without closing them leads to file handle exhaustion
**Why it happens:** The existing `db.ts` caches connections in a Map (appropriate for long-lived shared DBs), but memory DBs are per-agent and accessed infrequently
**How to avoid:** Either cache memory DB connections in the same Map pattern (extending DbName union) or open/close per request. Recommendation: add them to the connection cache with a "memory-{agentId}" key pattern, since the same readonly+WAL+busy_timeout pattern applies.
**Warning signs:** "SQLITE_CANTOPEN" errors, "too many open files"

### Pitfall 2: FTS5 Query Injection
**What goes wrong:** User search input containing FTS5 operators (*, ^, NEAR, ") causes query syntax errors
**Why it happens:** FTS5 MATCH has its own query language; raw user input may contain reserved characters
**How to avoid:** Sanitize search input -- strip or escape FTS5 special characters, or wrap entire input in double quotes for phrase matching. Catch errors and fall back to `LIKE '%query%'` on chunks.text.
**Warning signs:** "fts5: syntax error" from SQLite

### Pitfall 3: Hydration Mismatches on Timestamps
**What goes wrong:** Server renders UTC timestamps, client renders local time, React hydration fails
**Why it happens:** Already solved in the project via RelativeTime component with useEffect-deferred rendering
**How to avoid:** Use the existing `RelativeTime` component for all timestamp displays. For chart axis labels, use date-fns `format()` with consistent formatting (no timezone-dependent display).
**Warning signs:** Console "Text content does not match" hydration warnings

### Pitfall 4: Empty Data Charts
**What goes wrong:** Recharts throws or renders blank when data array is empty
**Why it happens:** content.db is 0-byte (no articles table), email.db has 0 rows. These charts will receive empty arrays.
**How to avoid:** Check data length before rendering chart. Show a styled empty state ("No data yet") instead of an empty chart area. This is expected, not an error.
**Warning signs:** Blank chart areas, missing axes

### Pitfall 5: Memory Chunk Grouping
**What goes wrong:** Displaying raw chunks as individual cards creates confusing UX -- a single daily log file might produce 2-3 chunks
**Why it happens:** OpenClaw's memory system splits files into embedding-sized chunks (start_line/end_line ranges)
**How to avoid:** Group chunks by `path` for card display. Each card represents a file (e.g., "2026-02-12.md"), and expanding shows the full text (concatenating chunks for that path, ordered by start_line). The `files` table provides the canonical file list.
**Warning signs:** Same date appearing as multiple cards, confusing "partial" content previews

### Pitfall 6: Stacked Area Chart Data Shape
**What goes wrong:** Recharts stacked AreaChart expects data with all agents as columns in each row, not separate rows per agent
**Why it happens:** SQL query returns rows per agent per day, but Recharts needs pivoted data
**How to avoid:** Pivot the SQL results in JavaScript: `{ date: "2026-02-21", main: 177941, landos: 50802, ops: 61440, ... }`. Fill missing agents with 0 for each date.
**Warning signs:** Areas overlapping instead of stacking, missing agent series

## Code Examples

### Memory Chunks Query (Browsing)
```typescript
// Source: Verified schema + data on EC2 2026-02-21
interface MemoryChunk {
  id: string;
  path: string;         // "memory/2026-02-12.md"
  text: string;
  start_line: number;
  end_line: number;
  updated_at: number;   // Unix ms
  agent_id: string;     // Added during merge
}

interface MemoryFile {
  path: string;
  agent_id: string;
  agent_name: string;
  updated_at: number;   // Max of chunks
  preview: string;      // First ~200 chars of first chunk
  chunks: MemoryChunk[];
}

function getMemoryFiles(agentId?: string): MemoryFile[] {
  const agents = agentId ? [agentId] : MEMORY_AGENTS;
  const files: MemoryFile[] = [];

  for (const aid of agents) {
    const db = getMemoryDb(aid);
    if (!db) continue;
    try {
      const rows = db.prepare(`
        SELECT id, path, text, start_line, end_line, updated_at
        FROM chunks
        ORDER BY path DESC, start_line ASC
      `).all() as MemoryChunk[];

      // Group by path
      const byPath = new Map<string, MemoryChunk[]>();
      for (const row of rows) {
        const existing = byPath.get(row.path) || [];
        existing.push({ ...row, agent_id: aid });
        byPath.set(row.path, existing);
      }

      for (const [filePath, chunks] of byPath) {
        const fullText = chunks.map(c => c.text).join("\n");
        files.push({
          path: filePath,
          agent_id: aid,
          agent_name: AGENT_NAMES[aid],
          updated_at: Math.max(...chunks.map(c => c.updated_at)),
          preview: fullText.slice(0, 200),
          chunks,
        });
      }
    } finally {
      db.close();
    }
  }

  // Sort by most recent first
  return files.sort((a, b) => b.updated_at - a.updated_at);
}
```

### FTS5 Search with Sanitization
```typescript
// Source: FTS5 verified working on EC2 2026-02-21
function sanitizeFtsQuery(input: string): string {
  // Remove FTS5 special characters that could cause syntax errors
  return input.replace(/[*^"(){}[\]:]/g, "").trim();
}

function searchMemoryChunks(query: string, agentId?: string) {
  const sanitized = sanitizeFtsQuery(query);
  if (sanitized.length < 2) return [];

  const agents = agentId ? [agentId] : MEMORY_AGENTS;
  const results: Array<MemoryChunk & { snippet: string }> = [];

  for (const aid of agents) {
    const db = getMemoryDb(aid);
    if (!db) continue;
    try {
      const rows = db.prepare(`
        SELECT c.id, c.path, c.text, c.start_line, c.end_line, c.updated_at,
               snippet(chunks_fts, 0, '<mark>', '</mark>', '...', 40) as snippet
        FROM chunks_fts f
        JOIN chunks c ON c.id = f.id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT 30
      `).all(sanitized);

      results.push(...rows.map(r => ({ ...r, agent_id: aid })));
    } catch {
      // FTS query failed -- fall back to LIKE
      const rows = db.prepare(`
        SELECT id, path, text, start_line, end_line, updated_at
        FROM chunks WHERE text LIKE ?
        ORDER BY updated_at DESC LIMIT 30
      `).all(`%${sanitized}%`);
      results.push(...rows.map(r => ({ ...r, agent_id: aid, snippet: "" })));
    } finally {
      db.close();
    }
  }
  return results;
}
```

### Token Time Series Query (Area Chart)
```typescript
// Source: observability.db schema verified 2026-02-21
function getTokenTimeSeries(days: number = 7) {
  const db = getDb("observability");
  if (!db) return [];

  const rows = db.prepare(`
    SELECT date(created_at) as day,
           CASE WHEN agent_id IN ('main', 'bob') THEN 'main' ELSE agent_id END as agent,
           sum(input_tokens + output_tokens) as tokens
    FROM llm_calls
    WHERE created_at > datetime('now', ? || ' days')
    GROUP BY day, agent
    ORDER BY day ASC
  `).all(`-${days}`) as Array<{ day: string; agent: string; tokens: number }>;

  // Pivot to { date, main, landos, ops, rangeos, quill, ... }
  const byDay = new Map<string, Record<string, number>>();
  for (const row of rows) {
    const existing = byDay.get(row.day) || { date: row.day };
    existing[row.agent] = (existing[row.agent] || 0) + row.tokens;
    byDay.set(row.day, existing);
  }
  return Array.from(byDay.values());
}
```

### Cron Donut Data (from JSON file)
```typescript
// Source: Cron jobs.json structure verified 2026-02-21
function getCronDonutData() {
  const raw = fs.readFileSync("/home/ubuntu/.openclaw/cron/jobs.json", "utf-8");
  const { jobs } = JSON.parse(raw);

  let ok = 0, error = 0, neverRun = 0;
  for (const job of jobs) {
    const status = job.state?.lastStatus;
    if (status === "ok") ok++;
    else if (status === "error") error++;
    else neverRun++;
  }

  return [
    { name: "Success", value: ok, fill: "hsl(142, 71%, 45%)" },
    { name: "Error", value: error, fill: "hsl(0, 84%, 60%)" },
    { name: "Never Run", value: neverRun, fill: "hsl(240, 5%, 65%)" },
  ].filter(d => d.value > 0);
}
```

### Recharts Donut with shadcn Wrapper
```typescript
// Source: Context7 /recharts/recharts + existing chart.tsx
import { PieChart, Pie, Cell } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

const chartConfig = {
  success: { label: "Success", color: "hsl(142, 71%, 45%)" },
  error: { label: "Error", color: "hsl(0, 84%, 60%)" },
  neverRun: { label: "Never Run", color: "hsl(240, 5%, 65%)" },
};

function CronDonut({ data }) {
  return (
    <ChartContainer config={chartConfig} className="h-[250px] w-full">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Pie>
        <ChartTooltip content={<ChartTooltipContent />} />
      </PieChart>
    </ChartContainer>
  );
}
```

### Agent Color Palette for Charts
```typescript
// Recommended: Distinct hues for each agent, legible on dark background
export const AGENT_COLORS: Record<string, string> = {
  main: "hsl(217, 91%, 60%)",     // Blue (Bob)
  landos: "hsl(142, 71%, 45%)",   // Green (Scout)
  rangeos: "hsl(262, 83%, 58%)",  // Purple (Vector)
  ops: "hsl(25, 95%, 53%)",       // Orange (Sentinel)
  quill: "hsl(340, 82%, 52%)",    // Pink (Quill)
  sage: "hsl(48, 96%, 53%)",      // Yellow (Sage)
  ezra: "hsl(186, 72%, 45%)",     // Cyan (Ezra)
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recharts 1.x with class components | Recharts 2.x with function components | 2023 | All examples use function components |
| Raw ResponsiveContainer | shadcn ChartContainer wrapper | Already in project | Use wrapper for consistent theming |
| Convex real-time | SWR polling (30s) | Phase 29 | All data fetching uses SWR, no WebSocket |
| File-based memory search (existing `/api/search`) | FTS5 SQLite search | New for Phase 32 | FTS5 is faster and ranked; existing file-walk search is fallback |

**Note on existing search:** The `/api/search` route already exists and does file-system walking across `~/clawd/agents/*/memory/` directories with naive string matching. The new memory page search should use FTS5 for better relevance ranking. The existing `/api/search` can remain for global dashboard search.

## Open Questions

1. **Office Avatar Assets**
   - What we know: User wants "illustrated character avatars" with "unique cartoon/illustrated avatar per agent"
   - What's unclear: Where do the avatar images come from? Are these pre-made assets, AI-generated, or simple placeholder SVGs?
   - Recommendation: Start with simple SVG placeholder avatars (colored circles with initials or simple geometric characters). The user can replace with illustrated assets later. This prevents the implementation from blocking on asset creation.

2. **Office Activity Badge Content**
   - What we know: "Small badge shows current task type (e.g., 'writing', 'researching') based on recent heartbeat/action data"
   - What's unclear: The `agent_activity` table has `activity_type` values like "coordination", "cron", "heartbeat", "session". These are system-level types, not human-friendly task descriptions. The `summary` column has more descriptive text.
   - Recommendation: Use `activity_type` for the badge with friendly labels: cron -> "Running cron", coordination -> "Coordinating", heartbeat -> "Monitoring", session -> "In session". If no recent activity, show "Idle".

3. **Memory Chunk Display Granularity**
   - What we know: Chunks are fragments of files (e.g., lines 1-34 of a daily log). A single file might have 1-3 chunks.
   - What's unclear: Should the card show the full reconstituted file content or individual chunks?
   - Recommendation: Group by `path`, show file-level cards. Card preview shows first ~150 chars. Expand reveals full text (all chunks concatenated by start_line). This matches the "Notion database view" feel the user wants.

## Sources

### Primary (HIGH confidence)
- EC2 filesystem inspection -- `~/.openclaw/memory/` directory, per-agent `.sqlite` files, schema verified
- EC2 SQLite queries -- chunks table data, FTS5 MATCH verified working, counts per agent (main:8, landos:20, ops:34, rangeos:30 chunks)
- Context7 `/recharts/recharts` -- AreaChart gradient fills, PieChart donut, LineChart tooltips, XAxis formatting
- Mission Control codebase inspection -- all existing patterns (db.ts, queries/, API routes, page components, chart.tsx)

### Secondary (MEDIUM confidence)
- Cron jobs.json structure -- 20 jobs, state.lastStatus verified (19 ok, 0 error, 1 never run)
- Observability.db token data -- 2,331 llm_calls across 5 agents, time series shape verified

### Tertiary (LOW confidence)
- None -- all findings verified against actual EC2 data

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use
- Architecture: HIGH -- following exact existing patterns from agents/dashboard pages
- Memory schema: HIGH -- verified via direct SQLite queries on EC2
- Chart implementation: HIGH -- Recharts patterns verified via Context7 + existing chart.tsx wrapper
- Office view: MEDIUM -- CSS/SVG layout is well-understood, but avatar assets are an open question
- Pitfalls: HIGH -- all derived from actual data inspection (empty DBs, FTS5 syntax, chunk grouping)

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable -- no external dependencies changing)
