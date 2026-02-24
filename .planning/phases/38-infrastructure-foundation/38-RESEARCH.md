# Phase 38: Infrastructure Foundation - Research

**Researched:** 2026-02-24
**Domain:** SQLite database creation, Docker bind-mounts, OpenClaw sandbox config
**Confidence:** HIGH

## Summary

Phase 38 is a pure infrastructure provisioning phase: create a SQLite database, a host directory, configure a bind-mount in openclaw.json, restart the gateway once, and validate everything works from inside the Docker sandbox. No application logic, no cron jobs, no UI.

The existing codebase has 5 precedent databases and 9 existing bind-mounts in openclaw.json. The pattern is well-established and documented. The key difference is that this phase mounts a **directory** (not individual files), which is simpler than the existing file-level mounts. The main risks are: (1) forgetting to create yolo.db before the bind-mount goes live, (2) file permission mismatches between host and container, and (3) the gateway restart disrupting active sessions.

**Primary recommendation:** Follow the exact existing bind-mount pattern (host ubuntu:ubuntu 644 files, Docker user 1000:1000), create everything on the host first, edit openclaw.json once, restart gateway once, then validate layer by layer.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Auto-increment integer primary key (id maps directly to build number 001, 002...)
- Status stored as TEXT with CHECK constraint: idea, building, testing, success, partial, failed
- self_score as INTEGER with CHECK(self_score BETWEEN 1 AND 5)
- created_at column with DEFAULT CURRENT_TIMESTAMP
- Composite index on (status, date) for dashboard filtering/sorting
- All columns per INFRA-01: id, date, slug, name, description, status, tech_stack, lines_of_code, files_created, self_score, self_evaluation, build_log, error_log, started_at, completed_at, duration_seconds
- 3-digit zero-padded (001, 002, ..., 999) for directory names
- Slug format: lowercase, hyphens, max 30 characters, strip special chars
- Example: 001-weather-dashboard-app/
- Next number determined by querying yolo.db MAX(id) + 1 (DB is single source of truth, no directory scanning)
- Minimum files per build directory: README.md + ideas.md (POSTMORTEM.md only on failure, added in Phase 39)
- Single new mount: ~/clawd/yolo-dev/ to /workspace/yolo-dev/ (read-write)
- yolo.db lives inside yolo-dev/ at ~/clawd/yolo-dev/yolo.db
- Standard rw permissions matching existing sandbox mounts, same UID mapping
- Phase 38 only adds yolo-dev/ mount (protocol docs mounted in Phase 39)
- Verification: Bob creates 000-test/ with README.md from inside sandbox as smoke test (keep as marker)
- Batch into single gateway restart: openclaw.json bind-mount config + yolo.db creation + directory setup
- Backup openclaw.json to openclaw.json.bak-20260224 before editing
- Validation order after restart: service status, mount check, DB write test, sandbox test (Bob creates 000-test/)

### Claude's Discretion
- Exact column types for text fields (TEXT vs VARCHAR -- SQLite is flexible)
- Index naming conventions
- Backup file naming format details
- Any additional SQLite pragmas (WAL mode, etc.)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | yolo.db SQLite database created at ~/clawd/yolo-dev/yolo.db with builds table (id, date, slug, name, description, status, tech_stack, lines_of_code, files_created, self_score, self_evaluation, build_log, error_log, started_at, completed_at, duration_seconds) | Schema section provides exact CREATE TABLE + CREATE INDEX DDL. Column types researched. sqlite3 CLI available on host and in sandbox. |
| INFRA-02 | ~/clawd/yolo-dev/ directory created with bind-mount in openclaw.json sandbox config mapping to /workspace/yolo-dev/ | Bind-mount pattern documented from 9 existing mounts. Directory mount syntax confirmed. UID mapping verified (host ubuntu=1000, container user=1000:1000). |
| INFRA-03 | Build artifacts stored in ~/clawd/yolo-dev/{NNN}-{slug}/ with sequential numbering and README.md per build | Numbering derived from DB id (MAX(id)+1). 000-test/ smoke test validates directory creation from sandbox. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| sqlite3 | 3.45.1 | Database creation and DDL on host | Already installed at /usr/bin/sqlite3 on EC2 |
| sqlite3-compat | (bind-mounted) | DB access from inside Docker sandbox | Already bind-mounted at /usr/bin/sqlite3:ro in sandbox |
| openclaw.json | N/A | Sandbox bind-mount configuration | Single config file for all Docker sandbox settings |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| systemctl --user | Gateway restart | After openclaw.json changes |
| jq | JSON validation of openclaw.json | Before restart, to catch syntax errors |

### Alternatives Considered
None -- this is infrastructure provisioning, not a technology choice.

## Architecture Patterns

### Existing Bind-Mount Pattern in openclaw.json
```json
// File mounts (existing pattern -- 9 entries)
"/home/ubuntu/clawd/coordination.db:/workspace/coordination.db:rw"
"/home/ubuntu/clawd/agents/main/email.db:/workspace/email.db:rw"
"/home/ubuntu/clawd/agents/main/observability.db:/workspace/observability.db:ro"

// Directory mount (new pattern for yolo-dev)
"/home/ubuntu/clawd/yolo-dev/:/workspace/yolo-dev/:rw"
```

**Key difference:** Existing mounts are individual files. The yolo-dev mount is a directory, which is simpler -- Docker mounts the entire directory tree, including yolo.db and any build subdirectories created later.

### Directory Structure on Host (after Phase 38)
```
~/clawd/yolo-dev/              # New directory, bind-mounted
  yolo.db                      # SQLite database
  000-test/                    # Smoke test marker (created by Bob in sandbox)
    README.md
```

### Sandbox View (after Phase 38)
```
/workspace/                    # Existing workspace root
  yolo-dev/                    # New bind-mount (rw)
    yolo.db
    000-test/
      README.md
  coordination.db              # Existing (rw)
  content.db                   # Existing (rw)
  email.db                     # Existing (rw)
  observability.db             # Existing (ro)
```

### Database Schema (DDL)

```sql
-- Recommendation: Use DELETE journal mode (matches existing DBs)
-- All existing project databases use DELETE mode, not WAL.
-- Consistent behavior is more important than WAL performance here.

CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'idea' CHECK(status IN ('idea', 'building', 'testing', 'success', 'partial', 'failed')),
    tech_stack TEXT,
    lines_of_code INTEGER,
    files_created INTEGER,
    self_score INTEGER CHECK(self_score BETWEEN 1 AND 5),
    self_evaluation TEXT,
    build_log TEXT,
    error_log TEXT,
    started_at TEXT,
    completed_at TEXT,
    duration_seconds INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_builds_status_date ON builds(status, date);
```

**Column type rationale (Claude's discretion):**
- All text fields: TEXT (SQLite ignores VARCHAR length anyway, TEXT is idiomatic)
- date, started_at, completed_at, created_at: TEXT (SQLite has no native datetime type; TEXT with ISO 8601 strings is the standard pattern)
- lines_of_code, files_created, duration_seconds: INTEGER
- self_score: INTEGER with CHECK constraint
- id: INTEGER PRIMARY KEY AUTOINCREMENT (ensures monotonically increasing, never-reused IDs)

**Index naming:** `idx_{table}_{columns}` -- matches common SQLite convention.

**Pragmas:** No additional pragmas recommended. DELETE journal mode is the default and matches all 5 existing project databases. WAL mode would be beneficial for concurrent reads (Mission Control dashboard in Phase 40), but introducing a different journal mode creates inconsistency and WAL generates -wal and -shm sidecar files that complicate backups. If needed later, WAL can be enabled per-connection.

### Anti-Patterns to Avoid
- **Mounting yolo.db as a separate file:** Don't. The whole point of the directory mount is that one mount covers both the DB and all build subdirectories. Mounting yolo.db separately would mean two mounts to maintain.
- **Creating yolo.db from inside the sandbox:** Create it on the host first. The sqlite3-compat binary in the sandbox has a version mismatch warning (header vs source version) -- use the host's /usr/bin/sqlite3 for initial creation to avoid issues.
- **Using ROWID instead of AUTOINCREMENT:** Without AUTOINCREMENT, deleted row IDs can be reused. Since build numbers = DB ids and directories like 005-foo/ are permanent, ID reuse would create conflicts. AUTOINCREMENT prevents this.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON editing | Manual string manipulation of openclaw.json | jq or careful text editing with backup | JSON syntax errors brick the gateway |
| DB creation | Python/Node script | sqlite3 CLI one-liner | Host has sqlite3 3.45.1; one command does it |
| Permission fixes | chmod/chown gymnastics | Match existing pattern (ubuntu:ubuntu 644) | Docker user 1000:1000 = host ubuntu:ubuntu |

**Key insight:** This phase is pure ops -- mkdir, sqlite3 DDL, JSON edit, service restart. No custom code needed.

## Common Pitfalls

### Pitfall 1: JSON Syntax Error in openclaw.json
**What goes wrong:** A missing comma, trailing comma, or mismatched bracket in openclaw.json prevents the gateway from starting. The gateway fails silently or with a cryptic parse error.
**Why it happens:** The binds array is deeply nested in agents.defaults.sandbox.docker.binds. Manual editing is error-prone.
**How to avoid:** (1) Backup before editing. (2) Validate with `jq . < openclaw.json > /dev/null` before restarting. (3) Keep the backup so you can instantly rollback.
**Warning signs:** Gateway fails to start after `systemctl --user restart openclaw-gateway`.

### Pitfall 2: yolo.db Not Created Before Gateway Restart
**What goes wrong:** If the bind-mount references ~/clawd/yolo-dev/ but yolo.db doesn't exist yet, the DB path exists but is empty. Bob's sandbox session tries to open /workspace/yolo-dev/yolo.db and gets an empty file or "not a database" error.
**Why it happens:** Ordering error -- editing config before creating the database.
**How to avoid:** Create directory and database FIRST, then edit config, then restart.
**Warning signs:** sqlite3 inside sandbox reports "file is not a database" or "unable to open database".

### Pitfall 3: Permission Denied on Directory Write
**What goes wrong:** Bob's sandbox session can read /workspace/yolo-dev/ but can't create subdirectories or write to yolo.db.
**Why it happens:** The host directory was created as root (e.g., via sudo mkdir) instead of as ubuntu, or with restrictive permissions.
**How to avoid:** Create directory as the ubuntu user (no sudo). Verify ownership is ubuntu:ubuntu (1000:1000) and permissions are 755 for directories, 644 for files. This matches the Docker sandbox user: "1000:1000".
**Warning signs:** "Permission denied" when Bob tries to mkdir or sqlite3 write.

### Pitfall 4: Gateway Restart Disrupts Active Sessions
**What goes wrong:** Restarting the gateway kills all active agent sessions (DMs, cron jobs in progress). After restart, DM sessions must be re-established by the user sending a message.
**Why it happens:** Gateway restart clears DM sessions (documented lesson learned).
**How to avoid:** Restart during a quiet period (no active cron jobs). Check `openclaw sessions` first. Batch ALL config changes into one restart.
**Warning signs:** Cron delivery failures after restart ("Action send requires a target").

### Pitfall 5: sqlite3-compat Version Mismatch in Sandbox
**What goes wrong:** The sqlite3-compat binary in the sandbox reports "SQLite header and source version mismatch" (confirmed: header=2024-01-30, source=2022-12-28). Some operations may behave unexpectedly.
**Why it happens:** The binary was compiled against a different SQLite version than its headers.
**How to avoid:** Use host sqlite3 (3.45.1, clean) for initial DB creation and schema. The sandbox sqlite3-compat works for basic operations (read/write) despite the warning -- just don't use it for schema creation.
**Warning signs:** Version mismatch warning on stderr when running sqlite3 in sandbox.

### Pitfall 6: Disk Space Constraint
**What goes wrong:** EC2 disk is at 81% used (7.4GB free of 38GB). yolo.db itself is tiny but build artifacts accumulate over time.
**Why it happens:** t3.small with 40GB EBS, already hosting Node, Docker images, 5 databases, mission-control, whisper, etc.
**How to avoid:** Phase 38 itself is fine (yolo.db starts at ~12KB). Flag for Phase 39+ that build retention policy should be considered. Each build is small (100-500 LOC, 2-6 files) but 365 builds/year adds up.
**Warning signs:** `df -h` showing >90% usage.

## Code Examples

### Create Directory and Database on Host
```bash
# As ubuntu user (no sudo)
mkdir -p ~/clawd/yolo-dev

# Create database with schema
sqlite3 ~/clawd/yolo-dev/yolo.db <<'SQL'
CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    slug TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'idea' CHECK(status IN ('idea', 'building', 'testing', 'success', 'partial', 'failed')),
    tech_stack TEXT,
    lines_of_code INTEGER,
    files_created INTEGER,
    self_score INTEGER CHECK(self_score BETWEEN 1 AND 5),
    self_evaluation TEXT,
    build_log TEXT,
    error_log TEXT,
    started_at TEXT,
    completed_at TEXT,
    duration_seconds INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_builds_status_date ON builds(status, date);
SQL

# Verify
sqlite3 ~/clawd/yolo-dev/yolo.db ".schema builds"
sqlite3 ~/clawd/yolo-dev/yolo.db ".tables"
ls -la ~/clawd/yolo-dev/yolo.db
# Expected: -rw-r--r-- 1 ubuntu ubuntu ~12288 ... yolo.db
```

### Edit openclaw.json Bind-Mount
```bash
# Backup first
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-20260224

# Add new bind to agents.defaults.sandbox.docker.binds array
# New entry: "/home/ubuntu/clawd/yolo-dev/:/workspace/yolo-dev/:rw"
# Insert after the last existing bind (observability.db line)
```

The binds array currently has 9 entries. Add as the 10th:
```json
{
  "binds": [
    "/home/ubuntu/.config/gogcli:/workspace/.config/gogcli:ro",
    "/usr/local/bin/gog:/usr/local/bin/gog:ro",
    "/home/ubuntu/.config/gh:/home/node/.config/gh:ro",
    "/usr/bin/gh:/usr/bin/gh:ro",
    "/home/ubuntu/clawd/sqlite3-compat:/usr/bin/sqlite3:ro",
    "/home/ubuntu/clawd/coordination.db:/workspace/coordination.db:rw",
    "/home/ubuntu/clawd/content.db:/workspace/content.db:rw",
    "/home/ubuntu/clawd/agents/main/email.db:/workspace/email.db:rw",
    "/home/ubuntu/clawd/agents/main/observability.db:/workspace/observability.db:ro",
    "/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw"
  ]
}
```

### Validate JSON Before Restart
```bash
jq . < ~/.openclaw/openclaw.json > /dev/null && echo "JSON valid" || echo "JSON INVALID"
```

### Gateway Restart
```bash
# Check no active sessions first
/home/ubuntu/.npm-global/bin/openclaw sessions

# Restart
systemctl --user restart openclaw-gateway

# Verify
systemctl --user status openclaw-gateway
# Expected: active (running)
```

### Validation Sequence (Layer by Layer)
```bash
# 1. Service status
systemctl --user status openclaw-gateway | grep "Active:"
# Expected: Active: active (running)

# 2. Host directory exists with DB
ls -la ~/clawd/yolo-dev/yolo.db
# Expected: file exists, ubuntu:ubuntu, ~12KB

# 3. DB schema correct
sqlite3 ~/clawd/yolo-dev/yolo.db ".schema builds"
# Expected: CREATE TABLE with all columns

# 4. DB write test from host
sqlite3 ~/clawd/yolo-dev/yolo.db "INSERT INTO builds (date, slug, name, status) VALUES ('2026-02-24', 'infra-test', 'Infrastructure Test', 'success'); SELECT * FROM builds; DELETE FROM builds WHERE slug='infra-test';"
# Expected: row inserted, displayed, deleted

# 5. Sandbox test: ask Bob to create 000-test/
# Via Slack DM or openclaw CLI, instruct Bob to:
# mkdir -p /workspace/yolo-dev/000-test && echo "# Smoke Test" > /workspace/yolo-dev/000-test/README.md
# Verify on host: ls ~/clawd/yolo-dev/000-test/README.md
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Individual file bind-mounts for each DB | Directory bind-mount for yolo-dev (covers DB + build dirs) | This phase | Simpler config, one mount instead of N |
| Separate health.db path in agents/main/ | All new DBs in ~/clawd/ root or subdirectory | v2.5 trend | Cleaner path structure |

**Note for Phase 40:** Mission Control's `db-paths.ts` will need a new entry for yolo.db at `/home/ubuntu/clawd/yolo-dev/yolo.db`. Not this phase's concern, but the path is established here.

## Open Questions

1. **sqlite3-compat binary reliability**
   - What we know: It reports a version mismatch warning but has been working for existing DB operations in the sandbox.
   - What's unclear: Whether the mismatch causes silent data corruption on write-heavy operations.
   - Recommendation: Use host sqlite3 for schema creation (verified clean). Accept sandbox sqlite3-compat for runtime reads/writes (proven working for 5 existing DBs). LOW risk.

2. **Trailing slash on directory bind-mount**
   - What we know: Docker bind-mount syntax works with or without trailing slashes on directory paths.
   - What's unclear: Whether OpenClaw's config parser handles trailing slashes identically to Docker.
   - Recommendation: Omit trailing slashes to match the most common Docker convention. The existing file mounts don't use trailing slashes.

## Sources

### Primary (HIGH confidence)
- EC2 live inspection: openclaw.json (full config with 9 existing binds)
- EC2 live inspection: existing DB file permissions (ubuntu:ubuntu 644)
- EC2 live inspection: Docker user config ("user": "1000:1000")
- EC2 live inspection: host ubuntu UID (uid=1000)
- EC2 live inspection: sqlite3 version 3.45.1 on host
- EC2 live inspection: disk usage 81% (7.4GB free)
- EC2 live inspection: existing DBs use DELETE journal mode
- EC2 live inspection: systemd service file for openclaw-gateway
- EC2 live inspection: Mission Control db-paths.ts (5 existing DB entries)

### Secondary (MEDIUM confidence)
- SQLite documentation: AUTOINCREMENT guarantees monotonically increasing, never-reused IDs
- SQLite documentation: CHECK constraints enforce domain constraints at insert/update time
- Docker documentation: directory bind-mounts include entire subtree

### Tertiary (LOW confidence)
- sqlite3-compat version mismatch impact on writes (no issues reported to date, but not formally tested)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools already installed and in use on EC2
- Architecture: HIGH - follows exact pattern of 9 existing bind-mounts and 5 existing databases
- Pitfalls: HIGH - every pitfall identified from live EC2 inspection or documented lessons learned

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (infrastructure patterns are stable)
