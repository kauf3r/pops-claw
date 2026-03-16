# Stack Research: v2.10 Self-Improvement Companion

**Project:** pops-claw — Bob as Self-Improvement Companion
**Researched:** 2026-03-16
**Confidence:** HIGH (existing patterns), MEDIUM (ClawhHub skills — need install/test), LOW (OpenClaw v2026.3.13 upgrade — behavioral changes possible)

---

## Executive Summary

v2.10 adds **one new SQLite database** (`growth.db`) and **2-4 ClawhHub skills**. No new infrastructure, no new agents, no new runtimes. The self-improvement features are built on patterns already proven across 9 milestones: workspace protocol docs for agent behavior, cron jobs for proactive nudges, SQLite for structured data, Oura API for health context, voice notes pipeline for input, and Slack DM for delivery.

The biggest leverage point is **not adding complexity**. ClawhHub has a `habit-flow-skill` (by tralves) with proactive coaching and cron sync, but it introduces its own Node.js scripts and TypeScript dependencies. **Build custom instead** — Bob already has the patterns for habit/goal tracking via workspace protocol docs + cron, same as CONTENT_TRIGGERS.md and VOICE_NOTES_PROTOCOL.md. Custom skills mean zero dependency risk and full control over the data model.

OpenClaw has released v2026.3.12 and v2026.3.13 since the current v2026.3.11. Key features worth upgrading for: `openclaw backup create` (safety net for config changes), Docker timezone override (`OPENCLAW_TZ`), and dashboard v2 (optional — doesn't affect Bob's agent behavior). The upgrade is low-risk but should be batched at milestone start before feature work begins.

---

## What NOT to Change (Working Fine)

| Component | Current State | Why Leave It |
|-----------|--------------|-------------|
| QMD v1.1.0 memory backend | 122 files indexed, search working | Memory system just overhauled in v2.9. Do not touch |
| 7-agent roster | main, landos, rangeos, ops, quill, sage, ezra | Self-improvement features run on `main` agent only |
| 25 cron jobs | All verified | New crons will be added, not replacing existing |
| Voice notes pipeline | Google Drive -> Whisper -> coordination.db | Extend, do not rebuild. Morning commute prompts feed INTO this pipeline |
| Oura skill | Already deployed, health.db working | Read Oura data for weekly reviews; do not change the skill |
| Slack Socket Mode | Working | All self-improvement interactions via Slack DM |
| Mission Control (Next.js 14) | Working at port 3001 | Add growth dashboard page later (Phase 2+), not Phase 1 |
| Docker sandbox / bind-mounts | All 6 DBs bind-mounted | Add growth.db bind-mount to the list |
| Compaction config | softThresholdTokens=8000, reserveTokensFloor=40000 | Tuned in v2.9. Do not touch |

---

## Recommended Stack

### 1. New Database: growth.db (SQLite)

**Why a new database instead of extending coordination.db:** Separation of concerns. coordination.db handles agent-to-agent coordination, task management, and system state. growth.db holds personal growth data (habits, goals, journal entries, mood logs). Different backup cadences, different query patterns, different data lifecycle.

**Schema design:**

```sql
-- Habits: what you track
CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    frequency TEXT NOT NULL DEFAULT 'daily',  -- daily, weekday, weekly, custom
    custom_days TEXT,  -- JSON array of day numbers [1,3,5] for custom
    category TEXT,  -- health, productivity, mindfulness, social, learning
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    archived_at TEXT,  -- soft delete
    streak_best INTEGER DEFAULT 0,
    streak_current INTEGER DEFAULT 0
);

-- Habit completions: when you did it
CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL REFERENCES habits(id),
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    date TEXT NOT NULL,  -- YYYY-MM-DD (one completion per habit per day)
    notes TEXT,  -- optional context
    source TEXT DEFAULT 'slack',  -- slack, voice, cron
    UNIQUE(habit_id, date)
);

-- Goals: OKR-style tracking
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL DEFAULT 'outcome',  -- outcome, keyresult, milestone
    parent_id INTEGER REFERENCES goals(id),  -- key results link to objectives
    target_value REAL,  -- numeric target (e.g., "run 100 miles")
    current_value REAL DEFAULT 0,
    unit TEXT,  -- miles, books, sessions, percent
    status TEXT NOT NULL DEFAULT 'active',  -- active, completed, paused, abandoned
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Goal check-ins: progress updates
CREATE TABLE goal_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id),
    value_delta REAL,  -- how much progress this check-in
    notes TEXT,
    checked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Journal entries: reflections and mood
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- YYYY-MM-DD
    prompt TEXT,  -- what prompt triggered this entry
    content TEXT NOT NULL,
    mood INTEGER,  -- 1-5 scale
    energy INTEGER,  -- 1-5 scale
    tags TEXT,  -- JSON array of tags
    source TEXT DEFAULT 'slack',  -- slack, voice, cron
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Weekly reviews: structured retrospectives
CREATE TABLE weekly_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,  -- YYYY-MM-DD (Monday)
    went_well TEXT,  -- JSON array
    to_improve TEXT,  -- JSON array
    insights TEXT,  -- AI-generated pattern analysis
    oura_summary TEXT,  -- sleep/readiness/HRV patterns for the week
    habit_summary TEXT,  -- completion rates per habit
    goal_summary TEXT,  -- progress snapshot
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(week_start)
);

-- Indexes for common queries
CREATE INDEX idx_habit_completions_date ON habit_completions(date);
CREATE INDEX idx_habit_completions_habit ON habit_completions(habit_id);
CREATE INDEX idx_journal_entries_date ON journal_entries(date);
CREATE INDEX idx_goal_checkins_goal ON goal_checkins(goal_id);
CREATE INDEX idx_goals_status ON goals(status);
```

**Why this schema specifically:**
- `habit_completions` has a UNIQUE(habit_id, date) constraint to prevent double-logging (voice note + manual both register for same day)
- `goals` uses self-referential parent_id for OKR hierarchy (Objectives -> Key Results)
- `journal_entries` stores the prompt that triggered the entry, enabling prompt effectiveness analysis over time
- `weekly_reviews` has dedicated Oura/habit/goal summary columns so the review is self-contained (readable without joining)
- All timestamps in UTC, all dates in YYYY-MM-DD for consistency with existing DBs

**Confidence:** HIGH. Schema follows patterns from coordination.db, content.db, and email.db already in production.

---

### 2. Workspace Protocol Documents (Zero Dependencies)

Following the proven pattern of CONTENT_TRIGGERS.md, VOICE_NOTES_PROTOCOL.md, MEETING_PREP.md, and other workspace protocol docs.

| Document | Location | Purpose |
|----------|----------|---------|
| `HABIT_TRACKER.md` | `~/clawd/agents/main/` | Standing instruction for habit CRUD via Slack DM. Commands: "log exercise", "my habits", "streak report" |
| `GOAL_TRACKER.md` | `~/clawd/agents/main/` | OKR management. Commands: "set goal", "check in [goal]", "goal status" |
| `JOURNAL_PROTOCOL.md` | `~/clawd/agents/main/` | Journal entry handling. Recognizes "journal:", "reflect:", mood/energy keywords |
| `WEEKLY_REVIEW.md` | `~/clawd/agents/main/` | Structured weekly review template. Pulls Oura data, habit stats, goal progress |
| `COMMUTE_PROMPTS.md` | `~/clawd/agents/main/` | Morning commute reflection prompt generation and voice note response handling |

**Why workspace protocol docs over ClawhHub skills:**
1. Bob already loads workspace files on every session startup — zero friction
2. Full control over data model (growth.db schema, query patterns)
3. No external dependencies to break during upgrades
4. Protocol docs can reference Python scripts for DB access (same pattern as content pipeline)
5. ClawhHub skills like `habit-flow-skill` bring their own Node.js scripts + TypeScript — unnecessary complexity for a custom deployment

**Confidence:** HIGH. This pattern is battle-tested across 9 milestones.

---

### 3. New Cron Jobs (4-5 new jobs)

| Cron ID | Schedule | Agent | Delivery | Purpose |
|---------|----------|-------|----------|---------|
| `morning-reflection-prompt` | `0 14 * * 1-5` (7am PT weekdays) | main | dm (Slack) | Deliver 1-2 reflection/discussion prompts for morning commute. Personalized based on yesterday's journal, current goals, recent Oura trends |
| `habit-accountability` | `0 1 * * *` (6pm PT daily) | main | dm (Slack) | End-of-day habit check-in. Lists unlogged habits for today, streak status, gentle nudge |
| `journal-prompt` | `0 23 * * *` (4pm PT daily) | main | dm (Slack) | Afternoon journal prompt. Varies by day: gratitude (Mon), energy audit (Tue), challenge reframe (Wed), wins (Thu), intention (Fri) |
| `weekly-review` | `0 16 * * 0` (9am PT Sunday) | main | dm (Slack) | Structured weekly review. Compiles Oura data, habit completion rates, goal progress, journal themes. Asks for "went well / to improve" input |
| `growth-health-check` | `0 12 * * 1` (5am PT Monday) | main | silent | Validates growth.db integrity, checks for stale goals, orphaned habits. Alerts only on issues |

**Schedule rationale:**
- Morning prompts at 7am PT = before typical commute window
- Habit accountability at 6pm PT = end of workday, before evening routines
- Journal prompt at 4pm PT = afternoon reflection break, pairs with daily-memory-flush at 4pm PT
- Weekly review on Sunday 9am PT = weekend reflection time
- All use `isolated: true` for cron sessions (fresh context, reads workspace protocol doc)

**Model routing:** All use Sonnet (default). No Opus needed — these are structured template-driven prompts, not creative analysis. Haiku is too terse for coaching-quality messages.

**Confidence:** HIGH. Same cron patterns as existing 25 jobs.

---

### 4. OpenClaw Platform Upgrade: v2026.3.11 -> v2026.3.13

**Should upgrade before feature work begins.** Key improvements since v2026.3.11:

| Version | Feature | Relevance to v2.10 |
|---------|---------|---------------------|
| v2026.3.12 | `openclaw backup create` / `openclaw backup verify` | Safety net before config changes. Use `--only-config` to snapshot openclaw.json |
| v2026.3.12 | Dashboard v2 (modular views, command palette) | Nice-to-have for Bob interaction. Does not affect agent behavior |
| v2026.3.12 | `/fast` mode for quick model interactions | Could speed up habit logging responses. Optional |
| v2026.3.12 | Ephemeral device tokens | Security improvement. Reduces long-lived credential risk |
| v2026.3.12 | Cron + Windows reliability fixes | Cron stability relevant for 4-5 new crons |
| v2026.3.13 | Docker `OPENCLAW_TZ` timezone override | Useful for cron schedule clarity. Set to `America/Los_Angeles` |
| v2026.3.13 | Compaction token counting fix | Prevents over-aggressive compaction. Direct relevance to long DM sessions with habit/journal entries |
| v2026.3.13 | Dashboard v2 tool-heavy render fix | Prevents UI freeze during tool-heavy runs |

**Upgrade procedure (established pattern):**
```bash
# On EC2 via SSH
openclaw backup create --only-config  # NEW in v2026.3.12 - use after upgrade
npm install -g openclaw@latest
openclaw doctor --fix
systemctl --user restart openclaw-gateway.service
# Verify
/home/ubuntu/.npm-global/bin/openclaw --version
# Should show v2026.3.13
```

**Risk:** LOW. v2026.3.12 and v2026.3.13 are incremental releases, not breaking changes. The security fix in v2026.3.11 is already applied. The compaction fix in v2026.3.13 is beneficial.

**Docker timezone config (add to openclaw.json after upgrade):**
```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "env": {
            "OPENCLAW_TZ": "America/Los_Angeles"
          }
        }
      }
    }
  }
}
```

**Confidence:** MEDIUM. Release notes are clear. Behavioral changes in compaction token counting need monitoring after upgrade.

---

### 5. ClawhHub Skills Assessment

Researched the ClawhHub marketplace for self-improvement, habit tracking, goal setting, and productivity skills. Here is the honest assessment:

| Skill | Slug | Verdict | Rationale |
|-------|------|---------|-----------|
| **habit-flow-skill** | `tralves/habit-flow-skill` | **DO NOT INSTALL** | Brings its own Node.js scripts (`sync_reminders.ts`), TypeScript deps, persona system. Overlaps with workspace protocol doc pattern. Adds complexity without value for a custom deployment |
| **habit-tracker** | `openclaw/habit-tracker` | **DO NOT INSTALL** | Generic persistent-memory approach. Does not use SQLite. Streak tracking is text-in-memory, not queryable |
| **self-improvement** | `navendugoyal19/self-improvement` | **CONSIDER** | Captures learnings, errors, corrections. Lightweight SKILL.md (no external deps). Could be useful for Bob's own self-improvement, not Andy's. Low priority |
| **self-improving-agent** | `pskoett/self-improving-agent` | **CONSIDER** | Structured incident logging. Complementary to Bob's existing learning system. Could enhance Bob's ability to improve his self-improvement coaching over time |
| **task-tracker** | `kesslerio/task-tracker` | **DO NOT INSTALL** | Overlaps with existing coordination.db task system + user_calendar_tasks. Would create competing task tracking systems |
| **goal-setting-okrs** | (community skill) | **DO NOT INSTALL** | Generic OKR templates. Custom GOAL_TRACKER.md with growth.db is more integrated and queryable |

**Recommendation:** Install 0-1 ClawhHub skills. The `self-improving-agent` skill is the only one worth considering, and only in a later phase after core habit/goal/journal features are stable. Custom workspace protocol docs + growth.db + crons are the right approach for v2.10.

**Confidence:** MEDIUM. Assessed based on skill descriptions, GitHub SKILL.md files, and community reviews. Have not tested any of these on the actual deployment.

---

### 6. Oura API Integration for Weekly Reviews

**Already have:** The `oura` skill and `health.db` with sleep, readiness, HRV, and heart rate data. Morning briefing Section 3 already pulls Oura data.

**What to add for weekly reviews:** A Python script that queries health.db for the past 7 days and generates a structured summary. No new API calls needed — health.db already has the data from existing cron ingest.

```python
# ~/scripts/weekly-oura-summary.py
# Reads health.db for past 7 days
# Returns JSON: avg_sleep_score, avg_readiness, hrv_trend, sleep_debt, best_day, worst_day
# Called by weekly-review cron via workspace protocol doc

import sqlite3, json
from datetime import date, timedelta

DB = "/home/ubuntu/clawd/health.db"

def weekly_summary():
    end = date.today()
    start = end - timedelta(days=7)
    conn = sqlite3.connect(DB)
    # Query sleep, readiness, HRV for date range
    # ... (implementation in plan phase)
    conn.close()
    return summary_dict

if __name__ == "__main__":
    print(json.dumps(weekly_summary()))
```

**Confidence:** HIGH. Same pattern as existing scripts that read health.db.

---

### 7. Voice Notes Pipeline Extension for Commute Prompts

**Current flow:** Phone -> Google Drive "Voice Notes" -> process-voice-notes.py -> coordination.db (voice_notes table)

**Extended flow for commute responses:**
1. `morning-reflection-prompt` cron delivers 1-2 prompts to Slack DM at 7am PT
2. Andy records voice note response on commute via Monologue app
3. Voice note appears in Google Drive "Voice Notes" folder
4. Existing `voice-notes-processor` cron (every 2 hours) picks it up, transcribes via Whisper, stores in coordination.db
5. **NEW:** Bob's next heartbeat (or a dedicated cron) reads new voice_notes entries, checks if they are responses to morning prompts (time window: 7am-10am PT), and creates a journal entry in growth.db from the transcript

**What to add:**
- Column in voice_notes table OR a linking table: `voice_note_id -> journal_entry_id`
- Logic in COMMUTE_PROMPTS.md: "If a voice note arrives within 3 hours of the morning prompt, treat it as a journal response. Extract mood/energy signals. Create journal entry in growth.db."
- No changes to process-voice-notes.py itself — the transcript storage is fine as-is

**Alternative considered:** Have Bob directly transcribe voice notes in real-time. **Rejected** because the existing pipeline (Google Drive -> Whisper -> DB) is working and free. Real-time would require a webhook or Slack audio integration, adding complexity.

**Confidence:** HIGH. Extends existing pipeline with one new interpretation layer.

---

### 8. growth.db Bind-Mount Configuration

Add growth.db to the Docker sandbox bind-mounts in openclaw.json, following the exact pattern of the other 6 databases.

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "binds": [
            "/home/ubuntu/clawd/growth.db:/workspace/growth.db"
          ]
        }
      }
    }
  }
}
```

**Note:** This goes in the existing `binds` array alongside coordination.db, health.db, content.db, email.db, observability.db, and yolo.db. Do not replace; append.

**Create the database before configuring the bind-mount:**
```bash
# On EC2
sqlite3 /home/ubuntu/clawd/growth.db < /home/ubuntu/scripts/growth-schema.sql
```

**Confidence:** HIGH. Same pattern as 6 existing database bind-mounts.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Habit tracking | Custom workspace protocol + growth.db | ClawhHub `habit-flow-skill` | Brings TypeScript deps, persona system, its own cron sync scripts. Overkill for a single-user deployment with established patterns |
| Goal tracking | Custom GOAL_TRACKER.md + growth.db | ClawhHub `goal-setting-okrs` | Generic templates. Custom gives queryable SQLite data and integration with morning briefing |
| Journal storage | growth.db `journal_entries` table | Markdown files in memory/ | DB is queryable (mood trends, prompt effectiveness). Files are not. Weekly review needs aggregate queries |
| Weekly review data | Python script reading health.db + growth.db | LLM-only analysis from memory | Concrete numbers (completion rates, sleep averages) are more useful than vibes from memory recall |
| Morning commute prompts | Cron -> Slack DM -> voice note response | Talk Mode (v2026.3.12) | Talk Mode requires phone connected to OpenClaw. Slack DM + Monologue voice note is already working and phone-native |
| New database | growth.db (separate) | Extend coordination.db | Different data domain, different lifecycle. coordination.db is system data; growth.db is personal data |
| OpenClaw upgrade | v2026.3.13 | Stay on v2026.3.11 | Missing backup CLI, Docker TZ override, compaction fix. Low-risk upgrade with clear benefits |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| ClawhHub `habit-flow-skill` | Brings TypeScript runtime, 7 persona configurations, its own cron management scripts. Conflicts with established workspace protocol pattern | Custom HABIT_TRACKER.md workspace doc |
| ClawhHub `task-tracker` | Conflicts with existing coordination.db task system and user_calendar_tasks | Existing task system for tasks; new GOAL_TRACKER.md for goals |
| New agent for self-improvement | 7 agents is already at the comfortable limit for t3.small. Self-improvement features are personal to Andy -> main agent | Run everything on `main` agent (Andy/Bob) |
| Notion/Airtable for habit data | Adds external dependency, API complexity, cost | SQLite growth.db — same pattern as 6 existing DBs |
| React Native / mobile app | Massive scope creep. Out of scope per PROJECT.md | Slack DM + Monologue voice notes cover mobile interaction |
| Whisper large model | Current `tiny` model is sufficient for voice note transcription. Large model would be slow on t3.small CPU | Keep `tiny` model. Transcription quality is adequate for journal entries |
| OpenAI API for anything | Quota exhausted per MEMORY.md. DALL-E/Whisper API skills still broken | Local Whisper, Gemini for embeddings, Claude for everything else |
| Dashboard v2 adoption | OpenClaw's built-in dashboard v2 (v2026.3.12) is for direct gateway interaction. Mission Control is the monitoring dashboard | Keep Mission Control. Dashboard v2 is opt-in for Bob interaction but doesn't replace MC |
| Separate voice note transcription for journal | Existing pipeline handles all voice notes uniformly | Post-process voice_notes in coordination.db to identify journal responses |

---

## Version Compatibility

| Component | Current Version | Target Version | Notes |
|-----------|----------------|---------------|-------|
| OpenClaw | v2026.3.11 | v2026.3.13 | Upgrade for backup CLI, Docker TZ, compaction fix |
| QMD | v1.1.0 | v1.1.0 (no change) | Memory system stable after v2.9 overhaul |
| Bun | v1.3.10 | v1.3.10 (no change) | QMD runtime, no change needed |
| Node.js | 18.x+ | 18.x+ (no change) | EC2 runtime |
| Python | 3.x | 3.x (no change) | Scripts (voice notes, Oura summary, growth.db init) |
| SQLite | 3.x | 3.x (no change) | growth.db uses same engine as 6 existing DBs |
| Next.js | 14.2.15 | 14.2.15 (no change) | Mission Control. Growth dashboard page added later |
| better-sqlite3 | 12.6.2 | 12.6.2 (no change) | Mission Control DB reads. Add growth.db config path |
| Whisper | tiny model | tiny model (no change) | Voice note transcription |
| Recharts | Installed | No change | Future growth trend charts in Mission Control |
| shadcn/ui | Installed | No change | Future growth dashboard components |

---

## Installation / Setup Summary

```bash
# On EC2 (100.72.143.9) via SSH

# === STEP 0: OpenClaw Upgrade (do first) ===
npm install -g openclaw@latest
openclaw doctor --fix
/home/ubuntu/.npm-global/bin/openclaw --version
# Verify: v2026.3.13

# Create config backup using NEW backup CLI
/home/ubuntu/.npm-global/bin/openclaw backup create --only-config

# === STEP 1: Create growth.db ===
# Upload schema SQL to EC2, then:
sqlite3 /home/ubuntu/clawd/growth.db < /home/ubuntu/scripts/growth-schema.sql
# Verify:
sqlite3 /home/ubuntu/clawd/growth.db ".tables"
# Should show: habits, habit_completions, goals, goal_checkins, journal_entries, weekly_reviews

# === STEP 2: Add growth.db bind-mount to openclaw.json ===
python3 -c "
import json, shutil
path = '/home/ubuntu/.openclaw/openclaw.json'
shutil.copy(path, path + '.bak-v2.10')
with open(path) as f:
    cfg = json.load(f)
binds = cfg['agents']['defaults']['sandbox']['docker']['binds']
new_bind = '/home/ubuntu/clawd/growth.db:/workspace/growth.db'
if new_bind not in binds:
    binds.append(new_bind)
# Add Docker timezone if upgrading
cfg['agents']['defaults']['sandbox']['docker'].setdefault('env', {})['OPENCLAW_TZ'] = 'America/Los_Angeles'
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
print('Done. growth.db bind-mount added.')
"

# === STEP 3: Deploy workspace protocol docs ===
# Write HABIT_TRACKER.md, GOAL_TRACKER.md, JOURNAL_PROTOCOL.md,
# WEEKLY_REVIEW.md, COMMUTE_PROMPTS.md to ~/clawd/agents/main/
# (Content defined in plan phase)

# === STEP 4: Deploy helper scripts ===
# weekly-oura-summary.py -> ~/scripts/
# growth-db-utils.py -> ~/scripts/  (CRUD helpers called by Bob via Python)

# === STEP 5: Add cron jobs to openclaw.json ===
# morning-reflection-prompt, habit-accountability, journal-prompt,
# weekly-review, growth-health-check
# (Exact payloads defined in plan phase)

# === STEP 6: Restart gateway (batch all config changes) ===
systemctl --user restart openclaw-gateway.service
journalctl --user -u openclaw-gateway.service --since '1 min ago' | tail -20

# === STEP 7: Verify ===
# Test habit logging via Slack DM: "log exercise"
# Test goal creation: "set goal: read 12 books this quarter"
# Test journal prompt arrives at scheduled time
# Verify growth.db has data: sqlite3 ~/clawd/growth.db "SELECT * FROM habits;"
```

**Packages to install:** None (npm). `openclaw@latest` global upgrade only.
**Packages to remove:** None.
**Docker images to build:** None.
**New agents to configure:** None.
**New databases to create:** 1 (growth.db).
**New cron jobs to add:** 4-5.
**New workspace protocol docs:** 5.
**New Python scripts:** 2-3 (weekly-oura-summary.py, growth-db-utils.py, optionally growth-schema.sql as standalone).
**ClawhHub skills to install:** 0.

---

## Sources

### HIGH confidence
- [OpenClaw Cron Jobs Documentation](https://docs.openclaw.ai/automation/cron-jobs) — cron schedule types, isolated sessions, delivery options
- [OpenClaw Skills Overview](https://docs.openclaw.ai/tools/clawhub) — skill structure, installation, workspace loading
- [OpenClaw GitHub Releases](https://github.com/openclaw/openclaw/releases) — v2026.3.12 and v2026.3.13 release notes, backup CLI, Docker TZ, compaction fix
- [Oura API v2 Documentation](https://cloud.ouraring.com/v2/docs) — daily readiness, sleep, heart rate endpoints
- PROJECT.md (internal) — confirmed current stack: v2026.3.11, 7 agents, 25 crons, 6 DBs, voice notes pipeline
- MEMORY.md (internal) — confirmed voice notes pipeline flow, Oura integration, cron configuration, Docker bind-mount patterns

### MEDIUM confidence
- [ClawhHub habit-flow-skill SKILL.md](https://github.com/openclaw/skills/blob/main/skills/tralves/habit-flow-skill/SKILL.md) — skill features, proactive coaching, cron sync scripts. Assessed as too complex for this deployment
- [ClawhHub self-improvement skill](https://github.com/openclaw/skills/blob/main/skills/navendugoyal19/self-improvement/SKILL.md) — incident logging, correction capture. Lightweight but low priority
- [kesslerio/task-tracker](https://github.com/kesslerio/task-tracker-openclaw-skill) — task management with weekly reviews. Overlaps with existing coordination.db
- [OpenClaw v2026.3.12 Release Notes](https://blockchain.news/ainews/openclaw-v2026-3-12-release-dashboard-v2-fast-mode-plugin-architecture-for-ollama-sglang-vllm-and-ephemeral-device-tokens) — dashboard v2, fast mode, backup CLI details
- [OpenClaw v2026.3.11 Security Fix](https://www.elegantsoftwaresolutions.com/blog/openclaw-v2026-3-11-security-fix-guide) — WebSocket origin validation, current version behavior
- [oura-ring PyPI](https://pypi.org/project/oura-ring/) — Python client for Oura API v2. Not needed (already have health.db with data)
- [OpenClaw Workspace Best Practices](https://openclaw.com.au/best-practices) — memory organization, heartbeat patterns, cron scheduling
- [OpenClaw Proactive Agent Patterns](https://medium.com/@rentierdigital/the-complete-openclaw-architecture-that-actually-scales-memory-cron-jobs-dashboard-and-the-c96e00ab3f35) — cron-triggered agentic loop, heartbeat architecture

### LOW confidence
- [VoltAgent awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) — skill catalog with 5,400+ skills. Used for discovery, not verification
- [DoneClaw Best ClawhHub Skills](https://doneclaw.com/blog/best-openclaw-skills-clawhub/) — editorial list, used for skill discovery
- [DataCamp Best ClawHub Skills](https://www.datacamp.com/blog/best-clawhub-skills) — editorial list, used for cross-reference

---

*Stack research for: pops-claw v2.10 Self-Improvement Companion — habit tracking, goal tracking, journal prompts, weekly reviews, morning commute prompts*
*Researched: 2026-03-16*
*Replaces: previous STACK.md covering v2.9 Memory System Overhaul*
