# Phase 42: CLI Tools Dashboard - Research

**Researched:** 2026-02-26
**Domain:** Next.js dashboard page + EC2 shell health-check script + SQLite/JSON data source
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool Inventory**
- EC2 tools only (no Mac-side tools) — this is Bob's operations dashboard
- Four sections: CLI Tools, Plugins, Scripts, Scheduled Jobs
- CLI Tools: openclaw, gog, bd, node/npm, whisper
- Plugins: camofox-browser, secureclaw (separate section, not mixed with CLIs)
- Scripts: prune-sessions.sh, process-voice-notes.py, collect_verified.sh (own section)
- Cron jobs: separate section with last-run and next-run times

**Health Indicators**
- CLI tools: version + reachability — green (responds + current), yellow (responds + outdated >7 days), red (not responding or missing)
- Cron jobs: last-run recency — green (ran within expected interval), yellow (missed 1 run), red (missed 2+ runs or never ran)
- Plugins: enabled + version — green (directory exists + in openclaw.json), yellow (exists but not in config), red (in config but directory missing)
- Data source: cached via periodic script on EC2 (every 5-10 min), writes to DB/JSON — dashboard reads cached data, no live SSH

**Layout & Grouping**
- Compact table rows within each section (not cards) — ops dashboard feel like a status page
- Section order: CLI Tools → Plugins → Scripts → Scheduled Jobs (priority order)
- Health summary banner at top: total tools count + green/yellow/red breakdown
- Sections collapsible, all expanded by default

**Quick Actions**
- Copy-paste commands (clipboard icon per row) — not executable buttons
- 1 primary diagnostic command shown per tool, expandable to 2-3 more
- Cron quick action: copy `openclaw cron trigger <id>` for manual firing
- Manual refresh icon next to "Last checked" timestamp — triggers health-check script via API, SWR auto-refreshes

### Claude's Discretion
- Exact health-check script implementation (shell script vs Python)
- DB schema for cached health data (tools.db vs JSON file)
- Refresh interval for periodic script (5 vs 10 min)
- Table column widths and responsive breakpoints
- Clipboard toast/feedback UX

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TOOLS-01 | Mission Control /tools page displaying CLI tool versions, health status, and quick-action shortcuts for bd, openclaw, scripts, and other project CLI tools | Full architecture documented below: health-check script writes JSON, API route reads it, Next.js page with SWR displays it with table rows, badge variants, and clipboard actions |
</phase_requirements>

## Summary

Phase 42 adds a `/tools` page to the existing Mission Control Next.js app (Next.js 14.2.15, SWR 2.4, better-sqlite3 12.6.2). The page reads pre-cached health data written by a periodic shell script running on EC2, following the same pattern as the existing `/api/cron` route (which already reads `~/.openclaw/cron/jobs.json` directly from the filesystem). No new database is needed — a JSON file at a fixed path is sufficient and simpler.

The Scheduled Jobs section is nearly free: the cron route already reads `jobs.json`, which contains live `state.lastRunAtMs` and `state.lastStatus` per job. All 24 cron jobs have real `state` data. The new `/api/tools` route reads the cached tools-health JSON (written by the health-check script) plus the existing `jobs.json` for cron section data. The manual refresh endpoint triggers the health-check script via `child_process.execFile` then SWR revalidates.

The UI follows established patterns: `use client` page with `useSWR`, compact `<Table>` rows (the `table.tsx` component already exists), existing `Badge` variants (success/warning/error/secondary), clipboard via the browser `navigator.clipboard` API, and collapsible sections using `useState`. The `FreshnessIndicator` component can be reused directly.

**Primary recommendation:** Use a JSON file (not a new DB) for health cache. Shell script for health checks. Re-use all existing UI components — Table, Badge, FreshnessIndicator, Card. The cron section pulls from the existing cron API or re-reads jobs.json directly.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14.2.15 | App framework, API routes | Already in use |
| SWR | 2.4.0 | Data fetching, auto-refresh | Already configured globally with `refreshInterval: 30000` |
| better-sqlite3 | 12.6.2 | DB access (not needed for tools) | Already in use for other pages |
| Tailwind CSS | 3.4.10 | Styling | Already in use |
| lucide-react | 0.475.0 | Icons (clipboard, refresh, chevron) | Already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `child_process.execFile` | Node built-in | Trigger health-check script from API | Refresh endpoint only |
| `fs/promises.readFile` | Node built-in | Read cached JSON | Same pattern as `/api/cron` |
| `navigator.clipboard` | Browser API | Copy to clipboard | Clipboard quick actions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON file cache | tools.db SQLite | JSON is simpler, no schema migration, sufficient for small inventory |
| Shell script | Python script | Shell is faster to write for version checks; Python needed only if complex parsing required |
| Cron section via new query | Re-use `/api/cron` data | Calling existing `/api/cron` from the page avoids duplication |

**Installation:** No new packages needed — all dependencies already in `package.json`.

## Architecture Patterns

### Recommended Project Structure
```
~/clawd/mission-control/src/
├── app/
│   ├── tools/
│   │   └── page.tsx                   # "use client", useSWR("/api/tools")
│   └── api/
│       ├── tools/
│       │   └── route.ts               # GET: reads tools-health.json + jobs.json
│       └── tools/refresh/
│           └── route.ts               # POST: runs health-check script, returns 200
└── components/
    └── tools/
        └── tools-table.tsx            # Reusable table rows per section
~/scripts/
└── tools-health-check.sh             # Runs every 5-10 min, writes ~/clawd/tools-health.json
```

### Pattern 1: Filesystem JSON cache (already established)
**What:** Health-check script writes a JSON file. API route reads it with `readFile`. No subprocess on read path.
**When to use:** Any data that's expensive to compute live (version checks, file existence checks) but can tolerate 5-10 min staleness.
**Example:**
```typescript
// Mirrors existing /api/cron/route.ts pattern exactly
import { readFile } from "fs/promises";

const TOOLS_HEALTH_PATH = "/home/ubuntu/clawd/tools-health.json";
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  try {
    const raw = await readFile(TOOLS_HEALTH_PATH, "utf-8");
    return NextResponse.json(JSON.parse(raw));
  } catch (error) {
    return NextResponse.json({ tools: [], lastChecked: null, error: String(error) }, { status: 500 });
  }
}
```

### Pattern 2: SWR with manual mutate for refresh
**What:** The "refresh" icon calls `POST /api/tools/refresh`, which runs the script synchronously (or with a short timeout), then the page calls `mutate()` to force SWR re-fetch.
**When to use:** Any "check now" action where the user expects near-immediate feedback.
**Example:**
```typescript
// In page.tsx
const { data, mutate } = useSWR<ToolsHealth>("/api/tools");

async function handleRefresh() {
  await fetch("/api/tools/refresh", { method: "POST" });
  mutate(); // force re-fetch
}
```

### Pattern 3: Collapsible sections with useState
**What:** Each section header has a toggle that collapses the table body. All start expanded.
**When to use:** Multi-section ops dashboards where users may want to focus on one section.
**Example:**
```typescript
const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
// Toggle: setCollapsed(c => ({ ...c, [section]: !c[section] }))
// Render: !collapsed[section] && <TableBody>...</TableBody>
```

### Pattern 4: Clipboard copy with toast feedback
**What:** Clicking the clipboard icon runs `navigator.clipboard.writeText(cmd)`. A brief local state flag shows a checkmark for 2 seconds.
**When to use:** Copy-paste quick actions.
**Example:**
```typescript
const [copied, setCopied] = useState<string | null>(null);
function copyCmd(id: string, cmd: string) {
  navigator.clipboard.writeText(cmd);
  setCopied(id);
  setTimeout(() => setCopied(null), 2000);
}
// In row: {copied === row.id ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Clipboard ... />}
```

### Health-Check Shell Script Pattern
**What:** A bash script that queries each CLI tool, checks filesystem paths, and writes structured JSON.
**Example skeleton:**
```bash
#!/bin/bash
# ~/scripts/tools-health-check.sh
# Run via cron: */5 * * * * /home/ubuntu/scripts/tools-health-check.sh

set -euo pipefail
OUT="/home/ubuntu/clawd/tools-health.json"
LAST_CHECKED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# CLI Tools section
OPENCLAW_VER=$(/home/ubuntu/.npm-global/bin/openclaw --version 2>/dev/null | head -1 || echo "error")
GOG_VER=$(gog --version 2>/dev/null | head -1 || echo "error")
NODE_VER=$(node --version 2>/dev/null || echo "error")
WHISPER_VER=$(/home/ubuntu/whisper-venv/bin/whisper --version 2>/dev/null | head -1 || echo "error")
# bd not installed on EC2 (command not found) -- always red, show "not installed"

# Plugins section: check directory existence + openclaw.json entries
CAMOFOX_DIR_EXISTS=$(test -d /home/ubuntu/.openclaw/extensions/camofox-browser && echo true || echo false)
SECURECLAW_DIR_EXISTS=$(test -d /home/ubuntu/.openclaw/plugins/secureclaw && echo true || echo false)

# Scripts section: check file existence + last-modified time
PRUNE_MTIME=$(stat -c %Y /home/ubuntu/scripts/prune-sessions.sh 2>/dev/null || echo 0)
VOICENOTES_MTIME=$(stat -c %Y /home/ubuntu/scripts/process-voice-notes.py 2>/dev/null || echo 0)
CLAWDSTRIKE_MTIME=$(stat -c %Y /home/ubuntu/.openclaw/skills/clawdstrike/scripts/collect_verified.sh 2>/dev/null || echo 0)

python3 -c "
import json, sys, time
now = time.time()

def days_since(mtime):
    return (now - int(mtime)) / 86400 if int(mtime) > 0 else None

data = {
  'lastChecked': '$LAST_CHECKED',
  'cli': [
    {'id': 'openclaw', 'name': 'openclaw', 'version': '$OPENCLAW_VER', 'path': '/home/ubuntu/.npm-global/bin/openclaw', 'status': 'green' if '$OPENCLAW_VER' != 'error' else 'red', 'commands': ['openclaw --version', 'systemctl --user status openclaw-gateway', 'openclaw doctor']},
    {'id': 'gog', 'name': 'gog', 'version': '$GOG_VER', 'path': '/usr/local/bin/gog', 'status': 'green' if '$GOG_VER' != 'error' else 'red', 'commands': ['gog --version', 'gog auth list', 'gog health']},
    {'id': 'node', 'name': 'node/npm', 'version': '$NODE_VER', 'path': '/usr/bin/node', 'status': 'green' if '$NODE_VER' != 'error' else 'red', 'commands': ['node --version', 'npm --version']},
    {'id': 'whisper', 'name': 'whisper', 'version': '$WHISPER_VER', 'path': '/home/ubuntu/whisper-venv/bin/whisper', 'status': 'yellow' if 'usage:' in '$WHISPER_VER' else 'green' if '$WHISPER_VER' != 'error' else 'red', 'commands': ['whisper --version', 'ls /home/ubuntu/whisper-venv/']},
    {'id': 'bd', 'name': 'bd', 'version': 'not installed', 'path': 'N/A', 'status': 'red', 'commands': []},
  ],
  'plugins': [
    {'id': 'camofox', 'name': 'camofox-browser', 'version': '1.0.13', 'status': 'green' if $CAMOFOX_DIR_EXISTS else 'red', 'dirExists': $CAMOFOX_DIR_EXISTS, 'inConfig': True, 'commands': ['openclaw plugins list', 'ls ~/.openclaw/extensions/camofox-browser/']},
    {'id': 'secureclaw', 'name': 'secureclaw', 'version': '2.1.0', 'status': 'green' if $SECURECLAW_DIR_EXISTS else 'red', 'dirExists': $SECURECLAW_DIR_EXISTS, 'inConfig': True, 'commands': ['ls ~/.openclaw/plugins/secureclaw/']},
  ],
  'scripts': [
    {'id': 'prune-sessions', 'name': 'prune-sessions.sh', 'path': '/home/ubuntu/scripts/prune-sessions.sh', 'status': 'green' if $PRUNE_MTIME else 'red', 'lastModifiedDays': days_since('$PRUNE_MTIME'), 'commands': ['bash ~/scripts/prune-sessions.sh', 'cat ~/scripts/prune-sessions.log | tail -20']},
    {'id': 'voice-notes', 'name': 'process-voice-notes.py', 'path': '/home/ubuntu/scripts/process-voice-notes.py', 'status': 'green' if $VOICENOTES_MTIME else 'red', 'lastModifiedDays': days_since('$VOICENOTES_MTIME'), 'commands': ['python3 ~/scripts/process-voice-notes.py', 'cat ~/scripts/voice-notes.log | tail -20']},
    {'id': 'clawdstrike', 'name': 'collect_verified.sh', 'path': '/home/ubuntu/.openclaw/skills/clawdstrike/scripts/collect_verified.sh', 'status': 'green' if $CLAWDSTRIKE_MTIME else 'red', 'lastModifiedDays': days_since('$CLAWDSTRIKE_MTIME'), 'commands': ['bash ~/.openclaw/skills/clawdstrike/scripts/collect_verified.sh']},
  ]
}
print(json.dumps(data, indent=2))
" > "\$OUT"
```

### Anti-Patterns to Avoid
- **Live SSH from API route:** Never shell out to SSH in an API route — it would block for seconds and fail when Tailscale is flaky.
- **Storing cron data in a new DB:** The cron jobs' `state.lastRunAtMs` is already in `jobs.json`. The cron API route already reads it. Duplicating into a separate DB adds a maintenance burden.
- **Executable remote actions from browser:** Locked decision — no "run now" buttons, only copy-paste commands.
- **`child_process.exec` with shell=true:** Use `execFile` with explicit args to avoid shell injection (even if internal-only).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table layout | Custom div grid | Existing `table.tsx` (Table/TableHeader/TableBody/TableRow/TableHead/TableCell) | Already in codebase, handles overflow |
| Health color badges | Custom span | Existing `Badge` with `success`/`warning`/`error` variants | Color system already matches green/yellow/red semantics |
| "N seconds ago" freshness | Custom timer | Existing `FreshnessIndicator` component | Already handles elapsed time with color transitions |
| Cron next-run calculation | Custom cron parser | `cron-parser` (already in MC package.json via `cron-utils.ts`) | Timezone-aware, handles complex expressions |
| Toast notification | Custom state manager | Local `useState` with 2s timeout | No toast library needed for a single copy action |

**Key insight:** The Mission Control codebase is mature — every UI primitive needed (Table, Badge, FreshnessIndicator, Card, Button) already exists. The planner should reference existing files rather than building new components.

## Common Pitfalls

### Pitfall 1: bd is not installed on EC2
**What goes wrong:** The inventory in CONTEXT.md lists `bd` as a CLI tool. SSH to EC2 confirms `bd: command not found`. Including it as "red/not installed" is correct.
**Why it happens:** bd is a Mac-side tool (local CLI). CONTEXT.md lists it because Andy uses it locally.
**How to avoid:** In the health-check script, always check `command -v bd 2>/dev/null` rather than assuming installation. Display as "not installed" (red) with no version.
**Warning signs:** Script errors if you do `bd --version 2>/dev/null || echo "error"` and bd isn't in PATH — need `|| echo "not installed"`.

### Pitfall 2: whisper --version exits non-zero
**What goes wrong:** `whisper --version` prints usage and exits 1 (it's an argparse CLI). The SSH test showed it prints `usage: whisper [-h] ...`.
**Why it happens:** Whisper's CLI doesn't support `--version` flag — it just shows usage.
**How to avoid:** Use `pip show openai-whisper 2>/dev/null | grep Version` inside the venv, or just check the venv directory exists as the health signal. Version string can be extracted via `pip show` inside `~/whisper-venv`.
**Warning signs:** Script exits with error code for whisper, marking it red incorrectly.

### Pitfall 3: Cron lastRun data is in jobs.json `state` not `lastRun`
**What goes wrong:** Initial inspection of jobs.json showed `"lastRun": {}`. The actual data is in `state.lastRunAtMs` and `state.lastStatus`.
**Why it happens:** The jobs.json schema has both a `lastRun` object (often empty) and a `state` object (populated). EC2 live check confirmed `state.lastRunAtMs` has real millisecond timestamps.
**How to avoid:** Parse `job.state.lastRunAtMs` (not `job.lastRun`) for last-run timestamps. Convert ms → ISO string with `new Date(ms).toISOString()`.
**Warning signs:** All cron jobs show "never ran" despite being actively running.

### Pitfall 4: Health-check script runs as cron — PATH issues
**What goes wrong:** Shell script cron job has minimal PATH. `openclaw`, `gog`, `node` may not be found if using bare names.
**Why it happens:** Cron executes with a stripped environment, not the user's login shell.
**How to avoid:** Use full paths in the health-check script: `/home/ubuntu/.npm-global/bin/openclaw`, `/usr/local/bin/gog`, `/usr/bin/node`. Or set `PATH` explicitly at top of script.
**Warning signs:** Script works when run manually but produces "error" for all tools when run via cron.

### Pitfall 5: Refresh endpoint blocking on slow script
**What goes wrong:** The health-check script is triggered via POST to `/api/tools/refresh`. If the script takes >10 seconds, the API times out.
**Why it happens:** Next.js API routes have a default execution timeout.
**How to avoid:** Run the script with a hard timeout: `execFile('timeout', ['15', '/home/ubuntu/scripts/tools-health-check.sh'], ...)`. Or fire-and-forget (spawn without await) and return 202 immediately, letting SWR pick up the result on the next 30s refresh.
**Warning signs:** Refresh button appears to hang; Next.js logs timeout errors.

### Pitfall 6: `force-dynamic` required for filesystem reads
**What goes wrong:** API routes that read filesystem files get statically cached by Next.js build if `dynamic` is not set.
**Why it happens:** Next.js 14 aggressively caches routes unless opted out.
**How to avoid:** Every API route that reads live files needs `export const dynamic = "force-dynamic"` — consistent with the existing cron and db-status routes.

## Code Examples

### Cron section: parse jobs.json state correctly
```typescript
// Source: live EC2 data inspection (2026-02-26)
interface CronJob {
  id: string;
  name: string;
  enabled: boolean;
  schedule: { expr: string; tz?: string };
  state?: {
    nextRunAtMs?: number;
    lastRunAtMs?: number;
    lastStatus?: string;
    consecutiveErrors?: number;
  };
}

function getCronHealth(job: CronJob): "green" | "yellow" | "red" {
  if (!job.enabled) return "red";
  const state = job.state;
  if (!state?.lastRunAtMs) return "yellow"; // never ran
  const errors = state.consecutiveErrors ?? 0;
  if (errors >= 2) return "red";
  if (errors === 1) return "yellow";
  // Check recency based on schedule
  const lastRun = new Date(state.lastRunAtMs);
  const intervalMs = estimateIntervalMs(job.schedule.expr); // from cron-utils
  const overdue = Date.now() - lastRun.getTime() > intervalMs * 2.5;
  if (overdue) return "yellow";
  return "green";
}
```

### NavBar: add /tools link
```typescript
// In /src/components/NavBar.tsx — add to links array
import { Wrench } from "lucide-react"; // or Terminal

{ href: "/tools", label: "Tools", icon: Wrench },
```

### Summary banner pattern
```tsx
// Health summary counts
const green = tools.filter(t => t.status === "green").length;
const yellow = tools.filter(t => t.status === "yellow").length;
const red = tools.filter(t => t.status === "red").length;

<div className="flex items-center gap-4 rounded-lg border border-border/60 bg-card/50 px-4 py-3">
  <span className="text-sm text-muted-foreground">{total} tools</span>
  <span className="text-sm text-emerald-400 font-medium">{green} healthy</span>
  {yellow > 0 && <span className="text-sm text-amber-400 font-medium">{yellow} warning</span>}
  {red > 0 && <span className="text-sm text-rose-400 font-medium">{red} critical</span>}
  <div className="ml-auto flex items-center gap-2">
    <span className="text-xs text-muted-foreground">Last checked: {lastChecked}</span>
    <button onClick={handleRefresh}><RefreshCw className="h-3.5 w-3.5" /></button>
  </div>
</div>
```

### Health indicator dot (inline, not Badge)
```tsx
// Compact dot for table rows — smaller than Badge pill
const HEALTH_DOT: Record<string, string> = {
  green: "bg-emerald-500",
  yellow: "bg-amber-500",
  red: "bg-rose-500",
};

<span className={cn("inline-block h-2 w-2 rounded-full flex-shrink-0", HEALTH_DOT[status])} />
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cards for all pages | Tables for ops data | Phase 40 decision | Use Table component for /tools, not cards |
| DB for everything | JSON file for simple caches | /api/cron precedent | tools-health.json is correct, no tools.db needed |
| Polling via setInterval | SWR global refreshInterval: 30000 | Phase 29 | Auto-refresh already wired — no page-level setInterval |

**Deprecated/outdated:**
- None relevant to this phase.

## Open Questions

1. **whisper version string**
   - What we know: `whisper --version` shows usage (exits 1). `pip show openai-whisper` inside venv gives version.
   - What's unclear: Is it worth running `pip show` in the script, or just check venv directory existence?
   - Recommendation: Check venv directory existence for green/red. Use `pip show openai-whisper 2>/dev/null | grep ^Version` for version string. Low priority — just needs to be non-blocking in script.

2. **bd on EC2 — display vs hide**
   - What we know: `bd` is not installed on EC2. CONTEXT.md lists it in inventory.
   - What's unclear: Should the row be shown as "not installed" (red) or omitted entirely?
   - Recommendation: Show it as red "not installed" — the user explicitly listed it in the inventory and the red indicator is informative ("I know bd isn't on EC2").

3. **Refresh endpoint — sync vs fire-and-forget**
   - What we know: Health-check script takes a few seconds. Next.js has execution limits.
   - What's unclear: Exact duration of the shell script.
   - Recommendation: Use fire-and-forget (spawn detached, return 200 immediately). SWR refreshInterval: 30000 will pick up the new data within 30 seconds. Add a local `refreshing` state to disable the button for 15s after click.

4. **Cron section: all 24 jobs or filtered subset**
   - What we know: There are 24 cron jobs in jobs.json. Many are heartbeats (5 heartbeat jobs).
   - What's unclear: Whether to show all 24 or filter to "meaningful" ones.
   - Recommendation: Show all 24 but group heartbeats as a collapsed sub-section, or just show all in a single table sorted by name. Let the planner decide. Either way, the data access is the same.

## Inventory Reference

### CLI Tools on EC2
| Tool | Binary Path | Version | Version Command |
|------|-------------|---------|----------------|
| openclaw | `/home/ubuntu/.npm-global/bin/openclaw` | 2026.2.17 | `openclaw --version` |
| gog | `/usr/local/bin/gog` | v0.9.0 | `gog --version` |
| node | `/usr/bin/node` | v22.22.0 | `node --version` |
| npm | (bundled with node) | 10.9.4 | `npm --version` |
| whisper | `/home/ubuntu/whisper-venv/bin/whisper` | (use pip show) | `pip show openai-whisper` |
| bd | not installed | N/A | — |

### Plugins
| Plugin | Directory | Config Status | Version |
|--------|-----------|---------------|---------|
| camofox-browser | `/home/ubuntu/.openclaw/extensions/camofox-browser` | In openclaw.json plugins.entries | 1.0.13 |
| secureclaw | `/home/ubuntu/.openclaw/plugins/secureclaw` | In openclaw.json plugins.entries | 2.1.0 |
| observability-hooks | `/home/ubuntu/.openclaw/extensions/observability-hooks` | In openclaw.json plugins.entries | 1.0.0 |
| slack | (built-in) | In openclaw.json plugins.entries | N/A |

Note: CONTEXT.md lists only camofox-browser and secureclaw. observability-hooks is in config too — planner should decide whether to include it.

### Scripts
| Script | Path | Category |
|--------|------|----------|
| prune-sessions.sh | `/home/ubuntu/scripts/prune-sessions.sh` | Session management |
| process-voice-notes.py | `/home/ubuntu/scripts/process-voice-notes.py` | Voice pipeline |
| collect_verified.sh | `/home/ubuntu/.openclaw/skills/clawdstrike/scripts/collect_verified.sh` | Security audit |

### Cron Jobs Summary
24 total jobs in `~/.openclaw/cron/jobs.json`. All have `state.lastRunAtMs` timestamps (except `monthly-expense-summary` and `yolo-build-notify` which show `?`). Data already accessible via existing `/api/cron` route at `state.lastRunAtMs` (milliseconds epoch).

## Sources

### Primary (HIGH confidence)
- Live EC2 SSH inspection (2026-02-26) — tools installed, versions, paths, jobs.json schema
- `/home/ubuntu/clawd/mission-control/src/` — full codebase read: API routes, components, lib modules
- `~/.openclaw/openclaw.json` — plugins configuration structure
- `~/.openclaw/cron/jobs.json` — 24 cron jobs with full state schema

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — user-locked choices applied directly
- Existing route patterns (`/api/cron`, `/api/yolo/builds`, `/api/db-status`) — high confidence these patterns work since they're in production

### Tertiary (LOW confidence)
- Whisper version via `pip show` — inferred; not verified in this session but standard Python package approach

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use, no new dependencies
- Architecture: HIGH — patterns directly copied from existing working routes
- Pitfalls: HIGH — bd/whisper issues verified via live EC2 SSH; cron state schema verified from live data

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable stack; EC2 tool versions may change but patterns hold)
