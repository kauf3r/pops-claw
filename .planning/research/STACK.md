# Technology Stack: v2.7 YOLO Dev

**Project:** pops-claw -- Overnight Autonomous Builder
**Researched:** 2026-02-24
**Confidence:** HIGH (sandbox patterns validated in prior milestones), MEDIUM (overnight loop guardrails)

---

## Executive Summary

YOLO Dev adds zero new npm dependencies to Mission Control and zero new infrastructure to the EC2 host. The entire capability is built from: (1) a new OpenClaw skill + cron for Bob, (2) a new yolo.db SQLite database following the exact same pattern as the 5 existing databases, (3) Python/bash scripts executing inside the existing Docker sandbox, and (4) a new `/yolo` page in Mission Control following the established query-module + API-route + SWR pattern from v2.5.

The sandbox already has Python 3, bash, curl, git, and jq. Bob already writes files to `/workspace/` (bind-mounted to `~/clawd/agents/main/`). The overnight build pipeline is a cron job that triggers Bob with a YOLO_DEV.md reference doc, Bob generates code, writes files to `~/clawd/yolo-dev/<project>/`, logs progress to yolo.db, and posts the result to Slack. No new runtimes needed. No new Docker images. No new agents.

---

## Recommended Stack

### Core: Skill + Cron (Zero New Dependencies)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| OpenClaw Skill | N/A | `yolo-dev` skill in `~/.openclaw/skills/yolo-dev/SKILL.md` | Teaches Bob how to ideate, scaffold, build, test, and log YOLO projects. Same pattern as all 13 existing skills |
| OpenClaw Cron | N/A | `yolo-build` cron triggering nightly at 1 AM PT (08:00 UTC) | Triggers Bob to pick an idea and build it overnight. Same cron system as 20 existing jobs |
| Reference Doc | N/A | `~/clawd/agents/main/YOLO_DEV.md` | Standing instructions for overnight builds, idea bank, constraints. Same pattern as CONTENT_TRIGGERS.md |

**Rationale:** Bob is already an autonomous agent that writes files, executes code, and logs to SQLite. YOLO Dev is a new *behavior*, not a new *system*. The skill teaches Bob the behavior; the cron triggers it; the reference doc provides context.

### Database: yolo.db (SQLite, 6th Database)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite (via `sqlite3` CLI) | Already installed | yolo.db at `~/clawd/yolo-dev/yolo.db` | Same pattern as 5 existing databases. Bob writes via sqlite3 CLI in sandbox (bind-mounted). Mission Control reads via better-sqlite3 |
| better-sqlite3 | 12.6.2 (already installed) | Dashboard reads yolo.db | Already the Mission Control DB driver. Add yolo.db to the existing DB_PATHS registry |

**Schema Design:**

```sql
-- ~/clawd/yolo-dev/yolo.db

CREATE TABLE builds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_name TEXT NOT NULL,           -- e.g. "wifi-signal-mapper"
  slug TEXT NOT NULL UNIQUE,            -- URL/folder-safe: "wifi-signal-mapper"
  description TEXT NOT NULL,            -- 1-2 sentence pitch
  idea_source TEXT,                     -- what inspired it: "morning-briefing", "voice-note", "random"
  tech_stack TEXT NOT NULL,             -- "python", "html+js", "python+flask"
  status TEXT NOT NULL DEFAULT 'ideating',  -- ideating|building|testing|completed|failed|abandoned
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at TEXT,
  build_duration_seconds INTEGER,       -- wall clock from start to completion
  files_created INTEGER DEFAULT 0,      -- count of files generated
  lines_of_code INTEGER DEFAULT 0,      -- total LOC across all files
  error_message TEXT,                   -- if failed, what went wrong
  demo_url TEXT,                        -- if servable, how to access
  slack_message_ts TEXT,                -- Slack message ID for the build report
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE build_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  build_id INTEGER NOT NULL REFERENCES builds(id),
  phase TEXT NOT NULL,                  -- "ideation"|"scaffolding"|"implementation"|"testing"|"packaging"
  message TEXT NOT NULL,                -- what happened
  timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE build_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  build_id INTEGER NOT NULL REFERENCES builds(id),
  file_path TEXT NOT NULL,              -- relative to project dir: "app.py", "templates/index.html"
  language TEXT,                        -- "python", "html", "javascript", "css"
  line_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for dashboard queries
CREATE INDEX idx_builds_status ON builds(status);
CREATE INDEX idx_builds_created ON builds(created_at DESC);
CREATE INDEX idx_build_logs_build ON build_logs(build_id);
CREATE INDEX idx_build_files_build ON build_files(build_id);
```

**Why this schema:** Three tables track the full lifecycle. `builds` is the main record (what was built, outcome, metrics). `build_logs` captures the step-by-step narrative (useful for debugging and for the dashboard timeline view). `build_files` inventories artifacts (useful for "what did it create?" display). The `slug` column becomes the folder name under `~/clawd/yolo-dev/`.

**Why NOT a single table:** Build logs are append-only and high-volume (10-50 entries per build). Mixing them with the builds table would make dashboard queries for "list all builds" pull unnecessary log data. The three-table design matches the content pipeline pattern (topics, articles, pipeline_activity).

### Sandbox Runtime: Already Sufficient

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python 3 | 3.11 (Debian Bookworm) | Default prototyping language | Already in the sandbox image (`openclaw-sandbox:bookworm-slim` includes python3). No pip needed for stdlib-only prototypes |
| bash | 5.2 | Script execution, file manipulation | Already in sandbox |
| curl | Already installed | HTTP testing, API interaction | Already in sandbox |
| git | Already installed | Version tracking of builds (optional) | Already in sandbox |
| sqlite3 CLI | Debian 12-compatible binary | Write to yolo.db from sandbox | Already bind-mounted at `/usr/bin/sqlite3` (Phase 6 fix: glibc-compatible binary at `~/clawd/sqlite3-compat`) |
| Node.js | **NOT in default sandbox** | For JS/HTML prototypes that need a dev server | **See "What NOT to Add" -- stdlib Python + static HTML covers 90% of prototypes** |

**Key insight:** The default sandbox image includes Python 3 but NOT pip, NOT Node.js, NOT Go, NOT Rust. This is fine. YOLO Dev prototypes should use Python stdlib (http.server, json, sqlite3, urllib, etc.) and static HTML/CSS/JS. If a prototype needs pip packages, Bob can install them via `python3 -m ensurepip && pip install X` in the sandbox (requires `readOnlyRoot: false` which is already the case based on the setupCommand pattern used for other tools). But the SKILL.md should strongly prefer stdlib-only prototypes.

### Build Artifact Storage: Filesystem

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Filesystem | N/A | `~/clawd/yolo-dev/<slug>/` on EC2 host | Bind-mounted into sandbox as `/workspace/yolo-dev/<slug>/`. Each build gets its own directory. Simple, inspectable, no extra infrastructure |

**Directory structure per build:**

```
~/clawd/yolo-dev/
+-- yolo.db                        # Build metadata database
+-- wifi-signal-mapper/            # Build 1
|   +-- README.md                  # Auto-generated by Bob
|   +-- app.py                     # Main application
|   +-- templates/
|       +-- index.html
+-- habit-streak-tracker/          # Build 2
|   +-- README.md
|   +-- tracker.py
|   +-- data/
+-- ...
```

**Why filesystem over S3/cloud:** Single machine, personal use, inspectable via SSH. The files are already on the EC2 instance. Adding cloud storage adds cost and complexity for zero benefit.

### Mission Control: /yolo Page (Zero New Dependencies)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js 14 | 14.2.15 (existing) | `/yolo` page route | Same framework, same patterns as existing 7 pages |
| better-sqlite3 | 12.6.2 (existing) | Read yolo.db | Add to existing DB_PATHS registry, same singleton pattern |
| SWR | 2.3.3 (existing) | Poll `/api/yolo/builds` | Same polling pattern as all other dashboard data |
| shadcn/ui | Existing | Card, Badge, Table components | Already installed. Status badges (building/completed/failed) use existing Badge variants |
| Recharts | 3.7.0 (existing) | Build frequency chart, LOC trends | Already installed via shadcn charts |
| date-fns | 3.6.0 (existing) | Relative timestamps ("built 2 days ago") | Already installed |

**New files to create on EC2:**

```
~/clawd/mission-control/src/
+-- app/
|   +-- yolo/
|   |   +-- page.tsx                # /yolo page (server component, initial render)
|   +-- api/
|       +-- yolo/
|           +-- builds/
|           |   +-- route.ts        # GET /api/yolo/builds (list all builds)
|           +-- builds/[id]/
|               +-- route.ts        # GET /api/yolo/builds/:id (build detail + logs + files)
+-- lib/
|   +-- db-paths.ts                 # ADD "yolo" to DB_NAMES, DB_PATHS, DB_LABELS
|   +-- queries/
|       +-- yolo.ts                 # Prepared statements for yolo.db queries
+-- components/
    +-- yolo/
        +-- build-card.tsx          # Individual build card with status badge
        +-- build-timeline.tsx      # Build log timeline for detail view
        +-- build-stats.tsx         # Aggregate stats (total builds, success rate, LOC)
```

**Dashboard integration pattern (same as all existing pages):**

1. Add `yolo` to `DB_PATHS` in `db-paths.ts`: `yolo: "/home/ubuntu/clawd/yolo-dev/yolo.db"`
2. Create query module `queries/yolo.ts` with prepared statements
3. Create API route `/api/yolo/builds/route.ts` that calls query functions
4. Create page `/yolo/page.tsx` that reads server-side + passes to client
5. Add `/yolo` to the navigation sidebar
6. SWR polls `/api/yolo/builds` every 60 seconds

### Cron Delivery: Slack + Morning Briefing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Slack Socket Mode | Existing | Post build results to DM or #ops | Same delivery pattern as all other cron outputs |
| Morning Briefing | Existing | Add "YOLO Dev" section to briefing | New Section 11 (or append to existing): last night's build result, project name, status, LOC |

**No new Slack channels.** Build results post to Bob's DM (same as evening recap). Morning briefing includes a YOLO summary line.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build runtime | Python 3 (stdlib) in existing sandbox | Install Node.js in sandbox via setupCommand | Adds startup latency, requires `readOnlyRoot: false` + `network: bridge` (already true). Python stdlib covers 90% of prototype needs. If Node is genuinely needed for a specific build, Bob can install it on-demand |
| Build runtime | Existing sandbox image | Build custom Docker image with full dev tooling | Custom images require maintenance, disk space (1-2GB+), and rebuilds on updates. The existing image plus on-demand installs is sufficient for prototyping |
| Database | yolo.db (SQLite) | Extend coordination.db with yolo tables | coordination.db is for agent coordination, not feature data. Each domain gets its own DB (content.db, email.db, etc.) -- yolo.db follows this pattern |
| Database | SQLite via CLI | Python sqlite3 module | Bob already uses sqlite3 CLI for all other databases. Consistency > convenience |
| Artifact storage | Filesystem (~/clawd/yolo-dev/) | Git repo per project | Over-engineering for throwaway prototypes. Git adds complexity Bob would need to manage. If a project is worth keeping, Andy can `git init` manually |
| Dashboard | New /yolo page in Mission Control | Separate yolo dashboard | Defeats the "single pane of glass" principle. Mission Control is where system state lives |
| Agent | Bob (main agent) | New "Yolo" agent | Adding an 8th agent increases rate limit pressure, adds heartbeat overhead, needs Slack binding. Bob already has all the tools and context. A skill is sufficient |
| Trigger | Nightly cron (1 AM PT) | On-demand via Slack DM | Cron ensures builds happen automatically (the whole point of "overnight"). On-demand can be added later as a secondary trigger via YOLO_DEV.md protocol doc (same pattern as CONTENT_TRIGGERS.md) |
| Build framework | No framework (raw files) | Cookiecutter / copier templates | Templates constrain creativity. YOLO Dev is explicitly about wild ideas -- Bob should scaffold from scratch each time, informed by the skill's guidelines |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Node.js in sandbox image | Adds 100MB+ to image, startup cost. Python stdlib covers prototyping needs | Python 3 (already there). For HTML/JS projects, Bob writes static files and uses `python3 -m http.server` |
| pip packages pre-installed | Most prototypes should use stdlib. Pre-installed packages rot and bloat the image | On-demand `python3 -m ensurepip && pip install X` when genuinely needed (rare) |
| New OpenClaw agent | Rate limit pressure, heartbeat overhead, Slack channel setup | Bob with a `yolo-dev` skill. One agent, one skill, one cron |
| GitHub integration | Auto-pushing prototypes to GitHub adds OAuth setup, repo management, PR creation | Filesystem only. If a prototype is worth sharing, Andy pushes manually |
| CI/CD for prototypes | Testing infrastructure for throwaway code is over-engineering | Bob tests his own code by running it. The skill includes a "testing" phase where Bob executes the prototype |
| Custom Docker image | Maintenance burden, disk space, rebuild-on-update | Existing `clawdbot-sandbox:with-browser` image. It has python3, bash, curl, git |
| Deployment/hosting | Serving prototypes publicly adds security surface and infrastructure | Prototypes run locally. If demo-able, `python3 -m http.server 8080` inside sandbox, accessible via SSH tunnel |
| Build queuing system | Redis/RabbitMQ for build queues is enterprise-grade overkill | One build per cron run. Sequential. If it fails, it fails. Retry next night |
| @tanstack/react-table | Interactive sortable/filterable tables for build history | shadcn Table component (static). Build history is at most dozens of rows. No interactivity needed |
| WebSocket for build streaming | Real-time build log streaming to dashboard | SWR polling. Builds happen overnight when Andy is asleep. No one is watching live |

---

## Integration Points with Existing System

### yolo.db Access Pattern

**Writer:** Bob (main agent) via sqlite3 CLI inside Docker sandbox
- Path inside sandbox: `/workspace/yolo-dev/yolo.db`
- Bob creates the DB + schema on first build (idempotent CREATE TABLE IF NOT EXISTS)

**Reader:** Mission Control via better-sqlite3
- Path on host: `/home/ubuntu/clawd/yolo-dev/yolo.db`
- Read-only, WAL mode, same singleton pattern as 5 existing databases

**Bind-mount:** yolo-dev directory needs to be bind-mounted into the sandbox.
- Current bind-mounts include `~/clawd/agents/main/` -> `/workspace/`
- Since yolo-dev lives at `~/clawd/yolo-dev/` (NOT inside `agents/main/`), it needs its own bind-mount entry in `openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "binds": [
            "/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw"
          ]
        }
      }
    }
  }
}
```

This adds the yolo-dev directory as a writable mount inside the sandbox at `/workspace/yolo-dev/`. Bob can create project directories, write code files, and update yolo.db from inside the sandbox.

### Morning Briefing Integration

Add a YOLO Dev section to the morning briefing reference doc (MORNING_BRIEFING.md or equivalent). The section queries yolo.db for the most recent build:

```sql
SELECT project_name, status, description, build_duration_seconds,
       files_created, lines_of_code, error_message
FROM builds
ORDER BY created_at DESC
LIMIT 1;
```

Displays as:
```
## 11. YOLO Dev
Last night's build: **wifi-signal-mapper** (completed)
"Maps WiFi signal strength across rooms using ping latency"
Duration: 23 min | Files: 4 | LOC: 187
```

### Sandbox Environment Constraints

| Constraint | Impact on YOLO Dev | Mitigation |
|------------|-------------------|------------|
| 2GB RAM (t3.small) | Python prototypes must be lightweight | Skill instructs: no ML, no large datasets, no heavy computation |
| 40GB EBS disk | Build artifacts accumulate | Auto-cleanup: delete builds older than 30 days, keep last 20 builds |
| Docker bridge networking | Prototypes CAN make HTTP requests | Useful for API-consuming prototypes. Security acceptable (sandbox still isolated from host) |
| No GPU | No ML/AI training workloads | Skill explicitly excludes ML prototypes. Claude API calls from prototypes NOT supported (no API key in sandbox... and shouldn't be) |
| readOnlyRoot may be true | Can't pip install if root FS is readonly | If needed, set `readOnlyRoot: false` in agent-specific sandbox override. Currently the sandbox uses setupCommand which implies writable root |

### Cleanup Strategy

Build artifacts at `~/clawd/yolo-dev/` will accumulate. Add a cleanup cron or integrate into existing `prune-sessions.sh` pattern:

```bash
# ~/scripts/prune-yolo-builds.sh
# Keep last 20 builds, delete the rest
cd ~/clawd/yolo-dev
ls -dt */ | tail -n +21 | xargs rm -rf
# Also purge yolo.db entries for deleted builds
sqlite3 ~/clawd/yolo-dev/yolo.db "DELETE FROM build_files WHERE build_id NOT IN (SELECT id FROM builds ORDER BY created_at DESC LIMIT 20)"
sqlite3 ~/clawd/yolo-dev/yolo.db "DELETE FROM build_logs WHERE build_id NOT IN (SELECT id FROM builds ORDER BY created_at DESC LIMIT 20)"
sqlite3 ~/clawd/yolo-dev/yolo.db "DELETE FROM builds WHERE id NOT IN (SELECT id FROM builds ORDER BY created_at DESC LIMIT 20)"
```

---

## Installation / Setup Summary

```bash
# On EC2 (100.72.143.9)

# 1. Create yolo-dev directory
mkdir -p ~/clawd/yolo-dev

# 2. Add bind-mount to openclaw.json (via jq or python3)
# Add "/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw" to
# agents.defaults.sandbox.docker.binds array

# 3. Deploy yolo-dev skill
mkdir -p ~/.openclaw/skills/yolo-dev
# Write SKILL.md to ~/.openclaw/skills/yolo-dev/SKILL.md

# 4. Deploy YOLO_DEV.md reference doc
# Write to ~/clawd/agents/main/YOLO_DEV.md

# 5. Add yolo-build cron to openclaw.json
# Schedule: "0 8 * * *" (08:00 UTC = 1 AM PT)
# Agent: main, Model: sonnet, Isolated: true

# 6. Restart gateway (batch with any other config changes)
systemctl --user restart openclaw-gateway.service

# 7. DM Bob to re-establish session

# Mission Control (also on EC2, ~/clawd/mission-control/):

# 8. Update db-paths.ts to include yolo
# 9. Create queries/yolo.ts
# 10. Create /api/yolo/builds route
# 11. Create /yolo page
# 12. Add /yolo to nav
# 13. Rebuild: cd ~/clawd/mission-control && npm run build
# 14. Restart: systemctl --user restart mission-control.service
```

**Packages to install:** None.
**Packages to remove:** None.
**Docker images to build:** None.
**New agents to configure:** None.

---

## Version Compatibility

| Package | Version | Already Installed | Notes |
|---------|---------|-------------------|-------|
| better-sqlite3 | 12.6.2 | Yes | Opens yolo.db same as 5 existing DBs |
| SWR | 2.3.3 | Yes | Polls /api/yolo/builds |
| Next.js | 14.2.15 | Yes | /yolo page route |
| shadcn/ui | Latest | Yes | Card, Badge, Table for build display |
| Recharts | 3.7.0 | Yes | Build frequency chart |
| date-fns | 3.6.0 | Yes | "2 days ago" timestamps |
| Python 3 | 3.11 | Yes (in sandbox) | Prototype runtime |
| sqlite3 CLI | Debian 12 compat | Yes (bind-mounted) | yolo.db writes from sandbox |
| cron-parser | 5.x | Yes | Calendar page shows yolo-build cron |

---

## Sources

### HIGH confidence
- [OpenClaw Sandboxing Docs](https://docs.openclaw.ai/gateway/sandboxing) -- sandbox configuration, bind-mounts, default tools, setupCommand
- [OpenClaw Agent Workspace Docs](https://docs.openclaw.ai/concepts/agent-workspace) -- workspace file access, writable paths
- Phase 6 Summary (project internal) -- sqlite3 glibc compatibility fix, bind-mount patterns
- Phase 29 Research (project internal) -- better-sqlite3 singleton pattern, DB_PATHS registry, WAL mode
- PROJECT.md (project internal) -- existing 5 databases, 13 skills, 20 crons, sandbox architecture
- MEMORY.md (project internal) -- sandbox details, bind-mount patterns, Docker image `clawdbot-sandbox:with-browser`

### MEDIUM confidence
- [Docker Blog: OpenClaw Sandbox Security](https://www.docker.com/blog/run-openclaw-securely-in-docker-sandboxes/) -- sandbox image contents, security considerations
- [OpenClaw GitHub: Dockerfile.sandbox](https://github.com/openclaw/openclaw/blob/main/Dockerfile.sandbox) -- default sandbox image includes python3, bash, curl, git, jq, ripgrep
- [Ralph Wiggum Pattern for Autonomous Builds](https://beyond.addy.ie/2026-trends/) -- autonomous loop patterns, guardrails, iteration limits

### LOW confidence
- None. All recommendations are based on existing validated patterns in this project.

---

*Stack research for: pops-claw v2.7 YOLO Dev -- overnight autonomous builder*
*Researched: 2026-02-24*
*Replaces: previous STACK.md covering v2.5 Mission Control Dashboard stack*
