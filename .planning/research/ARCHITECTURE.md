# Architecture: YOLO Dev Integration with Existing OpenClaw System

**Domain:** Autonomous overnight prototype builder integrated into existing multi-agent OpenClaw deployment
**Researched:** 2026-02-24
**Confidence:** HIGH (integration patterns proven across 6 milestones), MEDIUM (code execution safety in Docker sandbox)

---

## System Context: What Already Exists

```
EC2 (100.72.143.9) -- Tailscale -- t3.small (2GB RAM + 2GB swap)
|
+-- OpenClaw Gateway :18789 (tailnet bind)
|   +-- 7 agents (main, landos, rangeos, ops, quill, sage, ezra)
|   +-- 20 cron jobs (staggered across agents)
|   +-- 13 skills (~/.openclaw/skills/)
|   +-- Config: ~/.openclaw/openclaw.json
|   +-- Service: openclaw-gateway.service (systemd user)
|
+-- SQLite Databases (~/clawd/)
|   +-- coordination.db -- agent coordination, standup data
|   +-- health.db ------- Oura Ring metrics
|   +-- content.db ------ content pipeline (topics, articles)
|   +-- email.db -------- email tracking
|   +-- observability.db  LLM usage (tokens, models, turns)
|
+-- Mission Control (~/clawd/mission-control/)
|   +-- Next.js 14.2.15 + Tailwind + SWR + better-sqlite3
|   +-- Port 3001 (Tailscale direct)
|   +-- Pages: /, /agents, /memory, /office, /content, /analytics, /calendar
|   +-- Pattern: query module -> API route -> SWR poll -> component
|
+-- Docker Sandbox (agent runtime, network=bridge, read-only FS)
    +-- /workspace/ = ~/clawd/agents/{agent_id}/ (bind-mount, rw)
    +-- Explicit bind overlays for shared DBs:
    |   content.db, coordination.db, email.db -> /workspace/*.db
    +-- Host binaries: sqlite3, gh -> /usr/bin/* (bind-mount, ro)
    +-- Agents write code, run sqlite3 CLI, execute shell commands
```

**Key insight for YOLO Dev:** Bob (agent `main`) already executes arbitrary shell commands inside the Docker sandbox. He already writes files to `/workspace/`. He already uses sqlite3 CLI to read/write SQLite databases. YOLO Dev does not require new execution infrastructure -- it requires a new SKILL that instructs Bob on what to build, where to put it, and how to log it.

---

## Recommended Architecture

### Overview: YOLO Dev as a Cron-Triggered Skill

YOLO Dev follows the exact pattern established by the content pipeline (v2.1):

```
Cron fires at 11 PM PT
    -> OpenClaw creates session for agent "main" (Bob)
    -> Bob reads YOLO_SESSION.md from /workspace/
    -> Bob picks an idea (from YOLO_IDEAS.md or generates one)
    -> Bob builds prototype in /workspace/yolo-dev/{project-slug}/
    -> Bob logs build to yolo.db via sqlite3 CLI
    -> Bob posts summary to Slack channel
    -> Mission Control reads yolo.db via /api/yolo route
    -> /yolo page displays build history
```

### What Is New vs What Is Modified

| Component | Status | Action |
|-----------|--------|--------|
| `yolo-dev` skill | **NEW** | `~/.openclaw/skills/yolo-dev/SKILL.md` |
| `yolo-dev-overnight` cron | **NEW** | Added to openclaw.json crons array |
| `YOLO_SESSION.md` | **NEW** | `/workspace/YOLO_SESSION.md` (cron reference doc) |
| `YOLO_IDEAS.md` | **NEW** | `/workspace/YOLO_IDEAS.md` (idea bank) |
| `yolo.db` | **NEW** | `~/clawd/yolo.db` (shared via bind-mount) |
| `~/clawd/yolo-dev/` | **NEW** | Build artifact directory on host |
| MC query module | **NEW** | `src/lib/queries/yolo.ts` |
| MC API route | **NEW** | `src/app/api/dashboard/yolo/route.ts` |
| MC page | **NEW** | `src/app/yolo/page.tsx` + client component |
| MC navbar | **MODIFY** | Add /yolo link to existing NavBar |
| MC db layer | **MODIFY** | Add yolo.db to `DB_PATHS` in `src/lib/db-paths.ts` |
| openclaw.json | **MODIFY** | Add cron job + bind-mount for yolo.db + yolo-dev/ |
| MEMORY.md | **MODIFY** | Add YOLO Dev section (brief, <10 lines) |

**Zero new npm packages.** Zero new agents. Zero new Slack channels. Bob is the builder.

---

## Component Boundaries

### 1. YOLO Dev Skill (`~/.openclaw/skills/yolo-dev/SKILL.md`)

**Responsibility:** Define what Bob does during a YOLO Dev session. This is the brain.

**Key sections:**
- **Idea Selection:** Read YOLO_IDEAS.md for pending ideas. If empty, generate an idea based on project context (Andy's interests from MEMORY.md) and current trends
- **Tech Stack Constraint:** Python + HTML/CSS/JS only. No npm install, no pip install beyond stdlib + what's available in sandbox. This prevents build failures from missing dependencies
- **Build Protocol:** Create directory, write code, test by running it, capture output
- **Logging Protocol:** INSERT into yolo.db with project name, description, tech stack, status, artifacts path, build log
- **Time Budget:** Single session, ~45 min target. Don't try to build a SaaS -- build a working demo
- **Failure Protocol:** If build fails, log the failure with error details. Partial builds are fine. Never delete a failed attempt

**Pattern precedent:** Follows exact SKILL.md structure from `seo-writer`, `content-editor`, `coding-assistant` skills. Same markdown format, same section headers.

### 2. Cron Job (`yolo-dev-overnight`)

**Responsibility:** Trigger YOLO Dev session at a low-activity time.

```json
{
  "id": "yolo-dev-overnight",
  "name": "YOLO Dev Overnight Build",
  "schedule": "0 6 * * *",
  "description": "Autonomous overnight prototype build",
  "kind": "agentTurn",
  "agentId": "main",
  "message": "Read /workspace/YOLO_SESSION.md and follow the YOLO Dev build protocol. Pick a project idea, build a working prototype, log results to yolo.db.",
  "sessionTarget": "main",
  "model": "sonnet",
  "isolated": true,
  "silentOnNoDelivery": false
}
```

**Schedule:** `0 6 * * *` = midnight PT (UTC-8 offset, 6 AM UTC). Runs daily. Can be adjusted to skip weekends if desired.

**Why `isolated: true`:** YOLO Dev sessions are long and resource-intensive. Isolating ensures no interference with morning briefing (which fires at 6 AM PT = 2 PM UTC) or other cron jobs.

**Why `model: "sonnet"`:** Sonnet is the sweet spot -- fast enough for code generation, smart enough for architecture decisions. Opus would be overkill and consume rate limit budget. Haiku is too limited for multi-file code generation.

**Why `agentId: "main"` (Bob):** Bob has the broadest context -- access to MEMORY.md, all shared DBs, GitHub CLI, sqlite3, and the most workspace files. Creating a new "yolo" agent would require duplicating all these bind-mounts and building up agent context from scratch. Bob already builds code via the `coding-assistant` skill.

### 3. Session Reference Doc (`YOLO_SESSION.md`)

**Responsibility:** Detailed instructions for the cron session. Keeps the cron message concise while providing rich context.

**Pattern precedent:** Same as MEETING_PREP.md, STANDUP.md, WRITING_SESSION.md, REVIEW_SESSION.md, PUBLISH_SESSION.md -- all existing cron reference docs.

**Location:** `~/clawd/agents/main/YOLO_SESSION.md` (mapped to `/workspace/YOLO_SESSION.md` in sandbox)

**Contents:**
```markdown
# YOLO Dev Session Protocol

## Step 1: Select Project
- Check /workspace/YOLO_IDEAS.md for pending ideas (priority 1 first)
- If no pending ideas, generate one based on your knowledge of Andy's interests
- Ideas should be achievable in a single session (~45 min of coding)

## Step 2: Initialize Project
- Create /workspace/yolo-dev/{date}-{slug}/ directory
- Start a BUILD_LOG.md in the project directory

## Step 3: Build
- Default stack: Python 3 + HTML/CSS/JS
- Available tools: python3, sqlite3, curl, bash
- Write clean, commented code
- Test by running: `python3 main.py` or `python3 -m http.server`
- Capture test output in BUILD_LOG.md

## Step 4: Log to Database
- Log the build to /workspace/yolo.db using sqlite3 CLI:
  INSERT INTO builds (date, project_name, slug, description, tech_stack,
    status, artifacts_path, build_log, idea_source, lines_of_code,
    files_created, created_at)
  VALUES (...)

## Step 5: Report
- Post summary to channel:D0AARQR0Y4V (Andy's DM)
- Include: project name, what it does, status (complete/partial/failed),
  lines of code, and one-sentence takeaway
```

### 4. Idea Bank (`YOLO_IDEAS.md`)

**Responsibility:** Curated list of project ideas that Bob can pick from. Andy adds ideas; Bob consumes them.

**Location:** `~/clawd/agents/main/YOLO_IDEAS.md` (in workspace)

**Format:**
```markdown
# YOLO Dev Ideas

## Pending
- [ ] **CLI Weather Dashboard** - Terminal weather display using NOAA API. Python + curses. Priority: 1
- [ ] **Markdown Resume Generator** - Parse YAML resume data, output styled HTML. Python + Jinja2. Priority: 2
- [ ] **SQLite Query Analyzer** - Parse .db files and suggest indexes. Python + sqlite3. Priority: 2

## Completed
- [x] **First Build** - Description (2026-02-25)

## Rules
- Pick highest priority (1 = do next, 2 = whenever, 3 = someday)
- If all pending ideas are priority 3 or lower, generate your own
- After building, move the idea to Completed with the date
- Andy adds ideas here anytime; Bob only consumes, never adds to Pending
```

**Why a static file, not a DB table:** Ideas are curated by Andy (human). He'll edit this file via Slack DM to Bob or directly. A text file is simpler to view and edit than a database table. The ideas list will be small (5-20 items). No need for queryability.

### 5. Build Artifacts Directory (`~/clawd/yolo-dev/`)

**Responsibility:** Persistent storage for all YOLO Dev build outputs.

**Host path:** `~/clawd/yolo-dev/`
**Container path:** `/workspace/yolo-dev/` (via bind-mount in agents.defaults.sandbox.docker.binds)

**Directory structure:**
```
~/clawd/yolo-dev/
+-- 2026-02-25-cli-weather/
|   +-- main.py
|   +-- templates/
|   +-- BUILD_LOG.md
|   +-- README.md
+-- 2026-02-26-resume-gen/
|   +-- main.py
|   +-- resume.yaml
|   +-- output.html
|   +-- BUILD_LOG.md
+-- ...
```

**Convention:** `{YYYY-MM-DD}-{slug}/` directories. Date prefix ensures chronological ordering in `ls`. Slug matches the yolo.db `slug` column.

**Why `~/clawd/yolo-dev/` and not inside the agent workspace (`~/clawd/agents/main/yolo-dev/`):** Build artifacts should persist independently of agent workspace management. The `~/clawd/` directory is the project root where all persistent data lives (content.db, coordination.db, mission-control/). Keeping yolo-dev at the same level is consistent. Also, if the agent workspace is ever reset or pruned, build artifacts survive.

**Bind-mount configuration** (add to openclaw.json `agents.defaults.sandbox.docker.binds`):
```json
"/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw"
```

### 6. YOLO Database (`yolo.db`)

**Responsibility:** Track all builds with metadata, status, and logs.

**Host path:** `~/clawd/yolo.db`
**Container path:** `/workspace/yolo.db` (explicit bind-mount overlay, same pattern as content.db)

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                    -- YYYY-MM-DD
    project_name TEXT NOT NULL,            -- Human-readable name
    slug TEXT NOT NULL UNIQUE,             -- URL-safe identifier
    description TEXT,                      -- What this project does
    tech_stack TEXT DEFAULT 'python',      -- python, python+html, bash, etc.
    status TEXT DEFAULT 'building',        -- building, complete, partial, failed
    artifacts_path TEXT,                   -- Relative path: yolo-dev/2026-02-25-weather/
    build_log TEXT,                        -- Full build log (stdout + decisions)
    idea_source TEXT DEFAULT 'generated',  -- 'ideas-file' or 'generated'
    lines_of_code INTEGER DEFAULT 0,      -- Total LOC produced
    files_created INTEGER DEFAULT 0,      -- Number of files created
    duration_minutes INTEGER,             -- Approximate build duration
    error_message TEXT,                   -- If failed, why
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS build_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL REFERENCES builds(id),
    file_path TEXT NOT NULL,              -- Relative to artifacts_path
    file_type TEXT,                       -- py, html, css, js, md, etc.
    line_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_builds_date ON builds(date DESC);
CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);
CREATE INDEX IF NOT EXISTS idx_build_files_build_id ON build_files(build_id);
```

**Why two tables:** `builds` is the summary Bob writes during the session. `build_files` is optional enrichment -- Bob can log individual files for the Mission Control UI to show a file tree. If this is too complex for v1, skip `build_files` and just use `files_created` count in `builds`.

**Bind-mount configuration** (add to openclaw.json `agents.defaults.sandbox.docker.binds`):
```json
"/home/ubuntu/clawd/yolo.db:/workspace/yolo.db:rw"
```

**DB creation:** The YOLO Dev skill instructions tell Bob to create the tables on first run using sqlite3 CLI `CREATE TABLE IF NOT EXISTS`. No migration infrastructure needed.

### 7. Mission Control Integration

**Pattern:** Identical to every other MC subsystem (content, email, agents, crons).

#### Query Module: `src/lib/queries/yolo.ts`

```typescript
// src/lib/queries/yolo.ts
import { getDb } from "@/lib/db";

export function getYoloBuilds(limit = 20, offset = 0) {
  const db = getDb("yolo");
  if (!db) return { builds: [], total: 0 };

  const total = db.prepare("SELECT COUNT(*) as cnt FROM builds").get() as { cnt: number };
  const builds = db.prepare(`
    SELECT id, date, project_name, slug, description, tech_stack,
           status, artifacts_path, idea_source, lines_of_code,
           files_created, duration_minutes, error_message, created_at
    FROM builds
    ORDER BY date DESC, created_at DESC
    LIMIT ? OFFSET ?
  `).all(limit, offset);

  return { builds, total: total.cnt };
}

export function getYoloStats() {
  const db = getDb("yolo");
  if (!db) return { total: 0, complete: 0, failed: 0, totalLoc: 0, streak: 0 };

  const stats = db.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as complete,
      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
      SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial,
      SUM(lines_of_code) as totalLoc,
      SUM(files_created) as totalFiles
    FROM builds
  `).get();

  return stats;
}

export function getYoloBuild(slug: string) {
  const db = getDb("yolo");
  if (!db) return null;

  const build = db.prepare(`
    SELECT * FROM builds WHERE slug = ?
  `).get(slug);

  return build;
}
```

#### API Route: `src/app/api/dashboard/yolo/route.ts`

```typescript
export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";
import { getYoloBuilds, getYoloStats } from "@/lib/queries/yolo";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get("limit") || "20");
    const offset = parseInt(searchParams.get("offset") || "0");

    const { builds, total } = getYoloBuilds(limit, offset);
    const stats = getYoloStats();

    return NextResponse.json({ builds, total, stats });
  } catch (error) {
    return NextResponse.json(
      { builds: [], total: 0, stats: { total: 0, complete: 0, failed: 0, totalLoc: 0 }, error: String(error) },
      { status: 500 }
    );
  }
}
```

#### Page: `src/app/yolo/page.tsx`

**Layout concept:**
```
/yolo
+-- Stats Row (SWR 30s poll)
|   +-- Total Builds (count)
|   +-- Success Rate (complete / total %)
|   +-- Total LOC (sum)
|   +-- Current Streak (consecutive successful builds)
|
+-- Build History (scrollable list/grid)
    +-- BuildCard per build:
        +-- Date + Project Name
        +-- Status badge (complete=green, partial=yellow, failed=red)
        +-- Description (1-2 lines)
        +-- Tech stack tag
        +-- LOC count + file count
        +-- Expandable: build log, error message
```

**UI components:** Uses existing shadcn Card, Badge, StatusCard patterns from Phase 30. No new UI libraries.

#### DB Layer Update: `src/lib/db-paths.ts`

Add one entry:
```typescript
yolo: "/home/ubuntu/clawd/yolo.db"
```

And extend the `DbName` type to include `"yolo"`.

---

## Data Flow: End-to-End Build Pipeline

```
                    TRIGGER
                       |
                       v
            +---------------------+
            | Cron: 0 6 * * *     |     midnight PT
            | (yolo-dev-overnight)|
            +----------+----------+
                       |
                       v
            +---------------------+
            | OpenClaw Gateway    |     creates isolated session
            | agent: main (Bob)   |     model: sonnet
            +----------+----------+
                       |
                       v
            +---------------------+
            | Docker Sandbox      |     read-only FS + bind-mounts
            | /workspace/         |
            +----------+----------+
                       |
          +------------+------------+
          |            |            |
          v            v            v
   +-----------+ +-----------+ +-----------+
   | Read      | | Build     | | Log       |
   | IDEAS.md  | | Prototype | | to DB     |
   | or        | | in        | | yolo.db   |
   | generate  | | yolo-dev/ | | via       |
   | idea      | | directory | | sqlite3   |
   +-----------+ +-----------+ +-----------+
                       |
                       v
            +---------------------+
            | Post Summary        |     channel:D0AARQR0Y4V
            | to Andy DM          |     (Andy's Slack DM)
            +---------------------+
                       |
                       v
            +---------------------+
            | Mission Control     |     SWR polls /api/dashboard/yolo
            | /yolo page          |     reads yolo.db (read-only)
            +---------------------+
```

---

## Integration Points

### Docker Sandbox Bind-Mounts (openclaw.json)

Two new bind-mounts added to `agents.defaults.sandbox.docker.binds`:

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "binds": [
            "... existing binds ...",
            "/home/ubuntu/clawd/yolo.db:/workspace/yolo.db:rw",
            "/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw"
          ]
        }
      }
    }
  }
}
```

**Why add both:**
- `yolo.db` needs to be at a known path (`/workspace/yolo.db`) so Bob can use sqlite3 CLI to write to it
- `yolo-dev/` needs to be bind-mounted so build artifacts persist on the host (Docker sandbox filesystem is ephemeral for non-mounted paths)

**Impact:** These binds apply to ALL agents (they're in `agents.defaults`). This is fine -- other agents won't touch these files. Same pattern as content.db and coordination.db.

### Cron Integration (openclaw.json)

One new cron job added to the `crons` array. Follows exact same JSON structure as the 20 existing cron jobs. Total after: 21 cron jobs.

### Skill Integration

One new skill directory:
```
~/.openclaw/skills/yolo-dev/
+-- SKILL.md
```

Total skills after: 14. The skill is available to all agents but only Bob's cron session references it.

### Slack Delivery

Summary posted to `channel:D0AARQR0Y4V` (Andy's DM channel). Uses the validated `channel:ID` format from v2.6.

Alternative: Create a `#yolo-dev` Slack channel for build logs. This keeps YOLO Dev noise out of Andy's DM. Decision for the roadmap planner.

### Mission Control Read Path

```
yolo.db (host: ~/clawd/yolo.db)
    |
    +-- better-sqlite3 (readonly, WAL mode)
    |
    +-- src/lib/queries/yolo.ts (query module)
    |
    +-- src/app/api/dashboard/yolo/route.ts (JSON endpoint)
    |
    +-- src/app/yolo/page.tsx (SWR polling, 30s refresh)
```

Identical pattern to content pipeline (`content.db -> queries/metrics.ts -> api/dashboard/metrics -> /content`).

---

## Code Execution Inside Docker Sandbox

### What Bob Can Already Do

Bob runs inside a Docker container with `network=bridge` (internet access) and these capabilities:
- **Shell commands:** `bash`, `python3`, `curl`, `wget`
- **File operations:** Read/write anything under `/workspace/`
- **SQLite:** `sqlite3` CLI (bind-mounted from host)
- **GitHub:** `gh` CLI (bind-mounted from host)
- **No package managers:** `pip install` and `npm install` are NOT available (read-only FS outside /workspace/)

### What Bob Needs for YOLO Dev

Everything Bob needs is already available:

| Capability | Available? | How |
|------------|-----------|-----|
| Write Python files | Yes | Write to `/workspace/yolo-dev/{slug}/` |
| Write HTML/CSS/JS | Yes | Same directory |
| Run Python scripts | Yes | `python3 main.py` |
| Test HTTP servers | Partially | `python3 -m http.server` works but not accessible from outside sandbox |
| Access SQLite | Yes | `sqlite3 /workspace/yolo.db` |
| Capture output | Yes | Redirect: `python3 main.py 2>&1 | head -100` |
| Read project context | Yes | MEMORY.md, YOLO_IDEAS.md, other workspace files |

### What Bob CANNOT Do (Constraints)

| Constraint | Why | Workaround |
|-----------|-----|-----------|
| `pip install` anything | Read-only FS outside /workspace/ | Use Python stdlib only. stdlib includes: http.server, json, sqlite3, csv, html, urllib, argparse, pathlib, etc. |
| `npm install` | Same reason | Write vanilla HTML/JS. No React, no bundlers |
| Start persistent services | Container lifecycle tied to session | Build is a script, not a server. Demo via output, not deployment |
| Access GPU | No GPU on t3.small | No ML/AI model training. Pure logic and web projects only |
| Large file downloads | Network is available but slow | Keep builds self-contained. No large dataset downloads |

### Python Stdlib Capabilities (What's Available Without pip)

Python 3.10+ stdlib is rich enough for meaningful prototypes:

- **Web:** `http.server`, `urllib.request`, `html`, `json`
- **Data:** `sqlite3`, `csv`, `statistics`, `collections`, `itertools`
- **CLI:** `argparse`, `curses`, `readline`
- **System:** `os`, `pathlib`, `shutil`, `subprocess`, `threading`
- **Text:** `re`, `textwrap`, `string`, `difflib`
- **Math:** `math`, `decimal`, `fractions`, `random`
- **I/O:** `io`, `tempfile`, `gzip`, `zipfile`

This is more than enough to build: CLI tools, data processors, file converters, simple web servers, SQLite utilities, text analyzers, game prototypes, automation scripts.

---

## Patterns to Follow

### Pattern 1: Cron + Reference Doc + Skill (Established v2.1)

```
Cron fires -> message points to reference doc -> agent reads doc
-> doc references skill -> agent follows skill protocol -> logs result
```

This is the exact pattern for all content pipeline crons (writing-check, review-check, publish-check). YOLO Dev follows it identically.

### Pattern 2: Shared DB via Bind-Mount Overlay (Established v2.1)

```
Host: ~/clawd/yolo.db
    |
    +-- Bind-mount: /workspace/yolo.db (rw) -- Bob writes via sqlite3 CLI
    +-- Read-only: Mission Control opens via better-sqlite3
```

Same as content.db, coordination.db, email.db. Writer is the agent (via sqlite3 CLI inside sandbox). Reader is Mission Control (via better-sqlite3 on host).

### Pattern 3: MC Query Module + API Route + SWR Page (Established v2.5)

Every Mission Control subsystem follows:
1. `src/lib/queries/{domain}.ts` -- prepared statements, exported functions
2. `src/app/api/dashboard/{domain}/route.ts` -- thin JSON handler
3. `src/app/{page}/page.tsx` -- server component with initial data
4. Client component with SWR polling (30s refresh)

YOLO Dev adds one more instance of this pattern. No architectural novelty.

### Pattern 4: Self-Initializing DB Schema (Pragmatic)

Bob creates the yolo.db schema on first run via `CREATE TABLE IF NOT EXISTS`. No migration tool needed. Same approach used for content.db (created by content pipeline agents on first run).

If yolo.db doesn't exist when Bob first writes to it, `sqlite3 /workspace/yolo.db` will create it. The bind-mount creates the host-side file automatically if the container creates it at the mount point.

**Correction:** The bind-mount requires the host file to exist FIRST. So `yolo.db` must be created on the host before the first YOLO Dev session:
```bash
sqlite3 ~/clawd/yolo.db "SELECT 1;"  # Creates empty DB file
```

This is a one-time setup step in Phase 1.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Creating a New Agent for YOLO Dev

**What people do:** Create a dedicated "yolo" agent with its own workspace, heartbeat, and configuration.

**Why it's wrong for this project:** A new agent requires: new workspace directory, bind-mount configuration, personality files (SOUL.md, AGENTS.md), heartbeat cron, Slack channel routing. For one daily build session, this is massive overhead. Bob already has all the tools needed. The content pipeline uses 3 separate agents because they have distinct roles in a pipeline (researcher, writer, reviewer). YOLO Dev is a single-agent activity.

**Do this instead:** Use Bob (agent `main`) with an isolated cron session.

### Anti-Pattern 2: Running npm/pip Install Inside Sandbox

**What people do:** Try to install packages at build time for richer project capabilities.

**Why it's wrong:** The sandbox filesystem is read-only outside `/workspace/`. Package managers need to write to system directories (`/usr/lib/`, `/usr/local/`, etc.). Even if you worked around this, installed packages wouldn't persist between sessions.

**Do this instead:** Constrain the tech stack to Python stdlib + vanilla HTML/JS. This is a feature, not a limitation -- it forces creative, dependency-free prototypes that work anywhere.

### Anti-Pattern 3: Building a Custom Execution Engine

**What people do:** Build a separate script/service that watches for build requests and executes code.

**Why it's wrong:** Bob already IS the execution engine. He runs shell commands inside Docker. Adding another execution layer creates complexity and a second failure mode.

**Do this instead:** The skill file tells Bob how to execute. Bob runs Python directly. The cron triggers Bob. No intermediary.

### Anti-Pattern 4: Storing Build Logs in Slack Instead of a Database

**What people do:** Post full build logs to Slack and rely on Slack history for build tracking.

**Why it's wrong:** Slack messages are ephemeral in free tiers, unsearchable in context, and not queryable for dashboards. The content pipeline learned this -- everything goes in SQLite.

**Do this instead:** Build log goes in yolo.db. Slack gets a summary (project name, status, LOC, one-liner). Dashboard reads from yolo.db.

### Anti-Pattern 5: Trying to Deploy Prototypes

**What people do:** Add deployment steps (Docker build, server start, port mapping) to the build pipeline.

**Why it's wrong:** YOLO Dev is about building, not deploying. The Docker sandbox can't expose ports to the host. Deployment adds failure modes that have nothing to do with whether the prototype works. The value is in the code, not the running service.

**Do this instead:** Build artifacts are files on disk. "Working" means the script runs and produces output. If Andy wants to deploy a prototype later, he does it manually -- that's a separate activity.

---

## Build Order: Dependency-Aware Phase Sequence

```
Phase 1: Infrastructure Foundation
  - Create ~/clawd/yolo-dev/ directory on host
  - Create ~/clawd/yolo.db (empty, schema created by Bob on first run)
  - Add bind-mounts to openclaw.json (yolo.db + yolo-dev/)
  - Add cron job to openclaw.json
  - Restart gateway (batch ALL config changes into one restart)
  DEPENDS ON: Nothing
  RISK: Gateway restart clears DM sessions (Pitfall 3 from previous research)
  MITIGATION: Schedule restart during low-activity window; DM Bob after

Phase 2: Skill + Session Protocol
  - Create ~/.openclaw/skills/yolo-dev/SKILL.md
  - Create ~/clawd/agents/main/YOLO_SESSION.md (cron reference doc)
  - Create ~/clawd/agents/main/YOLO_IDEAS.md (seed with 3-5 ideas)
  - Update MEMORY.md with YOLO Dev section
  DEPENDS ON: Phase 1 (bind-mounts must exist for Bob to write to yolo-dev/)
  RISK: Skill file too verbose -> consumes context budget
  MITIGATION: Keep SKILL.md under 3000 chars; test with openclaw context list
  NOTE: No gateway restart needed (skill/workspace files are hot-loaded)

Phase 3: First Build Verification
  - Trigger cron manually: openclaw cron run --id yolo-dev-overnight
  - Verify: Bob picks an idea, creates directory, writes code, logs to yolo.db
  - Verify: Slack summary delivered to Andy's DM
  - Verify: Build artifacts exist at ~/clawd/yolo-dev/{slug}/
  - Verify: yolo.db has correct schema and row data
  - Fix any issues discovered during first run
  DEPENDS ON: Phase 2 (skill and session docs must exist)
  RISK: Bob may not follow the build protocol precisely on first attempt
  MITIGATION: Review BUILD_LOG.md, adjust SKILL.md/YOLO_SESSION.md as needed

Phase 4: Mission Control Dashboard
  - Add yolo.db to MC db-paths.ts
  - Create src/lib/queries/yolo.ts
  - Create src/app/api/dashboard/yolo/route.ts
  - Create src/app/yolo/page.tsx + client component
  - Add /yolo to NavBar
  - Build and verify on EC2
  DEPENDS ON: Phase 3 (yolo.db must have at least one row for the page to display data)
  RISK: Standard MC development risk (build errors, type mismatches)
  MITIGATION: Follow exact Phase 30 patterns
```

**Phase ordering rationale:**
- Phase 1 first because ALL other phases depend on the bind-mounts and cron existing
- Phase 2 before Phase 3 because Bob needs the skill and session docs to know what to do
- Phase 3 before Phase 4 because the dashboard needs real data to test against
- Phase 1 is the only phase requiring a gateway restart -- batch everything
- Phases 2-4 don't require gateway restarts (skill files, workspace docs, and MC code changes are all hot-loadable)

**Parallelization opportunity:** Phase 4 (MC dashboard) can start after Phase 1 completes if you're willing to test with mock data. But Phase 3 is cheap (one cron trigger) and provides real data, so sequential is better.

---

## Scalability Considerations

This is a personal overnight build tool. "Scaling" means: what happens after 30, 100, 365 builds?

| Concern | At 30 builds | At 100 builds | At 365 builds |
|---------|-------------|--------------|--------------|
| yolo.db size | ~50KB | ~200KB | ~500KB |
| Disk usage (artifacts) | ~3MB (avg 100KB/build) | ~10MB | ~35MB |
| MC /yolo page load | Instant (30 rows) | Instant (paginate at 20) | Paginate; still fast |
| Build log length | Short (text column) | Paginate in UI | Consider truncating logs >50KB |
| Dashboard query time | <1ms | <1ms | <1ms (indexed) |

**First bottleneck:** Disk space for build artifacts. At ~100KB per build, 365 builds = ~35MB. The EC2 has 40GB EBS with ~13GB free. Not a concern for years.

**When to worry:** If builds start including large data files (images, datasets), the per-build average could jump to 1-10MB. Add a disk usage check to the YOLO Dev skill: "Total yolo-dev/ should stay under 1GB."

---

## Open Questions (Must Verify Before Implementation)

1. **Python version in Docker sandbox:** Verify `python3 --version` inside the sandbox. If Python 3.8 or older, some stdlib features (walrus operator, match/case) won't be available. The skill should document the available Python version.

2. **Can Bob create the yolo.db schema via sqlite3 CLI?** The `CREATE TABLE IF NOT EXISTS` pattern should work, but verify that the bind-mount creates the file correctly when Bob writes to an initially-empty DB.

3. **Cron schedule collision:** `0 6 * * *` (midnight PT) must not overlap with other crons. Check current cron schedule for any job near 6 AM UTC. The existing morning-briefing is at 2 PM UTC (6 AM PT), so midnight PT is safe -- 6 hours earlier.

4. **Should YOLO Dev run daily or weekly?** Daily = 365 builds/year, consistent habit. Weekly = 52 builds/year, less rate limit pressure. Start daily; reduce to weekdays or weekly if rate limits are a concern.

5. **Slack channel: DM or dedicated channel?** DM is simpler (no new channel). Dedicated `#yolo-dev` channel keeps build logs out of DM and makes them browsable in Slack history. Recommend DM for v1, add channel later if needed.

---

## Sources

### HIGH confidence (internal project)
- PROJECT.md -- full system inventory, tech stack, agent roster, cron jobs, databases
- MEMORY.md -- EC2 access, sandbox architecture, bind-mount patterns, cron configuration
- Phase 12 (Content DB + Agent Setup) -- established DB + bind-mount + skill pattern
- Phase 30 (Dashboard Metrics) -- established MC query module + API route + SWR pattern
- Phase 33 (Content Pipeline Improvements) -- established cron reference doc + channel:ID pattern
- v2.6 ROADMAP.md -- most recent milestone structure and phase pattern

### MEDIUM confidence (OpenClaw platform)
- OpenClaw cron documentation -- cron job JSON schema, `isolated` flag, `sessionTarget` behavior
- OpenClaw skill documentation -- SKILL.md format, skill loading, skill scoping
- OpenClaw sandbox documentation -- Docker bind-mount behavior, read-only FS, available binaries

### LOW confidence (needs verification on EC2)
- Python version available in Docker sandbox
- sqlite3 CLI behavior with bind-mounted empty DB files
- Exact cron schedule collision check (need to inspect current jobs.json)

---

*Architecture research for: pops-claw v2.7 YOLO Dev -- autonomous overnight prototype builder*
*Researched: 2026-02-24*
*Replaces: previous ARCHITECTURE.md covering v2.5 Mission Control Dashboard*
