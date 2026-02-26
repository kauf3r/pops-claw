# Phase 39: Build Pipeline - Research

**Researched:** 2026-02-24
**Domain:** OpenClaw cron job, workspace protocol docs, skill design, autonomous code generation guardrails
**Confidence:** HIGH

## Summary

Phase 39 builds the complete autonomous build pipeline: a nightly cron triggers Bob to generate ideas, pick one, build a prototype, self-evaluate, log everything to yolo.db, and write human-readable artifacts. Every component maps to a proven pattern already running in production. The cron follows the same schema as 20+ existing crons. The workspace protocol docs (YOLO_BUILD.md, YOLO_INTERESTS.md) follow the exact CONTENT_TRIGGERS.md and DAILY_FLUSH.md patterns. DB access uses Python sqlite3 (confirmed working in Phase 38-02 sandbox validation). Build artifacts go to /workspace/yolo-dev/{NNN}-{slug}/ (validated by 000-test/ and 001-chronicle/).

The critical design challenge is the YOLO_BUILD.md reference doc itself -- it is the single document that defines Bob's entire behavior during overnight builds. It must encode: idea generation from YOLO_INTERESTS.md, candidate logging to ideas.md, build constraints (Python stdlib + vanilla HTML/JS, 100-500 LOC, 2-6 files), status tracking through the full lifecycle in yolo.db via Python sqlite3, self-evaluation with 1-5 scoring, POSTMORTEM.md on failure, and all hard guardrails. This is a prompt engineering exercise, not an infrastructure one.

The second critical finding is a **schedule collision**: the daily-memory-flush cron already fires at 11 PM PT (Sonnet, isolated). The YOLO build cron must be offset -- 11:30 PM PT or later -- to avoid contention. Haiku model selection (per BUILD-01) means the YOLO build uses a different rate pool than the Sonnet memory-flush, but concurrent isolated sessions on a 2GB RAM EC2 still risk memory pressure.

**Primary recommendation:** Create three artifacts on EC2: YOLO_BUILD.md (build protocol), YOLO_INTERESTS.md (idea seeds), and the cron job entry. Use the `openclaw cron add` CLI to register the cron (not manual jobs.json editing). Validate with a manual `openclaw cron run` trigger before relying on the nightly schedule.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUILD-01 | Nightly cron job triggers Bob to execute an overnight build (isolated session, ~11 PM PT, Haiku model to avoid rate limit contention) | Cron schema documented from 20+ existing examples. Schedule offset to 11:30 PM PT to avoid daily-memory-flush collision at 11 PM. Haiku model selection confirmed as separate rate pool. Use `openclaw cron add` CLI. |
| BUILD-02 | YOLO_BUILD.md workspace reference doc defines the full build protocol -- idea generation, execution, logging, evaluation | Workspace protocol doc pattern proven (CONTENT_TRIGGERS.md, DAILY_FLUSH.md, MEETING_PREP.md). Must include Python sqlite3 code snippets for DB operations (sandbox constraint from Phase 38-02). |
| BUILD-03 | Bob generates 3-5 project ideas informed by personal context (interests, recent voice notes, projects, skills), picks the best with reasoning, logs candidates to ideas.md | Idea generation instructions embedded in YOLO_BUILD.md. ideas.md written per-build in the build directory. Context sources: YOLO_INTERESTS.md (primary), coordination.db tasks, recent voice_notes. |
| BUILD-04 | YOLO_INTERESTS.md workspace protocol doc seeds idea generation with Andy's domains, technologies, and project types -- editable anytime | Same workspace doc pattern as CONTENT_TRIGGERS.md. Placed at ~/clawd/agents/main/YOLO_INTERESTS.md. Needs initial population with Andy's domains/interests. |
| BUILD-05 | Bob builds a working prototype using Python stdlib + vanilla HTML/JS as default stack, constrained to 100-500 LOC and 2-6 files | Stack constraint enforced in YOLO_BUILD.md instructions. Python stdlib + http.server for serving HTML. No pip/npm installs. Build directory: /workspace/yolo-dev/{NNN}-{slug}/. LOC and file counts logged to yolo.db. |
| BUILD-06 | Build status tracked in yolo.db with enum: idea -> building -> testing -> success/partial/failed | Status updates via Python sqlite3 UPDATE statements at each lifecycle stage. Schema CHECK constraint already enforces valid statuses (Phase 38-01). YOLO_BUILD.md includes exact SQL snippets. |
| BUILD-07 | Bob self-evaluates each build on a 1-5 scale with reasoning | Self-evaluation section in YOLO_BUILD.md with rubric: 1=broken, 2=runs with errors, 3=works but rough, 4=solid prototype, 5=impressive. Score and reasoning logged to yolo.db self_score + self_evaluation columns. |
| BUILD-08 | On failure or partial build, Bob writes POSTMORTEM.md explaining what was attempted, where it broke, and what would fix it | YOLO_BUILD.md includes POSTMORTEM.md template with sections: What Was Attempted, Where It Broke, Root Cause, What Would Fix It. Written in the build directory alongside ideas.md and README.md. |
| BUILD-09 | Hard guardrails: 15-turn cap, 30-minute timeout, no pip/npm installs outside /workspace/, tech stack variety (no same stack 3x in a row) | Turn cap via cron `maxTurns` config (if supported) or enforced in YOLO_BUILD.md instructions. Timeout via cron `timeoutSeconds: 1800`. Tech stack variety checked by querying last 2 builds from yolo.db before idea selection. No installs enforced by sandbox read-only FS + explicit instruction. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| OpenClaw cron system | v2026.2.17 | Nightly trigger | 20+ crons running in production, exact same JSON schema |
| Workspace protocol docs | N/A | Build instructions + interests | Proven pattern: CONTENT_TRIGGERS.md, DAILY_FLUSH.md, MEETING_PREP.md |
| Python sqlite3 module | Python 3.x (sandbox) | yolo.db read/write from sandbox | Confirmed working in Phase 38-02 (CLI sqlite3 unavailable in sandbox) |
| openclaw cron add CLI | v2026.2.17 | Register cron job | Used for daily-memory-flush (Phase 34-02). Avoids manual jobs.json editing |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| openclaw cron run | Manual trigger for testing | After creating cron, before relying on nightly schedule |
| openclaw cron list | Verify cron registered | After `cron add`, confirm entry visible |
| Python http.server | Serve HTML prototypes | When builds produce index.html (built-in, no install needed) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openclaw cron add | Manual jobs.json edit | CLI is safer but requires knowing exact flags. Manual edit risks JSON syntax errors. CLI preferred |
| Python sqlite3 | sqlite3 CLI | CLI not available in sandbox (Phase 38-02 discovery). Python sqlite3 is the only path |
| YOLO_BUILD.md as reference doc | Skill SKILL.md | Skills are for DM-triggered behaviors. Cron-triggered protocols use workspace reference docs (established pattern) |

## Architecture Patterns

### Cron Job Schema (from existing production examples)
```json
{
  "id": "<generate-uuid>",
  "agentId": "main",
  "name": "yolo-dev-overnight",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "30 7 * * *",
    "tz": "America/Los_Angeles"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "model": "haiku",
  "timeoutSeconds": 1800,
  "payload": {
    "kind": "systemEvent",
    "text": "Read /workspace/yolo-dev/YOLO_BUILD.md and follow its instructions to execute tonight's autonomous build."
  },
  "note": "Schedule: 11:30 PM PT (07:30 UTC). Created YYYY-MM-DD."
}
```

**Key design decisions:**
- `schedule.expr`: `30 7 * * *` UTC = 11:30 PM PT. Offset from daily-memory-flush (11 PM PT = `0 7 * * *` UTC). The 30-minute gap lets memory flush complete before YOLO build starts.
- `sessionTarget`: `isolated` -- clean context per build, no session bleed
- `model`: `haiku` -- separate rate pool from Sonnet, sufficient for Python/HTML prototypes (per BUILD-01)
- `timeoutSeconds`: `1800` (30 min) -- hard wall-clock timeout (per BUILD-09)
- `payload.text`: Points to `/workspace/yolo-dev/YOLO_BUILD.md` (sandbox path, not host path) because isolated sessions run in Docker sandbox

**IMPORTANT:** The payload references `/workspace/yolo-dev/YOLO_BUILD.md` -- this means YOLO_BUILD.md must be placed in `~/clawd/yolo-dev/` on the host (bind-mounted to /workspace/yolo-dev/). NOT in `~/clawd/agents/main/` like other workspace docs.

### Workspace Protocol Doc Pattern

Established by MEETING_PREP.md, CONTENT_TRIGGERS.md, DAILY_FLUSH.md, SECURECLAW_EXCEPTIONS.md:

1. Cron fires with short `systemEvent` text pointing to the reference doc
2. Bob reads the reference doc for full instructions
3. Reference doc contains: purpose, step-by-step protocol, data access patterns (SQL snippets), output format, constraints
4. Reference doc is editable without re-registering the cron

For YOLO Dev, two reference docs:
- **YOLO_BUILD.md** at `~/clawd/yolo-dev/YOLO_BUILD.md` -- the build protocol (read by cron)
- **YOLO_INTERESTS.md** at `~/clawd/yolo-dev/YOLO_INTERESTS.md` -- idea seeds (read by YOLO_BUILD.md instructions)

Both in yolo-dev/ directory so they're accessible via the existing bind-mount. No additional bind-mounts needed.

### Build Lifecycle Flow
```
Cron fires (11:30 PM PT)
  |-> Bob reads YOLO_BUILD.md
  |-> Step 1: Check guardrails
  |     - Query last 2 builds tech_stack from yolo.db (variety check)
  |     - Memory/disk pre-checks (optional, defensive)
  |-> Step 2: Generate ideas
  |     - Read YOLO_INTERESTS.md for domains/interests
  |     - Generate 3-5 candidates with brief descriptions
  |     - Pick one with reasoning
  |-> Step 3: Initialize build
  |     - Query MAX(id) from yolo.db for next build number
  |     - Create /workspace/yolo-dev/{NNN}-{slug}/
  |     - Write ideas.md with all candidates + selection reasoning
  |     - INSERT into yolo.db with status='idea'
  |     - UPDATE status='building'
  |-> Step 4: Build prototype
  |     - Write code files (Python + HTML/JS as needed)
  |     - Stay within 100-500 LOC, 2-6 files
  |     - Write README.md as you go
  |-> Step 5: Test
  |     - UPDATE status='testing'
  |     - Run the code (python3 script.py, check exit code)
  |     - Capture stdout/stderr
  |-> Step 6: Evaluate
  |     - Self-score 1-5 with reasoning
  |     - Determine final status: success/partial/failed
  |     - If failed/partial: write POSTMORTEM.md
  |-> Step 7: Log to yolo.db
  |     - UPDATE with final status, self_score, self_evaluation,
  |       lines_of_code, files_created, tech_stack, build_log,
  |       error_log, completed_at, duration_seconds
  |-> Done
```

### Python sqlite3 DB Access Pattern (from Phase 38-02 validation)
```python
import sqlite3
import os
from datetime import datetime

DB_PATH = '/workspace/yolo-dev/yolo.db'

def db_execute(sql, params=None):
    """Execute SQL and return results."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    results = cur.fetchall()
    conn.commit()
    conn.close()
    return results

# Get next build number
rows = db_execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM builds")
next_id = rows[0]['next_id']

# Insert new build
db_execute("""
    INSERT INTO builds (date, slug, name, description, status, started_at)
    VALUES (?, ?, ?, ?, 'idea', ?)
""", (datetime.now().strftime('%Y-%m-%d'), slug, name, desc,
      datetime.now().isoformat()))

# Update status
db_execute("UPDATE builds SET status=? WHERE id=?", ('building', build_id))

# Final update
db_execute("""
    UPDATE builds SET
        status=?, tech_stack=?, lines_of_code=?, files_created=?,
        self_score=?, self_evaluation=?, build_log=?, error_log=?,
        completed_at=?, duration_seconds=?
    WHERE id=?
""", (status, tech_stack, loc, file_count, score, evaluation,
      build_log, error_log, datetime.now().isoformat(),
      duration, build_id))

# Check last 2 builds for tech stack variety
rows = db_execute("""
    SELECT tech_stack FROM builds
    WHERE status IN ('success', 'partial')
    ORDER BY id DESC LIMIT 2
""")
```

### Build Directory Structure
```
/workspace/yolo-dev/
  YOLO_BUILD.md              # Build protocol (cron reads this)
  YOLO_INTERESTS.md          # Idea seeds (YOLO_BUILD.md reads this)
  yolo.db                    # Build metadata (Phase 38)
  000-test/                  # Smoke test marker (Phase 38)
    README.md
  001-chronicle/             # First build (already exists)
    chronicle.py
  002-{slug}/                # Next build
    ideas.md
    README.md
    main.py (or equivalent)
    index.html (if applicable)
    POSTMORTEM.md (if failed/partial)
```

### Anti-Patterns to Avoid
- **Embedding full build instructions in cron payload text:** Cron payloads have practical length limits and aren't editable without re-registering. Use a reference doc instead (established pattern).
- **Using skill SKILL.md for cron-triggered behavior:** Skills are DM-triggered. Cron-triggered protocols use workspace reference docs. Mixing them creates confusion about when the behavior activates.
- **Writing yolo.db with sqlite3 CLI from sandbox:** Phase 38-02 confirmed sqlite3 CLI is unavailable inside the Docker sandbox. Must use Python sqlite3 module.
- **Placing YOLO_BUILD.md in ~/clawd/agents/main/:** The cron runs in an isolated sandbox session. Only bind-mounted paths are accessible. ~/clawd/yolo-dev/ is bind-mounted; ~/clawd/agents/main/ is the default workspace but not the cron sandbox workspace.
- **Using Sonnet model for overnight builds:** Burns through the rate limit pool shared with daytime crons. Haiku has a separate pool and is sufficient for small prototypes.
- **Scheduling at exactly 11 PM PT:** Collides with daily-memory-flush cron. Offset by 30 minutes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron job registration | Manual JSON editing of jobs.json | `openclaw cron add` CLI | CLI handles UUID generation, validation, and atomic file writes. Manual editing risks JSON syntax errors |
| Build number generation | Directory scanning (ls + count) | DB query `MAX(id) + 1` | DB is the single source of truth (Phase 38 CONTEXT decision). Directory scanning would break on deleted builds |
| DB operations in sandbox | sqlite3 CLI, better-sqlite3, custom HTTP API | Python sqlite3 module | Only viable DB access path from inside Docker sandbox (Phase 38-02 discovery) |
| Tech stack variety check | File-based tracking or memory | SQL query against yolo.db `ORDER BY id DESC LIMIT 2` | DB already stores tech_stack. One query replaces any custom tracking mechanism |
| Build timeout enforcement | Custom timer script in YOLO_BUILD.md | Cron `timeoutSeconds: 1800` | OpenClaw cron system handles timeouts natively. Session killed after 30 minutes |

**Key insight:** Phase 39 is almost entirely prompt engineering (YOLO_BUILD.md) plus one cron registration command. The infrastructure exists. The challenge is writing instructions clear enough that Haiku can follow them autonomously at midnight.

## Common Pitfalls

### Pitfall 1: YOLO_BUILD.md Located in Wrong Directory
**What goes wrong:** Build protocol doc placed at ~/clawd/agents/main/YOLO_BUILD.md (like other workspace docs). Cron fires, Bob can't find the file. The isolated sandbox session only sees bind-mounted paths.
**Why it happens:** All previous workspace protocol docs (MEETING_PREP.md, DAILY_FLUSH.md, CONTENT_TRIGGERS.md) are at ~/clawd/agents/main/ because those crons use the "main" sessionTarget. The YOLO cron uses "isolated" sessionTarget, which runs in Docker sandbox where only bind-mounted paths are visible.
**How to avoid:** Place YOLO_BUILD.md and YOLO_INTERESTS.md inside ~/clawd/yolo-dev/ (which maps to /workspace/yolo-dev/ in sandbox). Reference as /workspace/yolo-dev/YOLO_BUILD.md in the cron payload.
**Warning signs:** Cron fires but Bob reports "file not found" or produces no build output.

### Pitfall 2: Schedule Collision with daily-memory-flush
**What goes wrong:** YOLO cron fires at 11 PM PT. The daily-memory-flush cron also fires at 11 PM PT (registered in Phase 34-02). Both are isolated sessions on a 2GB RAM EC2. Memory pressure from two concurrent sessions causes slow performance or OOM.
**Why it happens:** The Phase 39 requirements say "~11 PM PT" without noting the existing cron at that exact time.
**How to avoid:** Schedule YOLO build at 11:30 PM PT (07:30 UTC). The daily-memory-flush typically completes in under 5 minutes (Sonnet, simple DB queries), so 30 minutes is a conservative gap.
**Warning signs:** Both crons running simultaneously visible in `openclaw sessions`. High memory usage during 11 PM-midnight window.

### Pitfall 3: Haiku Fails to Follow Complex Build Instructions
**What goes wrong:** YOLO_BUILD.md contains a multi-step protocol (idea generation, DB operations, file creation, testing, evaluation, logging). Haiku, being a smaller model, skips steps, misformats SQL, or produces incomplete prototypes.
**Why it happens:** Haiku is optimized for speed and cost, not complex multi-step reasoning. The build protocol has 7 stages with conditional logic (POSTMORTEM.md only on failure, tech variety check requiring SQL query and comparison).
**How to avoid:** Keep YOLO_BUILD.md instructions extremely explicit and linear. Provide exact SQL snippets (not "write SQL to..."). Include Python code templates for DB operations. Minimize branching logic. Test with a manual `openclaw cron run` before the first nightly trigger. If Haiku consistently fails after 3-5 attempts, escalate to Sonnet with tighter turn limits.
**Warning signs:** First few builds have status='failed' with error logs showing SQL syntax errors or missing files.

### Pitfall 4: Build Number Mismatch Between DB and Directory
**What goes wrong:** 001-chronicle already exists as a manually created build (from the initial YOLO prototype test). The next cron-triggered build queries MAX(id)=0 from yolo.db (no rows for 001-chronicle) and creates 001-{slug}/, colliding with the existing directory.
**Why it happens:** 001-chronicle was created before the yolo.db infrastructure existed (Phase 38). It's a directory-only artifact with no corresponding DB row.
**How to avoid:** Seed yolo.db with a row for 001-chronicle before the first cron run. Or accept that the first automated build will be 001-{slug} and rename 001-chronicle to be the DB-tracked build #1 by inserting its metadata. The simplest approach: insert a row for 001-chronicle into yolo.db during this phase's setup.
**Warning signs:** Directory already exists error when Bob tries to mkdir.

### Pitfall 5: Isolated Session Can't Read Personal Context
**What goes wrong:** BUILD-03 requires ideas "informed by personal context (interests, recent voice notes, projects, skills)." An isolated sandbox session only sees bind-mounted paths. coordination.db and voice_notes data are at /workspace/coordination.db (bind-mounted rw), but other context (AGENTS.md, LEARNINGS.md at ~/clawd/) may not be accessible.
**Why it happens:** Isolated sessions run in Docker sandbox with limited filesystem access. Only paths in the openclaw.json binds array are visible.
**How to avoid:** YOLO_INTERESTS.md serves as the primary context source (it's in the bind-mounted yolo-dev/ directory). For richer context, YOLO_BUILD.md can instruct Bob to query coordination.db (bind-mounted at /workspace/coordination.db:rw) for recent tasks and voice_notes table for recent transcripts. These are already accessible. Don't rely on files that aren't bind-mounted.
**Warning signs:** Bob generates generic ideas instead of personalized ones.

### Pitfall 6: Python sqlite3 Connection Left Open After Crash
**What goes wrong:** If the build session times out (30-minute hard limit) mid-write, a Python sqlite3 connection may be left in a bad state. Next build attempt gets "database is locked."
**Why it happens:** Python sqlite3 without explicit close() or context manager leaves WAL locks. Container reset between sessions should clear this, but the file is on a bind-mounted host directory.
**How to avoid:** YOLO_BUILD.md should use `with sqlite3.connect(DB_PATH) as conn:` context manager pattern in all code snippets. Also, the DB uses DELETE journal mode (not WAL), so lock cleanup is simpler. If locked, a new connection attempt after container restart will succeed.
**Warning signs:** "database is locked" errors in build_log.

## Code Examples

### Cron Registration Command
```bash
# Generate UUID for cron ID
CRON_UUID=$(python3 -c "import uuid; print(str(uuid.uuid4()))")

# Register via CLI (confirmed working pattern from Phase 34-02)
/home/ubuntu/.npm-global/bin/openclaw cron add \
  --name "yolo-dev-overnight" \
  --cron "30 7 * * *" \
  --agent main \
  --session isolated \
  --model haiku \
  --timeout 1800 \
  --message "Read /workspace/yolo-dev/YOLO_BUILD.md and follow its instructions to execute tonight's autonomous build."

# Verify
/home/ubuntu/.npm-global/bin/openclaw cron list | grep yolo-dev
```

**Note:** The exact `openclaw cron add` flags should be verified at execution time. Phase 34-02 used `--cron` for the schedule expression. If flags have changed in v2026.2.17, use `openclaw cron add --help` to confirm.

### YOLO_BUILD.md Structure (outline)
```markdown
# YOLO Build Protocol

You are executing an autonomous overnight build. Follow these steps exactly.

## Step 0: Pre-Flight Checks
[Check disk space, query last 2 builds for tech variety]

## Step 1: Generate Ideas
[Read YOLO_INTERESTS.md, generate 3-5 candidates, pick one]

## Step 2: Initialize Build
[Get next build number from yolo.db, create directory, write ideas.md, INSERT into DB]

## Step 3: Build Prototype
[Write code, stay within constraints, write README.md]

## Step 4: Test
[Run the code, capture output, verify it works]

## Step 5: Evaluate
[Self-score 1-5, determine final status]

## Step 6: Log Results
[UPDATE yolo.db with all metadata]

## Step 7: Handle Failure (if applicable)
[Write POSTMORTEM.md]

## Constraints
- Python stdlib + vanilla HTML/CSS/JS only
- 100-500 lines of code
- 2-6 files maximum
- No pip install, no npm install
- Build directory: /workspace/yolo-dev/{NNN}-{slug}/

## DB Access (Python sqlite3)
[Exact code snippets for all DB operations]
```

### YOLO_INTERESTS.md Structure (outline)
```markdown
# Andy's YOLO Interests

## Domains
- Personal productivity & automation
- Data visualization
- Developer tools & CLI utilities
- Smart home / IoT
- Music & audio
- Fitness & health tracking
- Writing & content creation

## Technologies I Like
- Python (stdlib focus)
- HTML/CSS/JS (vanilla, no frameworks)
- SQLite
- APIs & data mashups
- Terminal/CLI interfaces

## Recent Context
(Updated periodically -- check coordination.db and voice_notes for recent interests)

## Ideas I'd Love to See Built
- [Starter ideas seeded here]

## Avoid
- Heavy frameworks (React, Django, Flask)
- Anything requiring API keys not in the sandbox
- Games that need graphics libraries
```

### Seeding 001-chronicle into yolo.db
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.execute("""
    INSERT INTO builds (date, slug, name, description, status, tech_stack,
                       lines_of_code, files_created, self_score, self_evaluation,
                       started_at, completed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    '2026-02-24', 'chronicle', 'Chronicle',
    'Turn any git repo history into a visual narrative HTML page',
    'success', 'python,html,css,javascript',
    528, 1, 4,
    'Working prototype that analyzes git repos and generates a beautiful HTML dashboard with heatmap, timeline, and stats. Single Python file generates self-contained HTML.',
    '2026-02-24T00:00:00', '2026-02-24T00:30:00'
))
conn.commit()
conn.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Skill SKILL.md for all agent behaviors | Workspace protocol docs for cron-triggered behaviors | v2.5-v2.6 (CONTENT_TRIGGERS.md, DAILY_FLUSH.md) | Cron instructions live in reference docs, not skills. Skills are DM-triggered |
| Manual jobs.json editing | openclaw cron add CLI | v2.6 (Phase 34-02) | Safer registration, handles UUID and validation |
| sqlite3 CLI for DB access in sandbox | Python sqlite3 module | Phase 38-02 (2026-02-24) | CLI binary not available in Docker sandbox. Python is the confirmed path |
| All workspace docs in ~/clawd/agents/main/ | Docs alongside data in feature-specific directories | Phase 38 (yolo-dev/) | YOLO_BUILD.md lives with yolo.db and build artifacts, not in the generic agents workspace |

## Open Questions

1. **Exact `openclaw cron add` flags for model and timeout**
   - What we know: Phase 34-02 used the CLI successfully. The `--cron` flag sets the schedule expression.
   - What's unclear: Whether `--model haiku` and `--timeout 1800` are the exact flag names. The cron schema has `model` and `timeoutSeconds` fields.
   - Recommendation: Run `openclaw cron add --help` on EC2 at execution time. If the flags aren't supported, fall back to manual jobs.json editing with jq (Phase 38-01 pattern).

2. **Whether isolated sessions have access to /workspace/coordination.db**
   - What we know: coordination.db is bind-mounted at `/workspace/coordination.db:rw` in the global sandbox config. Isolated sessions should inherit all bind-mounts.
   - What's unclear: Whether "isolated" means a different Docker config or just a fresh session on the same sandbox.
   - Recommendation: Verify during manual cron test by querying coordination.db from the isolated session. If not accessible, YOLO_INTERESTS.md alone is sufficient for idea generation (all context is pre-seeded there).

3. **YOLO_INTERESTS.md initial content**
   - What we know: The doc needs Andy's actual interests, domains, and technologies.
   - What's unclear: Exact list of interests (this requires human input).
   - Recommendation: Populate with reasonable defaults based on project history (automation, developer tools, data viz, health tracking, productivity). Andy can edit anytime to steer direction.

4. **001-chronicle DB reconciliation**
   - What we know: 001-chronicle/ exists as a directory but has no yolo.db row. The next automated build will query MAX(id)+1 and get 1, creating a build number collision.
   - What's unclear: Whether to backfill 001-chronicle into yolo.db or renumber it.
   - Recommendation: Insert a row for 001-chronicle into yolo.db during setup. It's a real build, it should be tracked. This makes the next automated build #2.

5. **Haiku code quality for prototypes**
   - What we know: Requirements specify Haiku. Research recommends it for rate limit safety.
   - What's unclear: Whether Haiku can reliably produce working 100-500 LOC Python prototypes with correct sqlite3 operations.
   - Recommendation: Run the first 3-5 builds on Haiku. Track self_score and status. If >50% fail with code quality issues (not idea quality), escalate to Sonnet with a 10-turn limit.

## Sources

### Primary (HIGH confidence)
- Phase 38-01 SUMMARY: yolo.db schema, bind-mount config, openclaw.json structure
- Phase 38-02 SUMMARY: Python sqlite3 is the confirmed sandbox DB access path (not CLI sqlite3, not better-sqlite3)
- Phase 34-02 SUMMARY: daily-memory-flush cron at 11 PM PT, `openclaw cron add` CLI pattern
- Phase 09-01 cron evidence: Meeting prep cron schema (systemEvent + reference doc pattern)
- Phase 09-02 cron reference: Anomaly check cron JSON schema example
- Phase 25 cron audit: Full list of 20 production crons with schedules
- Phase 14-02 PLAN: Cron configuration with sessionTarget, model, timeout patterns
- REQUIREMENTS.md: BUILD-01 through BUILD-09 exact requirement text
- ROADMAP.md: Phase 39 success criteria
- Research SUMMARY.md: Stack decisions, pitfall analysis, phase structure
- Research FEATURES.md: Feature prioritization, anti-features, dependency graph

### Secondary (MEDIUM confidence)
- Research PITFALLS.md: OOM, rate limit, disk, and debug-loop failure modes
- 001-chronicle source code: Existing build artifact showing what a successful build looks like (528 LOC Python + embedded HTML)
- MEMORY.md: Cron configuration patterns, sandbox architecture, lesson learned about workspace protocol docs

### Tertiary (LOW confidence -- verify at execution)
- openclaw cron add exact flags (verify with --help)
- Isolated session access to coordination.db (verify during manual test)
- Haiku code quality for autonomous prototypes (empirical, first 3-5 builds)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- every component (cron, reference doc, Python sqlite3, bind-mount) is proven and in production
- Architecture: HIGH -- follows exact patterns from 6 previous milestones, every design decision has precedent
- Pitfalls: HIGH -- schedule collision identified from live cron audit data, sandbox limitations confirmed from Phase 38-02

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (cron patterns and sandbox architecture are stable)
