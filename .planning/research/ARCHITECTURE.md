# Architecture: Self-Improvement Companion (v2.10)

**Domain:** Habit tracking, journal prompts, weekly reviews, goal tracking, and morning commute voice note prompts integrated into existing OpenClaw agent/skill/cron/database architecture
**Researched:** 2026-03-16
**Confidence:** HIGH (existing system patterns well-documented from v2.0-v2.9), MEDIUM (voice note round-trip flow timing), LOW (ClawhHub habit-flow-skill internals -- not installed, evaluated from docs only)

---

## Executive Summary

The self-improvement features integrate into the existing pops-claw architecture as a **single new database** (`selfimprove.db`), **4-6 new cron jobs**, **2-3 new workspace protocol docs**, and **one new Mission Control page** (`/growth`). No new agents, no new skills from ClawhHub, no new infrastructure.

The key architectural insight is that every self-improvement feature maps onto patterns already established and battle-tested across 9 milestones: cron-triggered prompts follow the reference doc pattern (MEETING_PREP.md, YOLO_BUILD.md), data storage follows the SQLite + bind-mount + WAL-mode-read pattern (6 existing databases), voice note integration reuses the existing Google Drive -> Whisper -> coordination.db pipeline (process-voice-notes.py), and dashboard pages follow the SWR + API route + better-sqlite3 pattern (7 existing pages).

The critical design decision is: **one new database (`selfimprove.db`) rather than scattering tables across coordination.db**. Reason: coordination.db already serves 4+ purposes (tasks, voice notes, agent coordination, user calendar). Adding habits, goals, journal entries, and streaks would make it a dumping ground. A dedicated database maintains the pattern of domain-specific SQLite files (health.db for Oura, content.db for articles, email.db for conversations, yolo.db for builds).

---

## System Architecture: Current State + New Components

```
EC2 (100.72.143.9) -- t3.small, 2GB RAM + 2GB swap
|
+-- OpenClaw v2026.3.11 (gateway on loopback :18789)
|   +-- Config: ~/.openclaw/openclaw.json
|   +-- 7 agents (main, landos, rangeos, ops, quill, sage, ezra)
|   +-- 25 cron jobs (staggered heartbeats, briefings, content pipeline, etc.)
|   +-- 18 skills at ~/.openclaw/skills/
|
+-- EXISTING DATABASES (6)
|   +-- health.db       -- Oura Ring data (sleep, readiness, HRV)
|   +-- coordination.db -- tasks, voice_notes, agent coordination
|   +-- content.db      -- content pipeline (topics, drafts, articles)
|   +-- email.db        -- AgentMail conversations
|   +-- observability.db -- agent output + event logs
|   +-- yolo.db         -- YOLO Dev build history
|
+-- NEW: selfimprove.db  <-- single new database for all self-improvement data
|   +-- habits           -- habit definitions + daily completions
|   +-- habit_logs       -- individual completion events
|   +-- goals            -- OKR-style goals with key results
|   +-- goal_checkins    -- weekly progress check-ins
|   +-- journal_entries  -- daily journal responses (mood, energy, reflection)
|   +-- commute_prompts  -- morning prompt delivery + response tracking
|
+-- NEW CRON JOBS (4-6)
|   +-- morning-commute-prompt  -- 7:15 AM PT, before commute, Slack DM
|   +-- journal-prompt          -- 8:00 PM PT, evening reflection, Slack DM
|   +-- habit-nudge             -- 9:00 PM PT, accountability check, Slack DM
|   +-- weekly-growth-review    -- 8:00 AM PT Sundays, structured retrospective
|   +-- (optional) midday-checkin -- 12:00 PM PT, energy/focus pulse
|   +-- (optional) goal-weekly-checkin -- Fridays 4:00 PM PT
|
+-- NEW WORKSPACE DOCS
|   +-- ~/clawd/agents/main/GROWTH_COMPANION.md  -- standing instructions
|   +-- ~/clawd/agents/main/JOURNAL_PROMPT.md     -- evening cron reference doc
|   +-- ~/clawd/agents/main/WEEKLY_REVIEW_GROWTH.md -- Sunday review reference doc
|   +-- ~/clawd/agents/main/COMMUTE_PROMPT.md     -- morning prompt reference doc
|
+-- MODIFIED COMPONENTS
|   +-- morning-briefing cron -- add Section 12: Growth Dashboard (streaks, goals)
|   +-- weekly-review cron -- add self-improvement section (habit trends, goal progress)
|   +-- openclaw.json -- add selfimprove.db bind-mount to sandbox
|   +-- Mission Control -- add /growth page
|
+-- EXISTING VOICE NOTES PIPELINE (reused, not modified)
    +-- Google Drive "Voice Notes" folder
    +-- ~/scripts/process-voice-notes.py (polls Drive, Whisper transcription)
    +-- coordination.db voice_notes table (stores transcripts)
    +-- voice-notes-processor cron (every 2h)
```

---

## Recommended Architecture

### Component Boundaries

| Component | Responsibility | Communicates With | New/Modified |
|-----------|----------------|-------------------|--------------|
| `selfimprove.db` | Store all self-improvement data (habits, goals, journal, streaks) | Bob via Python sqlite3 in sandbox, Mission Control via better-sqlite3 | NEW |
| `GROWTH_COMPANION.md` | Standing instructions for Bob: how to log habits, respond to journal prompts, track goals, handle commute voice notes | Bob reads at session start | NEW |
| `morning-commute-prompt` cron | Deliver reflection/discussion topic before commute | Slack DM via main agent, reads selfimprove.db for context | NEW |
| `journal-prompt` cron | Deliver evening reflection prompt | Slack DM via main agent, reads health.db (Oura) for energy context | NEW |
| `habit-nudge` cron | Evening accountability check on incomplete habits | Slack DM, reads selfimprove.db habit_logs for today | NEW |
| `weekly-growth-review` cron | Sunday structured retrospective | Slack DM, reads selfimprove.db + health.db for weekly patterns | NEW |
| `morning-briefing` cron | Section 12: Growth Dashboard snapshot | Reads selfimprove.db for streaks, goals, yesterday's journal | MODIFIED |
| `weekly-review` cron | Add self-improvement section | Reads selfimprove.db for weekly habit completion rates | MODIFIED |
| Mission Control `/growth` | Dashboard page for self-improvement data | Reads selfimprove.db via API route | NEW |
| `process-voice-notes.py` | Existing voice note pipeline (unchanged) | coordination.db voice_notes table | UNCHANGED |
| Bob (main agent) | Processes DM responses to prompts, logs to selfimprove.db | selfimprove.db via Python sqlite3, Slack DM | ENHANCED |

### Database Schema: selfimprove.db

```sql
-- Habit definitions
CREATE TABLE habits (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,            -- "Meditation", "Exercise", "Read 30min"
    frequency TEXT NOT NULL DEFAULT 'daily',  -- daily, weekday, weekly
    target_count INTEGER DEFAULT 1, -- times per period
    category TEXT,                  -- health, mind, productivity, social
    created_at TEXT NOT NULL,       -- ISO 8601
    archived_at TEXT,               -- NULL = active
    streak_current INTEGER DEFAULT 0,
    streak_best INTEGER DEFAULT 0,
    streak_last_date TEXT           -- last completion date for streak calc
);

-- Individual habit completion events
CREATE TABLE habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id TEXT NOT NULL REFERENCES habits(id),
    completed_at TEXT NOT NULL,     -- ISO 8601
    notes TEXT,                     -- optional context from Bob
    source TEXT DEFAULT 'slack_dm', -- slack_dm, voice_note, briefing
    UNIQUE(habit_id, completed_at)  -- prevent double-logging same day
);

-- OKR-style goals
CREATE TABLE goals (
    id TEXT PRIMARY KEY,            -- UUID
    title TEXT NOT NULL,            -- "Ship v2.10 by March 30"
    description TEXT,
    category TEXT,                  -- personal, professional, health, learning
    target_date TEXT,               -- ISO 8601
    status TEXT DEFAULT 'active',   -- active, completed, paused, abandoned
    created_at TEXT NOT NULL,
    completed_at TEXT
);

-- Key results for each goal
CREATE TABLE key_results (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    description TEXT NOT NULL,      -- "Complete 3 phases per week"
    target_value REAL,              -- 3.0
    current_value REAL DEFAULT 0,   -- 2.0
    unit TEXT,                      -- "phases", "sessions", "%"
    updated_at TEXT
);

-- Weekly goal check-ins
CREATE TABLE goal_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT NOT NULL REFERENCES goals(id),
    week_start TEXT NOT NULL,       -- Monday date ISO 8601
    progress_notes TEXT,            -- Bob's summary
    blockers TEXT,
    confidence INTEGER,             -- 1-5 scale
    created_at TEXT NOT NULL
);

-- Journal entries (daily reflections)
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,              -- YYYY-MM-DD
    prompt TEXT,                     -- the prompt Bob delivered
    response TEXT,                   -- Andy's response
    mood INTEGER,                   -- 1-5 scale (extracted by Bob from response)
    energy INTEGER,                 -- 1-5 scale (extracted by Bob, or from Oura)
    themes TEXT,                    -- JSON array of extracted themes
    gratitude TEXT,                 -- extracted gratitude items
    created_at TEXT NOT NULL,
    source TEXT DEFAULT 'slack_dm', -- slack_dm, voice_note
    UNIQUE(date)                   -- one journal entry per day
);

-- Morning commute prompts (delivery + response tracking)
CREATE TABLE commute_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,              -- YYYY-MM-DD
    prompt_text TEXT NOT NULL,       -- what Bob sent
    prompt_category TEXT,            -- reflection, planning, gratitude, creative, growth
    delivered_at TEXT,               -- ISO 8601
    response_text TEXT,              -- Andy's response (if any)
    response_source TEXT,            -- slack_dm, voice_note
    responded_at TEXT,
    voice_note_id TEXT,             -- FK to coordination.db voice_notes if from voice
    UNIQUE(date)
);
```

**Why this schema:**
- **Separate habits from habit_logs:** Habits are definitions (what to track), logs are events (when completed). Enables streak calculation, completion rate stats, and historical analysis without scanning a flat table.
- **Goals with key_results:** OKR pattern gives measurable progress. Bob can update `current_value` during check-ins. Dashboard shows progress bars.
- **Journal entries with extracted fields:** Bob extracts mood/energy/themes from Andy's freeform response. Enables trend charts over time without requiring Andy to fill forms.
- **Commute prompts link to voice_notes:** The `voice_note_id` field connects morning commute responses (captured via voice) back to the existing voice notes pipeline. No pipeline modification needed.

---

## Data Flow: Feature by Feature

### Flow 1: Habit Tracking (Slack DM Logging)

```
Andy DMs Bob: "Done with meditation and exercise today"
         |
         v
Bob (main agent) reads GROWTH_COMPANION.md standing instructions
         |
         v  [pattern match: habit completion keywords]
Bob queries selfimprove.db for matching active habits:
  SELECT id, name FROM habits WHERE archived_at IS NULL
         |
         v
Bob inserts into habit_logs:
  INSERT INTO habit_logs (habit_id, completed_at, source) VALUES (?, date('now'), 'slack_dm')
         |
         v
Bob updates streak in habits table:
  UPDATE habits SET streak_current = streak_current + 1,
    streak_last_date = date('now'),
    streak_best = MAX(streak_best, streak_current + 1)
  WHERE id = ? AND streak_last_date = date('now', '-1 day')
         |
         v (streak broken if streak_last_date != yesterday)
  UPDATE habits SET streak_current = 1, streak_last_date = date('now')
  WHERE id = ? AND streak_last_date != date('now', '-1 day')
         |
         v
Bob responds: "Logged meditation (12-day streak!) and exercise (3-day streak)"
```

**Key pattern:** Bob handles habit logging conversationally via DM. No skill trigger needed -- GROWTH_COMPANION.md gives standing instructions to recognize habit completion language and log it. This matches the VOICE_NOTES_PROTOCOL.md pattern (workspace protocol doc, not skill).

### Flow 2: Morning Commute Prompt -> Voice Note -> Processing -> Tracking

```
CRON: morning-commute-prompt fires at 7:15 AM PT
         |
         v
Bob reads COMMUTE_PROMPT.md reference doc
         |
         v
Bob queries selfimprove.db for context:
  - Recent journal themes (last 7 days)
  - Active goals needing attention
  - Yesterday's Oura readiness score (from health.db)
  - Current habit streaks at risk (streak_last_date = 2 days ago)
         |
         v
Bob selects and personalizes a prompt from category rotation:
  Categories: reflection, planning, gratitude, creative, growth
  Example: "Your readiness was 85 yesterday and you have 3 active goals.
           On your commute today, think about: What's the one thing that
           would make this week feel successful? Record a voice note."
         |
         v
Bob delivers prompt via Slack DM + logs to selfimprove.db:
  INSERT INTO commute_prompts (date, prompt_text, prompt_category, delivered_at)
         |
         v  [Andy records voice note via Monologue app on phone]
         |
Phone -> Google Drive "Voice Notes" folder
         |
         v  [existing pipeline, no changes]
~/scripts/process-voice-notes.py (cron: every 2h)
  - Downloads from Google Drive
  - Whisper transcription (tiny model)
  - Stores in coordination.db voice_notes table
  - Moves to "Processed" folder
         |
         v  [NEW: Bob processes voice note with growth context]
Bob's next session (heartbeat or DM) reads GROWTH_COMPANION.md:
  "Check coordination.db for new voice notes since last check.
   If a voice note was recorded within 2 hours of a commute prompt,
   link it as the commute prompt response."
         |
         v
Bob updates commute_prompts:
  UPDATE commute_prompts SET
    response_text = ?, response_source = 'voice_note',
    responded_at = ?, voice_note_id = ?
  WHERE date = date('now')
         |
         v
Bob extracts themes/insights and logs to journal or goal check-in as appropriate
```

**Critical timing note:** The voice note pipeline runs every 2 hours. A voice note recorded at 7:30 AM during commute won't be transcribed until the 8:00 or 10:00 AM pipeline run. Bob's association of voice note to commute prompt happens at the NEXT session after transcription completes. This delay is acceptable -- the response doesn't need real-time processing. The key is the association logic in GROWTH_COMPANION.md: "within 2 hours of commute prompt delivery time."

### Flow 3: Evening Journal Prompt

```
CRON: journal-prompt fires at 8:00 PM PT
         |
         v
Bob reads JOURNAL_PROMPT.md reference doc
         |
         v
Bob queries for context:
  - Today's Oura readiness + sleep (health.db)
  - Today's habit completions (selfimprove.db)
  - Today's commute prompt + response if any (selfimprove.db)
  - Recent journal themes for variety (selfimprove.db, last 7 days)
         |
         v
Bob constructs personalized prompt:
  "You completed 4/5 habits today (missed reading). Your energy was 78.
   Reflect on: What energized you most today? What would you do differently?"
         |
         v
Bob delivers via Slack DM
         |
         v  [Andy responds in DM or via voice note]
Bob receives response (DM session) or picks up voice note (next pipeline run)
         |
         v
Bob extracts structured fields from freeform response:
  - mood (1-5, inferred from language)
  - energy (1-5, from Oura or self-report)
  - themes (array: ["focus", "exercise", "meetings"])
  - gratitude items (if present)
         |
         v
Bob inserts into selfimprove.db:
  INSERT INTO journal_entries (date, prompt, response, mood, energy, themes, gratitude, source, created_at)
```

### Flow 4: Weekly Growth Review (Sunday)

```
CRON: weekly-growth-review fires at 8:00 AM PT Sunday
         |
         v
Bob reads WEEKLY_REVIEW_GROWTH.md reference doc
         |
         v
Bob queries selfimprove.db + health.db for the week:
  - Habit completion rates per habit (7-day window)
  - Streaks gained/lost
  - Journal mood/energy trend (7 data points)
  - Goal progress (key_results current_value changes)
  - Commute prompt response rate
  - Oura weekly averages (sleep, readiness, HRV)
         |
         v
Bob constructs structured weekly review:
  ## This Week's Growth

  ### Habits (5/7 days average)
  - Meditation: 7/7 (14-day streak!)
  - Exercise: 5/7 (streak: 5)
  - Reading: 3/7 (needs attention)

  ### Energy & Mood Trend
  [text description of Mon-Sun pattern]
  Oura avg readiness: 82, sleep: 7.4h

  ### Goals Progress
  - Ship v2.10: 60% -> 75% (on track)
  - Read 12 books in 2026: 3/12 (behind pace)

  ### Patterns Noticed
  [Bob's AI analysis of correlations:
   "Exercise days correlate with higher mood scores.
    Reading habit drops on meeting-heavy days."]

  ### Next Week Focus
  [Based on patterns, suggest 1-2 adjustments]
         |
         v
Bob delivers via Slack DM
Bob logs goal_checkins for each active goal
```

### Flow 5: Morning Briefing Integration (Section 12)

```
EXISTING CRON: morning-briefing fires at 7:00 AM PT
         |
         v  [existing 11 sections unchanged]
         |
         v  [NEW Section 12: Growth Dashboard]
Bob queries selfimprove.db:
  - Active habit streaks (top 3 by streak length)
  - Yesterday's habit completion (X/Y)
  - Current mood trend (last 3 days)
  - Goals with upcoming target dates
  - Commute prompt for today (already delivered at 7:15? or preview)
         |
         v
Section 12: Growth Dashboard
  Habits: 4/5 yesterday | Meditation 14-day streak
  Mood trend: 4, 3, 4 (stable)
  Goals: v2.10 75% (due Mar 30) | Reading 25% (behind)
```

---

## Integration Points: What's New vs Modified vs Unchanged

### New Components

| Component | Type | Location | Depends On |
|-----------|------|----------|------------|
| `selfimprove.db` | SQLite database | `~/clawd/selfimprove.db` | Schema creation script |
| `GROWTH_COMPANION.md` | Workspace protocol doc | `~/clawd/agents/main/GROWTH_COMPANION.md` | selfimprove.db schema |
| `JOURNAL_PROMPT.md` | Cron reference doc | `~/clawd/agents/main/JOURNAL_PROMPT.md` | GROWTH_COMPANION.md |
| `WEEKLY_REVIEW_GROWTH.md` | Cron reference doc | `~/clawd/agents/main/WEEKLY_REVIEW_GROWTH.md` | selfimprove.db populated |
| `COMMUTE_PROMPT.md` | Cron reference doc | `~/clawd/agents/main/COMMUTE_PROMPT.md` | GROWTH_COMPANION.md |
| `morning-commute-prompt` | OpenClaw cron | openclaw.json crons array | COMMUTE_PROMPT.md |
| `journal-prompt` | OpenClaw cron | openclaw.json crons array | JOURNAL_PROMPT.md |
| `habit-nudge` | OpenClaw cron | openclaw.json crons array | selfimprove.db |
| `weekly-growth-review` | OpenClaw cron | openclaw.json crons array | WEEKLY_REVIEW_GROWTH.md |
| `/growth` page | Mission Control page | `~/clawd/mission-control/src/app/growth/` | selfimprove.db |
| `/api/growth/*` | API routes | `~/clawd/mission-control/src/app/api/growth/` | selfimprove.db |

### Modified Components

| Component | Change | Risk |
|-----------|--------|------|
| `openclaw.json` | Add selfimprove.db to sandbox bind-mounts + add 4-6 new cron entries | LOW -- established pattern, requires gateway restart |
| `morning-briefing` cron payload or reference doc | Add Section 12: Growth Dashboard | LOW -- additive section, no existing sections affected |
| `weekly-review` cron reference doc | Add self-improvement section | LOW -- additive section |
| Mission Control `db-paths.ts` | Add selfimprove.db path | LOW -- one line |
| Mission Control `NavBar` | Add /growth link | LOW -- one component |

### Unchanged Components

| Component | Why Unchanged |
|-----------|---------------|
| `process-voice-notes.py` | Existing pipeline already transcribes voice notes to coordination.db. Commute prompt responses go through the same pipeline. Bob associates them after transcription. |
| `health.db` | Read-only for Oura data. Journal prompts READ energy/sleep data but don't write to health.db. |
| `coordination.db` | Voice notes still stored here. No new tables added. Bob reads voice_notes to find commute responses. |
| All 7 agents | No new agents. Main agent (Bob) handles all self-improvement features. |
| All 18 skills | No new ClawhHub skills installed. Protocol docs handle everything. |
| QMD memory system | Unchanged. selfimprove.db data is queried directly, not via memory search. |
| Docker sandbox config | Only change is bind-mount addition for selfimprove.db. |

---

## Patterns to Follow

### Pattern 1: Reference Doc Pattern for Cron Instructions (Established v2.0+)

**What:** Cron payload message is concise ("Follow JOURNAL_PROMPT.md"). Detailed instructions live in the workspace protocol doc.

**When:** Every new cron job for self-improvement features.

**Why:** Cron payloads have character limits and are stored in openclaw.json (hard to edit). Reference docs are markdown files on disk (easy to iterate, version-controlled, readable by Bob at session start).

**Example:**
```json
{
  "id": "journal-prompt-001",
  "name": "journal-prompt",
  "agentId": "main",
  "schedule": { "expr": "0 20 * * *", "tz": "America/Los_Angeles", "kind": "cron" },
  "sessionTarget": "main",
  "isolated": true,
  "payload": {
    "kind": "systemEvent",
    "text": "Follow JOURNAL_PROMPT.md to deliver tonight's reflection prompt."
  },
  "delivery": { "channel": "slack:dm", "bestEffort": true }
}
```

### Pattern 2: SQLite + Bind-Mount + WAL-Mode Read (Established v2.5+)

**What:** New database file on EC2 host, bind-mounted into Docker sandbox for agent writes, read by Mission Control via better-sqlite3 in WAL mode.

**When:** selfimprove.db creation and access.

**Example:**
```json
// openclaw.json: agents.defaults.sandbox.docker.binds
"/home/ubuntu/clawd/selfimprove.db:/workspace/selfimprove.db:rw"
```

```typescript
// Mission Control: src/lib/db-paths.ts
export const SELFIMPROVE_DB = "/home/ubuntu/clawd/selfimprove.db";
```

```typescript
// API route opens in WAL read-only mode
const db = new Database(SELFIMPROVE_DB, { readonly: true });
db.pragma("journal_mode = WAL");
```

### Pattern 3: Python sqlite3 for Sandbox DB Access (Established v2.6+)

**What:** Bob uses Python sqlite3 module inside Docker sandbox to read/write databases. Not the sqlite3 CLI, not Node.js better-sqlite3.

**When:** Bob logs habits, creates goals, writes journal entries.

**Example from GROWTH_COMPANION.md instructions:**
```
When logging a habit completion, use this exact pattern:

python3 -c "
import sqlite3, json
from datetime import date
conn = sqlite3.connect('/workspace/selfimprove.db')
today = date.today().isoformat()
conn.execute('INSERT OR IGNORE INTO habit_logs (habit_id, completed_at, source) VALUES (?, ?, ?)',
    ('habit-uuid', today, 'slack_dm'))
conn.commit()
conn.close()
"
```

### Pattern 4: Standing Instructions via Protocol Doc (Established v2.6+)

**What:** GROWTH_COMPANION.md as a workspace protocol doc read by Bob at session start. Contains recognition patterns, DB access templates, response formats.

**When:** Every self-improvement interaction (habit logging, journal responses, goal updates).

**Why:** More reliable than skill triggers for pattern matching in DM conversations. Established pattern: VOICE_NOTES_PROTOCOL.md, CONTENT_TRIGGERS.md, YOLO_BUILD.md all use this approach successfully.

### Pattern 5: Additive Briefing Sections (Established v2.0+)

**What:** New briefing sections are added to the morning-briefing and weekly-review cron reference docs. Each section is independent -- failure in one section doesn't block others.

**When:** Adding Growth Dashboard to morning briefing.

**Why:** The morning briefing already has 11 sections. Section 12 follows the same pattern: query a database, format results, include in the briefing markdown.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Installing ClawhHub habit-tracker or self-improvement Skills

**What happens:** The ClawhHub has `habit-flow-skill` (tralves) and `self-improvement` (navendugoyal19) skills. Installing them adds YAML frontmatter skills that compete with the protocol doc approach.

**Why bad:** Skills are trigger-based (specific phrases or patterns). The self-improvement features need conversational recognition ("I did my meditation" should log a habit, but "meditation was discussed in the meeting" should not). Protocol docs give Bob context and judgment. Skills give rigid pattern matching. Additionally, ClawhHub skills use their own storage patterns that won't integrate with selfimprove.db or Mission Control.

**Instead:** Write GROWTH_COMPANION.md with specific recognition instructions. Bob's LLM judgment (via Sonnet/Opus) is more reliable than skill trigger patterns for this use case.

### Anti-Pattern 2: Adding Tables to coordination.db

**What happens:** Habits, goals, journal entries are added as new tables in coordination.db because "it's the main agent database."

**Why bad:** coordination.db already has tasks, voice_notes, and agent coordination data. Adding 6+ more tables turns it into a monolithic database. Mission Control queries become complex. Schema migrations become risky (one bad migration breaks tasks AND habits). The established pattern is domain-specific databases: health.db for health, content.db for content, email.db for email.

**Instead:** Create selfimprove.db as a new domain-specific database. Same bind-mount pattern, same WAL-mode reads, clean separation.

### Anti-Pattern 3: Creating a New Agent for Self-Improvement

**What happens:** A new "growth" or "sage" agent is created to handle self-improvement features.

**Why bad:** Self-improvement features are deeply personal -- they reference Andy's habits, goals, mood, and Oura data. This is Bob's (main agent) domain. A separate agent would need access to health.db, coordination.db (voice notes), and selfimprove.db, plus would need its own heartbeat, increasing rate limit pressure. The feature set doesn't justify a separate agent -- it's 4-6 cron jobs and conversational DM handling.

**Instead:** Bob (main agent) handles everything. GROWTH_COMPANION.md gives standing instructions. Cron jobs target the main agent.

### Anti-Pattern 4: Real-Time Voice Note Processing for Commute Responses

**What happens:** A new pipeline is built to process commute voice notes immediately (within minutes) so Bob can respond in real-time.

**Why bad:** The existing pipeline processes every 2 hours. Building real-time processing would require: Google Drive webhook, instant Whisper transcription, new cron or event trigger. This is significant infrastructure for a feature where latency doesn't matter -- Andy records during commute, the response can be processed by the next heartbeat or briefing.

**Instead:** Use the existing 2-hour pipeline. Bob associates voice notes with commute prompts during his next session. The 2-hour delay is acceptable because the value is in the recording and reflection, not the immediate processing.

### Anti-Pattern 5: Complex Streak Calculation Logic in Bob's Sessions

**What happens:** Bob calculates streaks by scanning the entire habit_logs table, counting consecutive days, handling weekday-only habits, etc. during every DM interaction.

**Why bad:** Expensive queries during conversational sessions. Risk of incorrect streak counts from LLM-generated SQL. Streaks are a derived metric that should be maintained incrementally.

**Instead:** Store `streak_current`, `streak_best`, and `streak_last_date` directly on the habits table. Update incrementally when logging completions. One simple comparison: if `streak_last_date == yesterday`, increment; otherwise reset to 1. This is fast and reliable.

---

## Build Order: Dependencies Between Components

```
PHASE 1: Database Foundation
  - Create selfimprove.db with schema on EC2
  - Add bind-mount to openclaw.json
  - Gateway restart (batch with any other config changes)
  - Write GROWTH_COMPANION.md standing instructions
  DEPENDS ON: Nothing
  RISK: Gateway restart clears DM sessions (known pitfall)
  OUTPUT: Bob can log habits, goals, journal entries via DM

PHASE 2: Habit Tracking + Accountability
  - Seed initial habits via Bob DM or direct SQL
  - Create habit-nudge cron (9 PM PT)
  - Add habit section to morning briefing (Section 12a)
  - Test: DM Bob "done with meditation", verify DB write + streak
  DEPENDS ON: Phase 1 (selfimprove.db + GROWTH_COMPANION.md)
  RISK: Low -- cron pattern established
  OUTPUT: Daily habit tracking loop operational

PHASE 3: Morning Commute Prompts + Voice Note Integration
  - Write COMMUTE_PROMPT.md reference doc
  - Create morning-commute-prompt cron (7:15 AM PT)
  - Add voice note association logic to GROWTH_COMPANION.md
  - Test: verify prompt delivery, record voice note, verify association
  DEPENDS ON: Phase 1 (selfimprove.db) + existing voice notes pipeline
  RISK: MEDIUM -- voice note timing depends on 2h pipeline lag
  OUTPUT: Morning commute reflection loop operational

PHASE 4: Journal Prompts + Goal Tracking
  - Write JOURNAL_PROMPT.md reference doc
  - Create journal-prompt cron (8 PM PT)
  - Add goal management instructions to GROWTH_COMPANION.md
  - Seed initial goals via Bob DM
  - Test: verify evening prompt delivery, journal entry creation
  DEPENDS ON: Phase 1 (selfimprove.db)
  RISK: Low -- follows established cron pattern
  OUTPUT: Daily journal + goal tracking operational

PHASE 5: Weekly Review + Briefing Integration
  - Write WEEKLY_REVIEW_GROWTH.md reference doc
  - Create weekly-growth-review cron (Sunday 8 AM PT)
  - Add full Growth Dashboard section to morning briefing
  - Update weekly-review cron to include self-improvement metrics
  DEPENDS ON: Phases 2-4 (needs data to review)
  RISK: Low -- all patterns established
  OUTPUT: Weekly feedback loop operational

PHASE 6: Mission Control Dashboard
  - Add selfimprove.db to db-paths.ts
  - Create /api/growth/* API routes (habits, goals, journal, overview)
  - Create /growth page with habit streaks, mood chart, goal progress
  - Add /growth link to NavBar
  - npm run build + restart mission-control service
  DEPENDS ON: Phase 1 (selfimprove.db), ideally after Phases 2-4 have data
  RISK: Low -- established MC pattern (SWR + API route + better-sqlite3)
  OUTPUT: Visual dashboard for self-improvement data
```

**Why this order:**
1. **Database first** because every other component depends on selfimprove.db existing and being bind-mounted.
2. **Habit tracking second** because it's the simplest interaction loop (DM -> log -> streak) and produces immediate daily value.
3. **Commute prompts third** because they have the most complex flow (cron -> Slack -> voice note -> pipeline -> association) and need the most testing.
4. **Journal + goals fourth** because they build on the habit tracking patterns but add extracted fields and OKR structure.
5. **Weekly review fifth** because it needs accumulated data from phases 2-4 to be meaningful.
6. **Dashboard last** because it needs all data sources populated and is the least functionally critical (Bob delivers all data via Slack already).

---

## Scalability Considerations

This is a single-user personal system. "Scaling" means: what happens at 1 year of daily data?

| Concern | At 1 month | At 6 months | At 1 year |
|---------|------------|-------------|-----------|
| selfimprove.db size | ~50KB | ~500KB | ~1MB |
| habit_logs rows | ~150 (5 habits * 30 days) | ~900 | ~1800 |
| journal_entries rows | ~30 | ~180 | ~365 |
| goal_checkins rows | ~12 | ~72 | ~144 |
| Query performance | Instant | Instant | Instant |
| Mission Control API latency | <50ms | <50ms | <100ms |
| Impact on t3.small RAM | Negligible | Negligible | Negligible |
| Voice note pipeline impact | None (unchanged) | None | None |

**First bottleneck:** None foreseeable. selfimprove.db will stay small. The voice note pipeline is the potential bottleneck, but it's already running and unchanged.

**When to worry:** If journal entries include full voice note transcripts (potentially 1000+ words each), the journal_entries table could grow faster. But this is still trivially small for SQLite.

---

## Mission Control /growth Page Design

### Page Layout

```
/growth
+------------------------------------------------------+
| Growth Dashboard                          [date range]|
+------------------------------------------------------+
|                                                       |
| HABIT STREAKS                    TODAY'S HABITS       |
| +------------------+    +-------------------------+   |
| | Meditation: 14   |    | [x] Meditation          |  |
| | Exercise:   5    |    | [x] Exercise            |  |
| | Reading:    0    |    | [ ] Reading              |  |
| | Journal:    7    |    | [x] Journal             |  |
| +------------------+    | [x] Water intake        |  |
|                         +-------------------------+   |
|                                                       |
| MOOD & ENERGY TREND (Recharts LineChart, 30 days)    |
| +--------------------------------------------------+ |
| |  5 |    *  *       *   *  *                      | |
| |  4 | *    *  * *  *  *    *  *                    | |
| |  3 |                        *  *                  | |
| |  1 |                                              | |
| +--------------------------------------------------+ |
|                                                       |
| GOALS                                                |
| +--------------------------------------------------+ |
| | Ship v2.10         [====75%====      ] Mar 30    | |
| | Read 12 books      [==25%=           ] Dec 31    | |
| | Daily meditation   [==========100%===] Ongoing   | |
| +--------------------------------------------------+ |
|                                                       |
| WEEKLY HABIT COMPLETION (Recharts BarChart, 7 days)  |
| +--------------------------------------------------+ |
| | Mon: 5/5 | Tue: 4/5 | Wed: 5/5 | ...            | |
| +--------------------------------------------------+ |
|                                                       |
| RECENT JOURNAL ENTRIES (last 7)                       |
| +--------------------------------------------------+ |
| | Mar 15: Mood 4, Energy 4 - "Productive day..."   | |
| | Mar 14: Mood 3, Energy 3 - "Meeting heavy..."    | |
| +--------------------------------------------------+ |
+------------------------------------------------------+
```

### API Routes

| Route | Method | Returns |
|-------|--------|---------|
| `/api/growth/overview` | GET | Today's habits, active streaks, mood trend (30d), active goals |
| `/api/growth/habits` | GET | All habits with streaks, completion rates (7d, 30d) |
| `/api/growth/journal` | GET | Last 30 journal entries with mood/energy |
| `/api/growth/goals` | GET | Active goals with key results and progress |

### Technology (Zero New Packages)

- **better-sqlite3**: Already installed, reads selfimprove.db in WAL mode
- **SWR**: Existing 30s polling pattern
- **Recharts**: Already installed for LineChart (mood/energy) and BarChart (weekly completion)
- **shadcn/ui Card, Badge, Progress**: Already installed for layout components

---

## Cron Schedule Integration

Existing cron jobs that interact with self-improvement features:

| Time (PT) | Existing Cron | Self-Improvement Addition |
|-----------|---------------|--------------------------|
| 7:00 AM | morning-briefing | Add Section 12: Growth Dashboard |
| 7:15 AM | (none) | **NEW: morning-commute-prompt** |
| 8:00 AM Sunday | weekly-review | Add self-improvement section |
| 8:00 AM Sunday | (none, or after weekly-review) | **NEW: weekly-growth-review** |
| 8:00 PM | (none) | **NEW: journal-prompt** |
| 9:00 PM | (none) | **NEW: habit-nudge** |

**Cron count impact:** Current 25 crons -> 29 crons (4 new). Well within OpenClaw's capacity. All new crons use `isolated: true` with `bestEffort: true` delivery to avoid blocking if Slack session is stale.

**Rate limit impact:** All new crons target main agent (Bob). They run at off-peak times (7:15 AM, 8 PM, 9 PM, Sunday 8 AM). No overlap with existing heartbeat windows (:00/:02/:04/:06). Minimal rate limit pressure.

---

## Gateway Restart Strategy

Only **one gateway restart** needed for the entire milestone:
- Add selfimprove.db bind-mount to openclaw.json
- Add 4-6 new cron job entries to openclaw.json

Everything else is hot-deployable:
- Workspace protocol docs (SCP to EC2)
- selfimprove.db creation (direct SQL on host)
- Mission Control page (build + restart MC service, not gateway)
- Briefing reference doc updates (SCP to EC2)

**Batch the restart into Phase 1.** All subsequent phases avoid gateway disruption.

---

## Sources

### HIGH confidence (established system patterns)
- PROJECT.md -- full system architecture, 6 databases, 25 crons, 18 skills, 7 agents
- MEMORY.md -- voice notes pipeline, cron configuration, sandbox architecture
- Cron audit (Phase 25) -- all 20+ crons verified, schedule expressions confirmed
- v2.9 ARCHITECTURE.md -- memory system data flow, QMD collection paths, bind-mount patterns
- RETROSPECTIVE.md -- established patterns: reference docs > skills, explicit bind-mounts, pattern reuse accelerates delivery
- findings.md -- cron job schema, webhook config, gateway config patterns
- process-voice-notes.py -- existing voice note pipeline (Google Drive -> Whisper -> coordination.db)

### MEDIUM confidence (design decisions requiring validation)
- Voice note to commute prompt association timing (2-hour pipeline lag acceptable but unverified in practice)
- Streak calculation approach (incremental update vs. query-time calculation -- incremental recommended but edge cases like timezone rollover need testing)
- Journal entry mood/energy extraction quality (depends on Bob's LLM prompt quality in JOURNAL_PROMPT.md)
- [ClawhHub habit-flow-skill](https://github.com/openclaw/skills/blob/main/skills/tralves/habit-flow-skill/SKILL.md) -- evaluated from docs, not installed
- [AI Journaling patterns](https://www.rosebud.app/) -- informed prompt category design
- [Morning Commute AI](https://completeaitraining.com/ai-tools/morning-commute/) -- informed commute prompt flow

### LOW confidence (needs validation during execution)
- Whether isolated cron sessions can reliably read selfimprove.db through bind-mount (should work based on content.db pattern, but verify)
- Whether Bob can reliably extract mood/energy as integers from freeform journal responses (may need prompt iteration)
- Optimal commute prompt delivery time (7:15 AM assumes Andy leaves ~7:30; may need adjustment)

---

*Architecture research for: pops-claw v2.10 Self-Improvement Companion*
*Researched: 2026-03-16*
*Replaces: v2.9 Memory System Overhaul ARCHITECTURE.md*
