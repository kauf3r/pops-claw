# Phase 40: YOLO Dashboard - Research

**Researched:** 2026-02-24
**Domain:** Next.js 14 page + API route + better-sqlite3 (Mission Control extension)
**Confidence:** HIGH

## Summary

This phase adds a `/yolo` page to the existing Mission Control Next.js 14 app. All patterns are already established in the codebase: page layout (agents, content), card components (AgentCard), badge variants (success/warning/error/secondary), database access (better-sqlite3 readonly via `getDb`), SWR auto-refresh (30s global config), and navbar links. The work is a straightforward application of existing conventions to a new data source (yolo.db).

The only new piece is registering yolo.db in `db-paths.ts` (currently 5 databases, this becomes the 6th) and writing a query function in `src/lib/queries/yolo.ts`. The page itself follows the agents page pattern: SWR fetch, loading skeletons, card grid, status-based styling.

**Primary recommendation:** Follow the agents page pattern exactly. Register yolo.db in db-paths.ts, create a query module, API route, and page component with card grid + filter bar. No new dependencies needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Card-based grid layout matching existing Mission Control patterns (shadcn Card component)
- Each card shows: build name, date, status badge (color-coded), self-score (1-5 as filled/empty dots or stars), description snippet, tech stack as small tags, duration, lines of code
- Left border accent per status, matching AgentCard pattern: success=emerald, partial=amber, failed=rose, building/testing=blue, idea=secondary
- Status badge uses existing Badge variants: success, warning, error, secondary
- Cards sorted newest-first by date (default)
- Standard Mission Control layout: `min-h-screen px-6 py-10`, `max-w-7xl mx-auto`
- Filter bar at top with pill-style buttons: All / Success / Partial / Failed (active state uses `bg-secondary text-foreground`)
- Responsive grid: 1 column mobile, 2 columns md, 3 columns lg
- Add "YOLO" to NavBar links array (with Zap or Rocket icon from lucide-react)
- Status color mapping: success=emerald, partial=amber, failed=rose, building/testing=blue, idea=secondary
- SWR with global 30s refreshInterval (matches existing config, satisfies SC-3)
- API route at `/api/yolo/builds` using better-sqlite3 readonly against yolo.db
- Register yolo.db path in db-paths.ts pointing to `~/clawd/yolo-dev/yolo.db`
- Loading: card skeleton placeholders (3 gray shimmer cards)
- Empty: centered message "No builds yet" with muted text
- Description truncated to 2 lines on card, no expand/detail view
- build_log and error_log NOT displayed

### Claude's Discretion
- Exact card spacing and typography within Mission Control conventions
- Skeleton animation style
- Icon choice for navbar (Zap, Rocket, or similar)
- Whether to show duration as "Xm Ys" or "X min"
- Score visualization (dots, stars, or numeric badge)

### Deferred Ideas (OUT OF SCOPE)
- Build detail/expand view with full logs -- future phase
- Search by name or tech stack -- future phase
- Build comparison (side by side) -- future phase
- Triggering new builds from the dashboard -- separate capability
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Mission Control /yolo page displays build history as cards with status badges, self-scores, descriptions, and tech stack -- newest first, filterable by status | All patterns verified in codebase: agents page layout, AgentCard border-accent, Badge variants, SWR config, db-paths registration, better-sqlite3 query pattern |
</phase_requirements>

## Standard Stack

### Core (already installed -- zero new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14.2.15 | App router, page + API route | Already running Mission Control |
| better-sqlite3 | ^12.6.2 | Readonly access to yolo.db | Used by all 5 existing databases |
| SWR | ^2.4.0 | Client-side data fetching + 30s auto-refresh | Global config in providers.tsx |
| lucide-react | ^0.475.0 | Navbar icon (Zap/Rocket) | Already used for Brain, Building2, BarChart3 |
| class-variance-authority | ^0.7.1 | Badge variant styling | Powers existing Badge component |
| date-fns | ^3.6.0 | Date formatting (if needed) | Already installed |
| Tailwind CSS | (config in project) | All styling | Standard throughout Mission Control |

### Supporting (already in codebase -- reuse, don't create)
| Component | Path | Purpose |
|-----------|------|---------|
| `Card`, `CardContent` | `src/components/ui/card.tsx` | Card wrapper with rounded-xl border |
| `Badge` | `src/components/ui/badge.tsx` | Status badges (success/warning/error/secondary variants) |
| `cn()` | `src/lib/utils.ts` | Tailwind class merging |
| `FreshnessIndicator` | `src/components/dashboard/freshness-indicator.tsx` | "Updated Xs ago" timer |
| `getDb()` | `src/lib/db.ts` | Database connection factory (readonly, WAL, cached) |
| `DB_PATHS` | `src/lib/db-paths.ts` | Database path registry |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pill-style filter buttons | shadcn Tabs component | Tabs add a dependency and different styling; pill buttons with `bg-secondary` match the CONTEXT.md spec exactly and are simpler |
| Custom score component | Numeric badge (e.g., "4/5") | Stars/dots require more markup; a compact numeric badge is simpler and equally scannable |

**Installation:** None required -- all dependencies already installed.

## Architecture Patterns

### File Structure (new files only)
```
src/
├── app/
│   ├── yolo/
│   │   └── page.tsx              # /yolo page (client component)
│   └── api/
│       └── yolo/
│           └── builds/
│               └── route.ts      # GET /api/yolo/builds
├── components/
│   └── yolo/
│       └── build-card.tsx        # YoloBuildCard component
└── lib/
    ├── db-paths.ts               # MODIFY: add "yolo" entry
    ├── db.ts                     # NO CHANGE (getDb already generic)
    └── queries/
        └── yolo.ts               # getYoloBuilds() query function
```

### Pattern 1: Database Registration
**What:** Add yolo.db to the existing `DB_PATHS` registry so `getDb("yolo")` works.
**How:** Add `"yolo"` to the `DB_NAMES` tuple and `DB_PATHS` record in `db-paths.ts`.

```typescript
// In db-paths.ts -- add "yolo" to existing pattern
export const DB_NAMES = [
  "coordination",
  "observability",
  "content",
  "email",
  "health",
  "yolo",      // NEW
] as const;

export const DB_PATHS: Record<DbName, string> = {
  // ... existing 5 ...
  yolo: "/home/ubuntu/clawd/yolo-dev/yolo.db",
};

export const DB_LABELS: Record<DbName, string> = {
  // ... existing 5 ...
  yolo: "YOLO Builds",
};
```
**Confidence:** HIGH -- verified exact pattern from `src/lib/db-paths.ts` on EC2.

### Pattern 2: Query Module
**What:** A typed query function that reads builds from yolo.db and returns them sorted newest-first.
**How:** Follow the `agents.ts` query pattern: import `getDb`, define TypeScript interfaces, write SQL, map rows to typed objects.

```typescript
// src/lib/queries/yolo.ts
import { getDb } from "@/lib/db";

export interface YoloBuild {
  id: number;
  date: string;
  slug: string;
  name: string;
  description: string | null;
  status: "idea" | "building" | "testing" | "success" | "partial" | "failed";
  techStack: string[];       // parsed from comma-separated string
  linesOfCode: number | null;
  filesCreated: number | null;
  selfScore: number | null;  // 1-5
  startedAt: string | null;
  completedAt: string | null;
  durationSeconds: number | null;
}

export interface YoloBuildSummary {
  builds: YoloBuild[];
  counts: { total: number; success: number; partial: number; failed: number };
}

export function getYoloBuilds(): YoloBuildSummary {
  const db = getDb("yolo");
  if (!db) return { builds: [], counts: { total: 0, success: 0, partial: 0, failed: 0 } };

  const rows = db.prepare(`
    SELECT id, date, slug, name, description, status,
           tech_stack, lines_of_code, files_created,
           self_score, started_at, completed_at, duration_seconds
    FROM builds
    ORDER BY date DESC, id DESC
  `).all() as Array<{
    id: number; date: string; slug: string; name: string;
    description: string | null; status: string; tech_stack: string | null;
    lines_of_code: number | null; files_created: number | null;
    self_score: number | null; started_at: string | null;
    completed_at: string | null; duration_seconds: number | null;
  }>;

  const builds: YoloBuild[] = rows.map(r => ({
    id: r.id,
    date: r.date,
    slug: r.slug,
    name: r.name,
    description: r.description,
    status: r.status as YoloBuild["status"],
    techStack: r.tech_stack ? r.tech_stack.split(",").map(s => s.trim()) : [],
    linesOfCode: r.lines_of_code,
    filesCreated: r.files_created,
    selfScore: r.self_score,
    startedAt: r.started_at,
    completedAt: r.completed_at,
    durationSeconds: r.duration_seconds,
  }));

  // Status counts for filter badges
  const counts = {
    total: builds.length,
    success: builds.filter(b => b.status === "success").length,
    partial: builds.filter(b => b.status === "partial").length,
    failed: builds.filter(b => b.status === "failed").length,
  };

  return { builds, counts };
}
```
**Confidence:** HIGH -- directly mirrors `agents.ts` pattern verified on EC2.

### Pattern 3: API Route
**What:** `GET /api/yolo/builds` returns JSON from the query module.
**How:** Follow the `api/agents/route.ts` pattern exactly.

```typescript
// src/app/api/yolo/builds/route.ts
import { NextResponse } from "next/server";
import { getYoloBuilds } from "@/lib/queries/yolo";

export const dynamic = "force-dynamic";

export function GET() {
  try {
    return NextResponse.json(getYoloBuilds());
  } catch (error) {
    return NextResponse.json(
      { builds: [], counts: { total: 0, success: 0, partial: 0, failed: 0 }, error: String(error) },
      { status: 500 }
    );
  }
}
```
**Confidence:** HIGH -- identical pattern to existing API routes.

### Pattern 4: Card Component with Status Border
**What:** `YoloBuildCard` using Card + left border accent + Badge for status.
**How:** Follow `AgentCard` pattern: `border-l-4` + status color map.

```typescript
// Status border colors (matching AgentCard pattern)
const STATUS_BORDER: Record<string, string> = {
  success: "border-l-emerald-500",
  partial: "border-l-amber-500",
  failed: "border-l-rose-500",
  building: "border-l-blue-500",
  testing: "border-l-blue-500",
  idea: "border-l-secondary",
};

// Badge variant mapping
const STATUS_BADGE: Record<string, "success" | "warning" | "error" | "secondary" | "default"> = {
  success: "success",
  partial: "warning",
  failed: "error",
  building: "default",
  testing: "default",
  idea: "secondary",
};
```
**Confidence:** HIGH -- verified Badge variants exist (success/warning/error/secondary/default/outline) in `badge.tsx`.

### Pattern 5: Client-Side Filtering
**What:** Filter bar with pill buttons that filter the builds array client-side.
**How:** `useState` for active filter, filter `data.builds` before mapping to cards. All data fetched in one SWR call, filtering is instant.

```typescript
const [filter, setFilter] = useState<"all" | "success" | "partial" | "failed">("all");
const filtered = filter === "all" ? builds : builds.filter(b => b.status === filter);
```
**Confidence:** HIGH -- standard React pattern, no library needed.

### Pattern 6: NavBar Addition
**What:** Add "YOLO" link to navbar.
**How:** Add entry to `links` array in `NavBar.tsx`.

```typescript
// In NavBar.tsx links array -- add after Calendar
{ href: "/yolo", label: "YOLO", icon: Zap },
```

Import `Zap` from lucide-react (already imported: `Brain`, `Building2`, `BarChart3`).

**Confidence:** HIGH -- verified NavBar.tsx structure.

### Anti-Patterns to Avoid
- **Server-side filtering via query params:** Don't add ?status=X to the API. With <100 builds per year, fetch all and filter client-side. Simpler, fewer API routes, instant filter switching.
- **Creating a new DB helper for yolo.db:** Don't create a separate `getYoloDb()`. Register in `db-paths.ts` and use `getDb("yolo")` like every other database.
- **Using `useEffect` for data fetching:** Don't use raw fetch + useEffect. SWR is the established pattern with global 30s refresh config.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database connection | New sqlite3 import | `getDb("yolo")` via db-paths | Connection caching, readonly, WAL pragma, busy_timeout -- all handled |
| Status badges | Custom colored spans | `Badge` component with variant prop | success/warning/error/secondary variants already defined |
| Card layout | Custom div styling | `Card` + `CardContent` components | Consistent rounded-xl border, bg-card, shadow |
| Auto-refresh | setInterval + fetch | SWR with global 30s refreshInterval | Deduping, error handling, revalidation all built in |
| Class merging | String concatenation | `cn()` utility | Handles Tailwind class conflicts correctly |

**Key insight:** This entire feature is assembled from existing primitives. Zero new libraries, zero new utility functions. The only new code is the yolo-specific query, API route, page, and card component.

## Common Pitfalls

### Pitfall 1: Forgetting `export const dynamic = "force-dynamic"` on API route
**What goes wrong:** Next.js 14 statically renders API routes at build time by default. Without `force-dynamic`, the route returns stale data frozen at build time.
**Why it happens:** Next.js aggressive static optimization.
**How to avoid:** Always include `export const dynamic = "force-dynamic"` in API route files. Already established pattern in existing routes.
**Warning signs:** Data never updates despite SWR polling.

### Pitfall 2: tech_stack is comma-separated string, not JSON array
**What goes wrong:** Treating `tech_stack` as a JSON array and calling `JSON.parse()` will throw.
**Why it happens:** yolo.db schema defines `tech_stack TEXT` and Bob writes values like `"python,html,css,javascript"`.
**How to avoid:** Split on comma: `tech_stack.split(",").map(s => s.trim())`. Handle null/empty case.
**Warning signs:** Runtime error on first card render.

### Pitfall 3: Hydration mismatch with dates
**What goes wrong:** Server renders UTC date, client renders PT date -- React hydration error.
**Why it happens:** Server and client timezone differ. Known issue documented in MEMORY.md.
**How to avoid:** Use the established pattern: defer `new Date()` formatting to client-side via `useEffect`, or use relative-time components that handle this. Since /yolo page is `"use client"`, this is less of a concern -- but date formatting should still use a consistent approach.
**Warning signs:** Console hydration warnings about text content mismatch.

### Pitfall 4: yolo.db path not resolving in development vs production
**What goes wrong:** `getDb("yolo")` returns null because the file doesn't exist at the hard-coded path.
**Why it happens:** Mission Control runs on EC2 only (no local dev), so the path `/home/ubuntu/clawd/yolo-dev/yolo.db` is correct. But if someone runs `next dev` locally, it fails gracefully (returns null, empty state shows).
**How to avoid:** The `getDb()` function already returns null gracefully for missing files. The page's empty state handles this.
**Warning signs:** "No builds yet" message when builds exist.

### Pitfall 5: `border-l-secondary` not resolving as expected
**What goes wrong:** Tailwind `border-l-secondary` may not generate the expected color because `secondary` is a CSS variable, not a Tailwind color.
**Why it happens:** Tailwind theme colors via CSS variables need `border-l-[hsl(var(--secondary))]` syntax, not direct class.
**How to avoid:** Use `border-l-border` or `border-l-muted` for the `idea` status, which are established Tailwind theme utilities. Or use `border-l-zinc-600` directly. Check existing codebase for how AgentCard handles non-standard border colors.
**Warning signs:** Idea builds have no visible left border accent.

### Pitfall 6: Mission Control service restart after file changes
**What goes wrong:** Changes deployed to EC2 but not visible because Next.js is running the old build.
**Why it happens:** Mission Control runs as systemd service with `next start` (production mode). File changes require `next build` then service restart.
**How to avoid:** After deploying changes: `cd ~/clawd/mission-control && npm run build && systemctl --user restart mission-control`
**Warning signs:** Old page renders despite confirmed file changes.

## Code Examples

### Duration Formatting Helper
```typescript
// Recommendation: "Xm Ys" format for compact display
export function formatDuration(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}
```

### Score Visualization (Compact Numeric Badge)
```typescript
// Recommendation: numeric badge "4/5" -- compact, scannable
{build.selfScore != null && (
  <span className="text-xs font-medium text-muted-foreground">
    {build.selfScore}/5
  </span>
)}
```
Alternative (filled dots):
```typescript
// Dots: ●●●●○ for 4/5
{build.selfScore != null && (
  <span className="text-xs tracking-wider">
    {"●".repeat(build.selfScore)}{"○".repeat(5 - build.selfScore)}
  </span>
)}
```

### Filter Bar (Pill Buttons)
```typescript
const FILTERS = [
  { key: "all", label: "All" },
  { key: "success", label: "Success" },
  { key: "partial", label: "Partial" },
  { key: "failed", label: "Failed" },
] as const;

<div className="flex items-center gap-2">
  {FILTERS.map(f => (
    <button
      key={f.key}
      onClick={() => setFilter(f.key)}
      className={cn(
        "rounded-full px-3 py-1 text-sm font-medium transition-colors",
        filter === f.key
          ? "bg-secondary text-foreground"
          : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
      )}
    >
      {f.label}
      {f.key !== "all" && (
        <span className="ml-1.5 text-xs text-muted-foreground">
          {counts[f.key]}
        </span>
      )}
    </button>
  ))}
</div>
```

### Tech Stack Tags
```typescript
// Comma-separated string → pill badges
<div className="flex flex-wrap gap-1">
  {build.techStack.map(tech => (
    <Badge key={tech} variant="secondary" className="text-[10px] px-1.5 py-0">
      {tech}
    </Badge>
  ))}
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pages Router API routes | App Router route handlers (`route.ts`) | Next.js 13+ | All MC routes use App Router pattern |
| `fetch` + `useEffect` | SWR with global config | Project inception | Auto-refresh, deduping, error handling built in |
| Manual DB connections | Centralized `getDb()` with path registry | Phase 29+ | Single pattern for all 5 (now 6) databases |

**Deprecated/outdated:**
- None relevant. Mission Control's stack is stable and current.

## Open Questions

1. **Which icon for YOLO in navbar?**
   - What we know: User suggested Zap or Rocket from lucide-react. Both are available.
   - Recommendation: Use `Zap` -- it conveys energy/speed and is visually lighter than Rocket. Marked as Claude's discretion, so choose at implementation time.

2. **Score visualization style?**
   - What we know: User left this to Claude's discretion. Options: numeric badge ("4/5"), filled dots ("●●●●○"), or star icons.
   - Recommendation: Numeric badge "4/5" -- most compact, zero additional markup, scannable. Dots are a close second if more visual flair is desired.

3. **Duration format?**
   - What we know: User left this to Claude's discretion. Options: "30m 0s" or "30 min".
   - Recommendation: "Xm Ys" for builds under an hour (covers all current builds since they're <30min). Compact and precise.

## Sources

### Primary (HIGH confidence)
- EC2 filesystem: `~/clawd/mission-control/src/` -- all patterns verified by reading actual source files
- EC2 yolo.db: `sqlite3 .schema builds` -- confirmed table schema and data format
- EC2 yolo.db data: 1 build record (id=4, Chronicle, success, score 4, tech_stack="python,html,css,javascript")

### Secondary (MEDIUM confidence)
- Next.js 14 App Router conventions (force-dynamic, route handlers) -- verified against existing codebase usage

### Tertiary (LOW confidence)
- None. All findings verified against live codebase.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all existing
- Architecture: HIGH -- every pattern verified against existing MC source code
- Pitfalls: HIGH -- drawn from project history (MEMORY.md hydration fix) and verified code patterns

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable stack, no expected changes)
