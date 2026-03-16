# Feature Landscape: Self-Improvement Companion

**Domain:** AI-powered self-improvement companion (habit tracking, journaling, weekly reviews, goal tracking, morning commute prompts) layered onto existing OpenClaw agent
**Researched:** 2026-03-16
**Confidence:** HIGH for feature categories and UX patterns, MEDIUM for OpenClaw community skill patterns, LOW for voice-first commute interaction specifics

---

## Existing Infrastructure (What We Build On)

Before mapping new features, clarity on what already exists and can be extended. These are NOT new features -- they are foundations.

| Existing System | What It Does | How New Features Use It |
|----------------|-------------|------------------------|
| Morning briefing (7 sections + YOLO + content + email) | Daily Slack DM at wake time, health/calendar/email/weather/tasks/devices/GitHub | Add self-improvement section (habit streaks, goal progress, commute prompts) |
| Evening recap cron | End-of-day Slack DM summary | Add reflection prompts, habit check-in nudge |
| Weekly review cron | Weekly retrospective delivered via Slack | Upgrade from infrastructure status to personal retrospective with Oura energy patterns |
| Oura Ring integration (health.db) | Sleep score, readiness, HRV, resting HR stored daily | Correlate with habits, surface energy patterns in weekly reviews |
| Voice notes pipeline (Google Drive > Whisper > coordination.db) | Phone recordings transcribed and stored | Process commute voice responses, extract habit completions and reflections from speech |
| Memory system (QMD, MEMORY.md, daily flush) | Long-term context persistence across sessions | Store goal definitions, habit history, reflection themes for pattern detection |
| coordination.db | Task tracking, user calendar tasks | Store habits, goals, journal entries (extend existing tables or add new) |
| Reference doc pattern (HEARTBEAT.md, DAILY_FLUSH.md, etc.) | Cron instructions live in workspace markdown files | Create HABIT_TRACKER.md, WEEKLY_REVIEW.md, JOURNAL_PROMPTS.md, COMMUTE_PROMPTS.md |
| Slack DM as primary interface | All interaction via Slack DM to Bob | Natural language habit logging, goal updates, reflection responses |
| 25 cron jobs (staggered scheduling) | Heartbeats, briefings, pipeline, monitoring | Add habit nudge cron, journal prompt cron, commute prompt cron |

---

## Table Stakes

Features users expect from a self-improvement AI companion. Missing any of these makes the system feel incomplete or broken.

### 1. Habit Tracking with Streak Calculation

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Every productivity app has this. Streaks are the universal motivator. Without tracking, there's no feedback loop. |
| **Complexity** | MEDIUM -- new SQLite table(s) in coordination.db, streak calculation logic, cron for daily check-in |
| **Depends On** | coordination.db (existing), Slack DM interface (existing), morning briefing (existing) |
| **What It Includes** | Create/archive habits via Slack DM, log completions naturally ("I meditated today", "ran 3 miles"), streak tracking with 1-day forgiveness (research shows "emergency skip" days increase long-term adherence), daily/weekly frequency support, progress visible in morning briefing |
| **What It Does NOT Include** | Gamification badges, points systems, leaderboards (research shows 67% abandonment by week 4 with heavy gamification), complex habit stacking/chaining UIs |

**Key design decision:** Use natural language logging via Slack DM ("I did my pushups"), not a structured form or app UI. Bob parses intent and logs to SQLite. This matches the voice-first philosophy and Andy's Prospecting 81% (open-ended over structured).

**Streak forgiveness:** Research from behavioral science shows people are more motivated by a 7-day goal with 2 emergency skip days than a strict 5-day goal. Implement 1-day forgiveness: if a daily habit is missed for 1 day, the streak continues but is marked as "forgiven." Two consecutive misses break the streak.

**Schema sketch (coordination.db):**
```sql
CREATE TABLE habits (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  frequency TEXT DEFAULT 'daily',  -- daily, weekdays, weekly, custom
  target_days TEXT,                 -- for custom: "mon,wed,fri"
  created_at TEXT DEFAULT (datetime('now')),
  archived_at TEXT,
  notes TEXT
);

CREATE TABLE habit_completions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  habit_id TEXT NOT NULL REFERENCES habits(id),
  completed_date TEXT NOT NULL,     -- YYYY-MM-DD, PT timezone
  logged_via TEXT DEFAULT 'slack',  -- slack, voice_note, cron_prompt
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(habit_id, completed_date)
);
```

### 2. Morning Briefing Self-Improvement Section

| Aspect | Detail |
|--------|--------|
| **Why Expected** | The briefing is Andy's daily touchpoint. If self-improvement data isn't surfaced there, it might as well not exist. |
| **Complexity** | LOW -- add section to existing MORNING_BRIEFING.md reference doc |
| **Depends On** | Morning briefing cron (existing), habit tracking tables (new), Oura integration (existing) |
| **What It Includes** | Active habit streaks with current count, yesterday's completions summary, Oura readiness/sleep score (already exists -- just reference it alongside habit data), any goals due for weekly check-in today |
| **What It Does NOT Include** | Full habit history (too verbose for briefing), journal entries (private, not briefing material) |

**Format target:** 3-5 lines in the briefing. Not a wall of text. Example:
```
## Self-Improvement
Habits: meditation (12-day streak), reading (5-day), exercise (3/4 this week)
Oura: readiness 82, sleep 78 (7h12m), HRV 45ms
Goals: Q1 OKR check-in due Friday (2 of 3 KRs on track)
```

### 3. Daily Reflection/Journal Prompts

| Aspect | Detail |
|--------|--------|
| **Why Expected** | The core differentiator of AI companions over dumb trackers. Without reflection prompts, this is just a spreadsheet with a chatbot interface. |
| **Complexity** | LOW-MEDIUM -- prompt library, delivery cron, response storage |
| **Depends On** | Slack DM (existing), coordination.db (existing), memory system (existing) |
| **What It Includes** | 1 daily prompt delivered via Slack DM (evening, after work), varied categories (mindfulness, personal growth, work reflection, gratitude, relationships), personalized over time based on response patterns, responses stored in coordination.db for pattern analysis |
| **What It Does NOT Include** | Multiple prompts per day (prompt fatigue is real), mandatory responses (no guilt if skipped), clinical mental health assessment (this is reflection, not therapy) |

**Prompt categories (research-backed):**
- **Mindfulness:** "What is present in your body and environment right now?"
- **Personal growth:** "Which habit changed you most this quarter?"
- **Work reflection:** "What single constraint would make your work easier?"
- **Gratitude:** "What are you grateful for that you usually take for granted?"
- **Relationships:** "Where could you replace an assumption with a clarifying question?"
- **Energy:** "When did you feel most energized today? What were you doing?"

**Delivery timing:** Evening (around 5-6pm PT) when workday winds down. NOT morning -- mornings are for action (briefing), evenings are for reflection. Research supports this separation.

### 4. Weekly Review (Upgraded)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Already exists as infrastructure-focused weekly review. Users of self-improvement systems expect personal retrospectives, not server status reports. |
| **Complexity** | MEDIUM -- restructure existing weekly-review cron, add Oura correlation, habit summary |
| **Depends On** | Weekly review cron (existing -- restructure), Oura health.db (existing), habit tables (new), goal tables (new) |
| **What It Includes** | Structured sections: Wins (what went well), Challenges (friction points), Energy patterns (Oura readiness trend for the week -- which days high/low energy, sleep pattern), Habit report (streaks, completion rates, any broken streaks), Goal progress (OKR check-in), Focus for next week, Freeform insights |
| **What It Does NOT Include** | Infrastructure status (move to a separate ops review or append as optional section), automated scoring/grading of the week (humans resist being graded by their tools) |

**Key insight from research:** The most effective weekly reviews take 15-20 minutes and are conversational, not form-filling. Bob should prompt each section and allow Andy to respond, building the review collaboratively. The AI spots patterns ("Your energy dipped every afternoon this week -- Oura shows 6h sleep average vs 7h+ last week").

### 5. Goal Tracking (OKR-style)

| Aspect | Detail |
|--------|--------|
| **Why Expected** | Habits are daily behaviors; goals are quarterly outcomes. Without goal tracking, habits feel purposeless. OKR framework is well-understood and simple. |
| **Complexity** | LOW-MEDIUM -- new tables, weekly check-in cron, briefing integration |
| **Depends On** | coordination.db (existing), weekly review (upgraded), morning briefing (existing) |
| **What It Includes** | 3-5 Objectives per quarter, each with 2-3 measurable Key Results, weekly progress update via Slack DM or weekly review, traffic-light status (on track / at risk / off track), progress surfaced in morning briefing and weekly review |
| **What It Does NOT Include** | Team OKRs (this is personal), automated KR measurement (Andy manually updates progress -- simple is better), complex scoring (0.0-1.0 OKR scoring is for organizations, not individuals) |

**Schema sketch (coordination.db):**
```sql
CREATE TABLE goals (
  id TEXT PRIMARY KEY,
  objective TEXT NOT NULL,
  quarter TEXT NOT NULL,           -- e.g., "2026-Q1"
  status TEXT DEFAULT 'active',    -- active, completed, abandoned
  created_at TEXT DEFAULT (datetime('now')),
  notes TEXT
);

CREATE TABLE key_results (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL REFERENCES goals(id),
  description TEXT NOT NULL,
  target_value REAL,               -- numeric target (e.g., 10 for "read 10 books")
  current_value REAL DEFAULT 0,
  unit TEXT,                       -- "books", "miles", "%", etc.
  status TEXT DEFAULT 'on_track',  -- on_track, at_risk, off_track, completed
  updated_at TEXT
);
```

**Interaction pattern:** "Update my reading KR -- finished book 4 of 10" via Slack DM. Bob updates the database. Weekly review surfaces trend.

---

## Differentiators

Features that set this apart from generic habit apps. Not expected, but create significant value.

### 1. Morning Commute Prompts (Voice-First Reflection)

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Transforms dead commute time into active reflection time. Andy speaks; Bob listens (via existing voice notes pipeline). Unique to a proactive AI companion -- no standalone app does this. |
| **Complexity** | MEDIUM -- new cron, prompt generation, voice note processing integration |
| **Depends On** | Voice notes pipeline (existing), morning briefing (existing), Slack DM (existing) |
| **How It Works** | 1. Before commute (~7:30am PT), Bob sends 1-2 discussion topics to Slack DM. 2. Andy records voice note on phone during commute responding to the prompt. 3. Voice note hits Google Drive > Whisper pipeline > coordination.db. 4. Bob processes the transcription, extracts insights, stores in memory. |
| **Topics Are Personalized** | Based on: current goals (OKR check-in topics), recent journal reflections (follow-up on unresolved thoughts), Oura data (if sleep was poor, prompt about energy management), upcoming calendar (pre-meeting reflection), recent habit performance (if streak is strong, prompt about what's working) |

**Why this is a differentiator:** Standalone voice journaling apps (VoiceNotes AI, Pocket) can record and transcribe. They cannot personalize prompts based on your sleep data, calendar, habit streaks, and prior reflections because they don't have that data. Bob does.

**Timing consideration:** Prompt must arrive BEFORE the commute, not during. Andy reads the prompt, thinks about it, then records a voice note while driving. The prompt is a seed, not a conversation.

### 2. Oura-Correlated Habit Insights

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Surfaces patterns humans miss: "Your meditation streak correlates with 8% higher HRV on practice days" or "Sleep drops below 7h when you skip exercise for 2+ days." |
| **Complexity** | MEDIUM -- SQL queries joining health.db and habit_completions, pattern detection logic |
| **Depends On** | Oura Ring integration (existing), habit tracking tables (new), weekly review (upgraded) |
| **How It Works** | Weekly review includes an "Oura Insights" sub-section where Bob runs correlation queries: habit completion days vs. readiness scores, sleep duration trends vs. exercise habit, HRV patterns on meditation vs. non-meditation days. Findings presented conversationally, not as raw statistics. |
| **Confidence Level** | MEDIUM -- correlations require 4-6 weeks of habit data before patterns become meaningful. First 2-3 weeks will have insufficient data. Bob should say "not enough data yet" rather than fabricating patterns. |

**Example insight:** "Over the past 4 weeks, your readiness averaged 79 on days you meditated vs. 71 on days you didn't. Your HRV was also 6ms higher. The meditation habit seems to be paying off physically."

### 3. Pattern Detection Across Reflection Entries

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | After 4+ weeks of journal entries, Bob identifies recurring themes, mood shifts, and concern patterns. "You've mentioned feeling overwhelmed 4 times this month, always on Wednesdays after the team sync." |
| **Complexity** | LOW -- leverages existing QMD memory system. Journal entries stored in memory/; QMD indexes them; Bob searches and synthesizes during weekly review. |
| **Depends On** | Memory system (existing, QMD), journal entries stored as memory (new integration), weekly review (upgraded) |
| **How It Works** | Journal responses are appended to daily memory logs (memory/YYYY-MM-DD.md) alongside existing system state data. During weekly review, Bob searches QMD for recurring themes in recent entries. Pattern detection is LLM-powered (Bob reads entries and synthesizes), not algorithmic. |

### 4. Accountability Nudges (Not Nags)

| Aspect | Detail |
|--------|--------|
| **Value Proposition** | Gentle reminders that respect autonomy. Research shows urgent/guilt-based prompts increase cortisol and decrease long-term motivation. |
| **Complexity** | LOW -- conditional logic in evening recap cron |
| **Depends On** | Evening recap cron (existing), habit tracking tables (new) |
| **How It Works** | If it's 8pm and no habits logged today, Bob mentions it once in the evening recap: "No habits logged today -- want to check anything off before bed?" If Andy ignores it, Bob never follows up. No second reminder. No "you broke your streak!" guilt. The briefing next morning shows the updated streak status silently. |

**Anti-pattern alert:** Research from UC Berkeley shows adaptive algorithms that escalate urgency after missed days ("you missed yesterday too!") raise cortisol and reduce perceived autonomy. Bob must be the opposite: mention once, let it go. The streak count in the morning briefing provides passive accountability without nagging.

---

## Anti-Features

Features to explicitly NOT build. Commonly attempted, often counterproductive.

### 1. Heavy Gamification (Points, Badges, Leaderboards)

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Research: gamified habit apps show 41% higher engagement in first 2 weeks but 67% abandonment by week 4 (vs 38% for non-gamified). Points and badges create extrinsic motivation that undermines intrinsic habit formation. Andy's Kolbe profile (Quick Start 7) means novelty wears off fast -- gamification would be exciting for a week then abandoned. |
| **What to Do Instead** | Simple streaks + forgiveness. Streak count is motivating without being gamified. One-day forgiveness prevents the "all-or-nothing" thinking that causes habit abandonment after a single miss. |

### 2. Mood Scoring / Emotion Quantification

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Reducing complex emotional states to a 1-5 scale creates false precision. Users resist being asked "rate your mood" daily -- it feels clinical and reductive. Andy's ENFP-A profile (Feeling 68%) means emotions are rich and nuanced, not quantifiable. |
| **What to Do Instead** | Open-ended reflection prompts. "How are you feeling?" invites a real answer. Bob can detect sentiment from the response without forcing a number. Patterns emerge from natural language over time, not from a mood chart. |

### 3. Habit Stacking / Complex Routine Builder

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Habit stacking (if-then chaining: "after I brush my teeth, I will meditate") requires rigid sequential routines. Andy's Adaptability #5 + Prospecting 81% means he doesn't follow rigid sequences. Building a routine builder that goes unused wastes effort. |
| **What to Do Instead** | Track individual habits independently. Let Andy naturally link them if he wants. The AI doesn't need to enforce sequencing. |

### 4. Separate Self-Improvement App / Dashboard Page

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Adding a /self-improvement page to Mission Control creates a destination Andy has to visit. He already has Slack DM + morning briefing as his primary interface. A new page would go unused within 2 weeks (Follow Thru 4 = finds shortcuts, resists adding new tools). |
| **What to Do Instead** | Surface everything through existing touchpoints: morning briefing, evening recap, weekly review, Slack DM conversation. Mission Control can optionally show a habit chart later, but it should not be the primary interface. |

### 5. Automated Goal Scoring (0.0-1.0 OKR Grading)

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Google's 0.7 = success OKR scoring model works for teams with calibrated expectations. For personal goals, it adds complexity without value. "Did I achieve this? Mostly yes, with caveats" is more useful than "0.65." |
| **What to Do Instead** | Traffic light status: on track / at risk / off track. Andy updates manually based on judgment. Bob surfaces the status; Andy owns the assessment. |

### 6. Multiple Daily Prompts / Push Notification Overload

| Aspect | Detail |
|--------|--------|
| **Why Avoid** | Prompt fatigue is the #1 killer of journaling apps. Multiple daily prompts train users to dismiss notifications. The existing system already sends morning briefing, evening recap, heartbeats -- adding 3+ more self-improvement prompts would overwhelm the Slack DM channel. |
| **What to Do Instead** | ONE evening reflection prompt. ONE morning commute prompt. Both optional, no guilt if skipped. The system should feel like a friend checking in, not a task manager demanding attention. |

---

## Feature Dependencies

```
Habit Tracking (coordination.db tables)
    |
    +-- enables --> Morning Briefing Self-Improvement Section
    |                  (shows streak counts, completion rates)
    |
    +-- enables --> Evening Accountability Nudge
    |                  (checks if habits logged today)
    |
    +-- enables --> Weekly Review Habit Report
    |                  (completion rates, streak history)
    |
    +-- combined with Oura health.db --> Oura-Correlated Habit Insights
                                           (requires 4+ weeks of habit data)

Goal Tracking (coordination.db tables)
    |
    +-- enables --> Morning Briefing Goals Section
    |                  (shows quarterly OKR status)
    |
    +-- enables --> Weekly Review Goal Progress
                       (traffic light status, KR progress)

Journal Prompt System
    |
    +-- requires --> Prompt library (JOURNAL_PROMPTS.md reference doc)
    |
    +-- stores in --> coordination.db or daily memory logs
    |
    +-- enables --> Pattern Detection (after 4+ weeks of entries)
    |
    +-- enables --> Commute Prompt Personalization
                       (follow-up on unresolved reflections)

Morning Commute Prompts
    |
    +-- requires --> Voice notes pipeline (already working)
    +-- requires --> Habit tracking (for personalized topics)
    +-- requires --> Goal tracking (for OKR-related prompts)
    +-- requires --> Journal entries (for follow-up topics)
    +-- requires --> Oura data (for energy-based prompts)
    +-- requires --> Calendar (for pre-meeting reflection)

Weekly Review (Upgraded)
    |
    +-- requires --> Habit tracking data (streak reports)
    +-- requires --> Goal tracking data (OKR check-in)
    +-- requires --> Journal entries (pattern detection)
    +-- requires --> Oura weekly trends (energy pattern analysis)
    +-- modifies --> Existing weekly-review cron and reference doc
```

### Dependency Summary

- **Habit tracking is the foundation.** Everything else references it. Build first.
- **Goal tracking is independent of habits** but appears in the same surfaces (briefing, weekly review). Can be built in parallel.
- **Journal prompts are standalone** but feed pattern detection. Build early to start accumulating data.
- **Commute prompts depend on everything else.** They personalize based on habits, goals, journal entries, Oura, and calendar. Build last.
- **Weekly review upgrade is the integration point.** Pulls from all other systems. Build after habit + goal tracking are delivering data.

---

## MVP Recommendation

### Phase 1: Foundation (Habit Tracking + Goal Tracking + DB Schema)

Build the data layer first. Everything else reads from it.

1. **Habit tracking tables in coordination.db** -- habits + habit_completions tables
2. **Goal tracking tables in coordination.db** -- goals + key_results tables
3. **HABIT_TRACKER.md reference doc** -- instructions for Bob on how to log habits, calculate streaks, handle forgiveness
4. **GOAL_TRACKER.md reference doc** -- instructions for Bob on OKR management
5. **Seed initial habits and Q1 goals** via Slack DM conversation with Bob

**Why first:** No insights, prompts, or reviews are useful without data to reference. The schema is small, the reference docs follow established patterns, and seeding can happen in a single conversation.

### Phase 2: Briefing + Prompts (Morning Section + Evening Reflection)

Surface the data and start collecting reflection entries.

1. **Add self-improvement section to morning briefing** -- habit streaks, goal status, Oura summary (already there but now contextualized alongside habits)
2. **Create journal prompt system** -- JOURNAL_PROMPTS.md reference doc with prompt library, evening delivery cron (1x/day, ~5pm PT)
3. **Store journal responses** -- in coordination.db or appended to daily memory logs

**Why second:** The briefing section is trivial once data exists (LOW complexity). Journal prompts start the 4-week data accumulation clock for pattern detection. Start early.

### Phase 3: Weekly Review Upgrade + Accountability

Transform the existing review and add gentle nudges.

1. **Restructure weekly-review reference doc** -- personal retrospective format (Wins, Challenges, Energy Patterns, Habits, Goals, Focus)
2. **Add Oura weekly energy trends** -- readiness/sleep averages, best/worst days
3. **Add evening accountability nudge** -- conditional logic in evening recap: mention unlogged habits once, never nag

**Why third:** Weekly review needs 1-2 weeks of habit/goal data to be meaningful. Accountability nudge is trivial but should come after the habit system proves useful (avoid nudging about a system the user hasn't adopted yet).

### Phase 4: Commute Prompts + Correlations (Differentiators)

The premium layer -- personalized, voice-first, data-correlated.

1. **Morning commute prompt cron** -- COMMUTE_PROMPTS.md reference doc, delivered ~7:30am PT, personalized based on goals/habits/journal/Oura/calendar
2. **Voice note processing for self-improvement content** -- extend existing pipeline to extract habit completions and reflections from voice transcriptions
3. **Oura-correlated habit insights** -- weekly review sub-section with correlation analysis (requires 4+ weeks of habit data)
4. **Pattern detection across journal entries** -- QMD search during weekly review to surface recurring themes

**Why last:** Commute prompts are the most complex feature (many dependencies). Oura correlations need 4+ weeks of habit data. Pattern detection needs 4+ weeks of journal entries. Both naturally defer to Phase 4 timing.

### Defer Indefinitely

- Per-habit analytics dashboard in Mission Control (YAGNI until habits prove sticky)
- Habit sharing / social accountability (single user, no social graph)
- AI-generated habit suggestions ("you should try X") -- paternalistic, Andy decides his own habits
- Integration with external habit apps (Streaks, Habitica) -- Bob IS the habit app

---

## Cron Schedule Impact

New crons needed (additions to existing 25):

| Cron | Time (PT) | Agent | Frequency | Isolated | Notes |
|------|-----------|-------|-----------|----------|-------|
| commute-prompt | 7:30am | main | weekdays | yes | Before commute, sends 1-2 discussion topics |
| journal-prompt | 5:00pm | main | daily | yes | Evening reflection prompt |
| habit-nudge | (none -- embedded in evening-recap) | -- | -- | -- | Conditional: only if no habits logged |

**NOT adding a separate habit-nudge cron.** The evening recap already fires daily. Add conditional habit mention to the evening-recap reference doc instead. Avoid cron proliferation.

**Total cron count after v2.10:** 27 (from 25). Only 2 genuinely new crons. The habit nudge piggybacks on evening-recap.

---

## Voice-First UX Patterns

### Commute Voice Notes: Design Principles

1. **Prompt arrives before the commute, not during.** Andy reads 1-2 topics on his phone before getting in the car. The seed is planted; the voice note happens organically.

2. **No required format for voice responses.** Andy speaks naturally; Bob extracts structure. "Yeah so about that reading goal, I finished the fourth book last night, the one about systems thinking, it was actually really relevant to the content pipeline..." -- Bob extracts: book #4 complete, update KR.

3. **Transcription is the bottleneck, not generation.** Voice notes go through Google Drive > Whisper. Processing delay is acceptable (minutes to hours). The commute prompt doesn't expect an immediate response.

4. **Voice can log habits.** "I did my morning meditation and went for a run" in a voice note should be parseable by Bob as two habit completions. This extends the existing voice notes pipeline with habit-extraction logic.

5. **Fallback to Slack DM.** If Andy doesn't record a voice note, the commute prompt is just a message in Slack. It works either way. Voice is the premium path, not the only path.

### Slack DM: Natural Language Patterns

Bob should understand these patterns for habit logging:
- "I meditated today" -> log meditation completion for today
- "Ran 3 miles" -> log exercise completion for today
- "I read for 30 minutes yesterday" -> log reading completion for yesterday
- "Skip meditation today, sick" -> mark as forgiven skip (don't break streak)
- "How are my habits doing?" -> show current streaks and weekly stats
- "Add a new habit: cold shower, daily" -> create new habit

Bob should understand these patterns for goal updates:
- "Update reading KR to 4 books" -> set current_value to 4
- "My writing goal is at risk" -> update status to at_risk
- "What are my OKRs?" -> show current quarter goals with KR progress

---

## OpenClaw Community Patterns

### ClawhHub Habit Skills

Two relevant skills exist in the ClawhHub registry:

1. **tralves/habit-flow-skill (HabitFlow)** -- AI-powered atomic habit tracker with natural language logging, streak tracking with 1-day forgiveness, smart reminders, and coaching based on Atomic Habits principles. Requires Node.js 18+ and npm. Uses persona-based coaching.

2. **Generic habit-tracker skill** -- Simpler version, `/habits` trigger, classified as Productivity, "Easy" difficulty. No external dependencies.

**Recommendation: Do NOT install either ClawhHub skill.** Instead, build a custom implementation using the reference doc pattern (HABIT_TRACKER.md) + coordination.db. Reasons:

- ClawhHub skills add YAML frontmatter complexity and potential skill conflicts
- Both skills assume their own storage backend; we need integration with coordination.db, health.db, and the existing cron/briefing system
- The reference doc pattern is proven across 8+ existing protocol docs (HEARTBEAT.md, MEETING_PREP.md, DAILY_FLUSH.md, etc.)
- Custom implementation keeps habit data queryable by Mission Control, weekly review, and morning briefing
- Andy already has 21 skills deployed; more skills = more YAML frontmatter bugs to debug

The ClawhHub skills are useful as design references for streak calculation logic and natural language parsing patterns, but the implementation should be native to this system.

### Established OpenClaw Patterns to Follow

| Pattern | How to Apply |
|---------|-------------|
| **Reference doc in workspace** | HABIT_TRACKER.md, GOAL_TRACKER.md, JOURNAL_PROMPTS.md, COMMUTE_PROMPTS.md in ~/clawd/agents/main/ |
| **Cron + reference doc** | Cron payload: "Follow COMMUTE_PROMPTS.md"; instructions in the doc |
| **coordination.db for structured data** | Habits, completions, goals, key results in coordination.db |
| **Memory system for unstructured data** | Journal responses appended to daily memory logs; QMD indexes for pattern search |
| **Morning briefing section** | Add Section 12: Self-Improvement (after existing 11 sections) |
| **Conditional delivery** | Habit nudge only fires if no completions logged; commute prompts only on weekdays |
| **Isolated cron sessions** | New crons use isolated=true, Haiku model (rate limit management) |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Andy stops logging habits after 2 weeks | MEDIUM (Quick Start 7 = fast starts, sometimes fast stops) | Streak data stalls, weekly reviews become stale | 1-day forgiveness, minimal friction logging, voice note extraction. If abandoned, system gracefully degrades -- briefing section just says "no active habits" |
| Cron overload (27 crons on t3.small) | LOW | Rate limit pressure, CPU contention | 2 new crons only; both Haiku/isolated; stagger off existing heartbeat windows |
| Journal prompt fatigue | MEDIUM | User ignores prompts, system feels naggy | ONE prompt per day, optional, varied categories. No follow-up if skipped. |
| Oura correlation noise (insufficient data) | HIGH in first month | Misleading correlations | Require 4+ weeks minimum data; Bob explicitly says "not enough data yet" |
| Voice note parsing errors | MEDIUM | Habit completions from speech misinterpreted | Always confirm via Slack DM: "I heard you completed meditation and exercise today -- correct?" |
| Morning briefing gets too long | LOW | Andy skims/skips the briefing | Self-improvement section capped at 4 lines maximum |

---

## Sources

### HIGH confidence
- Andy's cognitive/personality profile (CliftonStrengths, Kolbe, MBTI, EOS) -- from CLAUDE.md global instructions
- Existing system inventory (25 crons, 6 databases, 21 skills, 7 agents) -- from PROJECT.md
- Voice notes pipeline architecture -- from MEMORY.md (Google Drive > Whisper > coordination.db)
- Oura Ring data model (sleep, readiness, HRV, HR in health.db) -- from PROJECT.md validated features
- Reference doc pattern (established across 8+ workspace protocol docs) -- from ARCHITECTURE.md

### MEDIUM confidence
- [HabitFlow skill (tralves/habit-flow-skill)](https://github.com/openclaw/skills/blob/main/skills/tralves/habit-flow-skill/SKILL.md) -- streak forgiveness, natural language logging patterns
- [Gamification research](https://www.cohorty.app/blog/gamification-in-habit-tracking-does-it-work-research-real-user-data) -- 67% abandonment with heavy gamification by week 4
- [VoiceNotes AI](https://www.getvoicenotes.app/) -- voice journaling UX patterns, commute use case validation
- [Reflection.app](https://www.reflection.app/) -- AI journaling prompt categories, personalization patterns
- [Max Frenzel daily AI review system](https://maxfrenzel.medium.com/the-daily-ai-enabled-review-system-that-changed-how-i-work-51944a948caf) -- structured review format (mood, activities, goals, blockers)
- [Oura Ring API](https://cloud.ouraring.com/v2/docs) -- available data points for correlation analysis
- [Tability personal OKRs](https://www.tability.io/okrs-examples/okrs-for-personal-development) -- simple personal OKR framework
- [Weekly review AI template](https://noteplan.co/templates/ai-weekly-review-planning-template) -- structured review sections

### LOW confidence
- Commute prompt timing (7:30am PT assumed based on typical Bay Area commute patterns -- actual timing TBD with Andy)
- Voice note habit extraction accuracy (depends on Whisper transcription quality + Bob's NLU parsing -- untested)
- Optimal journal prompt frequency (1x/day is industry standard but Andy's engagement pattern is unknown)

---

*Feature research for: pops-claw v2.10 Self-Improvement Companion*
*Researched: 2026-03-16*
*Replaces: FEATURES.md for v2.9 Memory System Overhaul (shipped)*
