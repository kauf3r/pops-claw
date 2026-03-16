# Pitfalls Research

**Domain:** Self-improvement companion features added to existing OpenClaw AI agent system (v2.10)
**Researched:** 2026-03-16
**Confidence:** HIGH (grounded in production system metrics, behavioral research on habit tracker abandonment, and 9-milestone history of this specific deployment)

> This file supersedes the v2.9 memory system PITFALLS.md.
> v2.9 pitfalls (QMD bootstrap, compaction tuning, OOM, gateway restart) remain relevant
> as infrastructure constraints and are referenced where they compound with v2.10 risks.

---

## Critical Pitfalls

### Pitfall 1: The Self-Improvement System Itself Becomes Another Thing to Maintain

**What goes wrong:**
You add habit tracking, journal prompts, goal tracking, weekly reviews, and commute prompts. That is 5 new feature surfaces layered onto a system already running 25 crons, 7 agents, 6 databases, and 21 skills. Within 2-3 weeks, the self-improvement features start feeling like obligations rather than tools. The daily journal prompt goes unanswered. The habit nudge becomes noise. The weekly review is skipped because "it was a busy week." The system dutifully continues sending prompts and nudges into the void, creating guilt rather than growth. Research shows 92% of habit tracking attempts fail within 60 days, and 52% of users drop off within 30 days.

**Why it happens:**
Self-improvement tools fail when they add friction to the user's day rather than removing it. The system is designed by the builder (you) during a motivated planning phase. Two weeks later, the motivation curve dips, and every prompt becomes an interruption. The system cannot distinguish between "user is busy today" and "user has abandoned this." It keeps nudging. The nudges create guilt. The guilt creates avoidance. The avoidance becomes permanent abandonment. This is the "what-the-hell effect" documented in behavioral psychology: one missed day triggers total abandonment, especially with streak-based tracking.

**How to avoid:**
- Start with ONE feature (habit tracker OR journal prompts, not both). Ship it. Use it for 14 days. Only add the next feature if the first one is actually being used.
- Build a "silence escalation" ladder: if a prompt gets no response for 2 days, reduce frequency. After 5 days of silence, pause that feature entirely and send a single "I've paused your habit nudges. DM me when you want to restart." No guilt, no pressure.
- Never launch all 5 features simultaneously. The v2.10 milestone should be phased over 4-6 weeks of actual usage, not 4-6 days of implementation.

**Warning signs:**
- More than 3 unanswered prompts in a row for any feature
- "I'll catch up on it later" responses to Bob's nudges
- Features implemented in rapid succession without 7+ days of actual usage between each
- Planning doc says "and then we'll also add..." more than twice

**Phase to address:** First phase of v2.10. Scope must be constrained to 1-2 features maximum. The phasing IS the prevention.

---

### Pitfall 2: Streak-Based Habit Tracking Creates Fragile Motivation That Collapses on First Miss

**What goes wrong:**
Habit tracker uses streaks (consecutive days) as the primary metric. User builds a 23-day meditation streak. Day 24, a travel day, meditation is skipped. The streak resets to 0. Research from Health Psychology shows people who break a streak are 47% more likely to abandon the behavior entirely. People who think in binary terms (perfect/broken) are 3.2x more likely to abandon goals after a single perceived failure. The "what-the-hell effect" turns a single missed day into total abandonment.

**Why it happens:**
Streaks exploit loss aversion — the longer the streak, the more painful the break. This works as motivation UNTIL the inevitable break. Then the same loss aversion that drove the streak makes the zero feel catastrophic. The psychological cost of "lost progress" overwhelms the rational understanding that 23 out of 24 days is excellent consistency. Andy's ENFP-A profile (Prospecting 81%, Adaptability #5) means rigid streak systems will clash with his natural flexibility. Prospecting types resist rigid systems and are more likely to feel trapped by them.

**How to avoid:**
- Use consistency rate (%) instead of streaks as the primary metric. "You meditated 6 of the last 7 days (86%)" is resilient to single misses.
- If showing streaks at all, show "best streak" and "current streak" as secondary stats, not the headline number.
- Implement "grace days" — one missed day per week doesn't break anything. The system treats 6/7 as a perfect week.
- Never reset to zero. Show total completions alongside any streak metric.
- A 2023 Journal of Behavioral Medicine study found users of non-streak trackers were 3.2x more likely to maintain consistent tracking at 6 months.

**Warning signs:**
- User stops logging habits after a missed day (the missed day is the canary)
- Habit tracker conversation starts including words like "behind," "catch up," or "make up for"
- Bob's nudge after a break sounds like "your streak ended" rather than "you've completed X of the last Y days"

**Phase to address:** Habit tracker design phase. Consistency-rate-first design is a hard requirement, not a nice-to-have.

---

### Pitfall 3: Cron Proliferation Exhausts Claude Pro 200 Rate Limits

**What goes wrong:**
v2.10 adds new crons: daily habit nudge, daily journal prompt, morning commute prompt, weekly review, weekly goal check-in. That is 5+ new crons on top of 25 existing ones. The new crons use Sonnet or Opus because they need to generate personalized, contextual prompts (not simple Haiku-level messages). During peak morning hours (6-9 AM PT), the existing morning briefing (Opus), meeting-prep-scan (Sonnet), heartbeats x4 (Haiku), and the new habit nudge + journal prompt + commute prompt all fire within a 90-minute window. Claude Pro 200 has undisclosed rate limits per model tier, and this burst pattern risks hitting them — causing silent failures, queued responses, or degraded quality.

**Why it happens:**
Each feature is designed in isolation. The habit nudge "needs to fire at 7 AM to catch the morning routine." The journal prompt "should arrive with the morning briefing." The commute prompt "must be ready by 8 AM." Nobody maps the aggregate load. The existing system already has the morning briefing at 6 AM PT and meeting-prep at 8 AM and 1 PM PT. Adding 3 more crons to the 6-9 AM window creates a burst that the rate limiter may throttle.

**How to avoid:**
- Map ALL existing crons on a timeline before adding any new ones. Identify the 6-9 AM PT burst window.
- Bundle new self-improvement content into the existing morning briefing as new sections (Section 12: Today's Habits, Section 13: Reflection Prompt) rather than creating separate crons. This is the single most impactful mitigation — zero new crons, zero new rate limit pressure.
- If separate crons are needed, use Haiku for notification-style messages ("Time to log your morning habits") and reserve Sonnet for the weekly review that requires synthesis.
- Stagger any new crons at :15, :25, :35 — avoid the :00/:02/:04/:06 heartbeat window and the :00 morning briefing.

**Warning signs:**
- Any new cron scheduled between 6:00 and 6:30 AM PT (morning briefing window)
- More than 2 new crons using Sonnet or Opus tier
- Total cron count exceeding 30 (currently 25 — budget is tight)
- Bob's responses arriving late or truncated during morning hours

**Phase to address:** Architecture/design phase. Cron timeline mapping is a prerequisite before any implementation. The "bundle into morning briefing" pattern should be the default, with separate crons justified only by strong timing requirements.

---

### Pitfall 4: Journal Prompt Fatigue — Same Prompts, Declining Engagement

**What goes wrong:**
Bob sends a daily journal prompt. Week 1: "What are you grateful for today?" Week 2: "What's one thing you'd improve about yesterday?" Week 3: the prompts start feeling repetitive. The user gives shorter answers. By week 5, the prompts go unanswered. Research shows that after 12 weeks of AI-generated daily prompts, "grateful," "proud," and "energized" appeared 92 times in journal entries, while "angry," "confused," "unsure," and "tired" appeared zero times — the system optimized for positivity, not genuine reflection.

**Why it happens:**
Three failure modes compound:
1. **Template exhaustion:** LLMs generating daily prompts converge on a narrow set of themes. "Gratitude" and "goals" dominate. Deeper prompts (conflict, fear, uncertainty, boredom) are avoided because the model optimizes for engagement, not growth.
2. **Context blindness:** The prompt doesn't adapt to what's actually happening in the user's life. A generic "what are you grateful for?" on a day when coordination.db shows 3 overdue tasks and Oura shows poor sleep is tone-deaf.
3. **Response fatigue:** Even good prompts become stale through daily repetition. The act of responding to a daily prompt becomes rote rather than reflective.

**How to avoid:**
- Context-aware prompts only. Bob should reference today's Oura data, calendar, and task state when generating the prompt. "Your HRV was 15% below your baseline — how are you feeling physically?" beats "What are you grateful for today?"
- Rotate prompt categories on a weekly cycle: Monday (goals), Tuesday (energy/health), Wednesday (relationships), Thursday (creative), Friday (weekly retrospective). Never the same category two days in a row.
- Include "negative space" prompts regularly: "What's frustrating you right now?", "What are you avoiding?", "What decision are you postponing?" These feel uncomfortable to generate but produce the most valuable reflection.
- Allow "skip" without guilt. Bob should accept "pass" or "not today" without follow-up. No "are you sure?" No streak penalty.
- Vary the medium: some days a prompt, some days a multiple-choice check-in ("Energy level: 1-5"), some days just "How's it going?" in conversational tone.

**Warning signs:**
- Journal responses getting shorter (>50% reduction in word count over 2 weeks)
- "Good" or "fine" as complete responses
- Same themes appearing in >40% of prompts over a 2-week window
- No prompts referencing health data, calendar events, or recent task completions

**Phase to address:** Journal prompt design phase. Prompt generation system must have access to Oura, calendar, and task state. Static prompt lists are unacceptable.

---

### Pitfall 5: t3.small Resource Ceiling — Another SQLite DB + Crons Tips the Balance

**What goes wrong:**
v2.10 adds a new `habits.db` (or extends coordination.db with new tables). The existing system runs 6 SQLite databases in WAL mode. Mission Control reads all of them via better-sqlite3. The gateway writes to them via Docker bind-mounts. QMD runs embedding models consuming ~300MB. Adding a 7th database, new cron jobs with Sonnet/Opus calls, and potentially a new Mission Control page increases the memory footprint on a machine with 2GB RAM + 2GB swap that has already experienced OOM events. The 2GB swap means the system technically has 4GB but swap access is 10-100x slower than RAM, causing latency spikes during page faults.

**Why it happens:**
Each individual addition is small. A new SQLite database is ~20KB. A new cron is negligible. A new Mission Control page adds maybe 5MB to the Next.js process. But the system is already near its ceiling — previous milestones have documented OOM events (Pitfall 3 in v2.9 PITFALLS.md), and the 2GB swap was added as a mitigation, not a solution. The problem is cumulative: 6 DBs in WAL mode each hold a read-ahead cache, the gateway buffers session state, QMD holds vector indices in memory, Docker containers have their own memory overhead, and Mission Control's Node.js process runs continuously.

**How to avoid:**
- Do NOT create a new database file. Add habit/goal/journal tables to the existing `coordination.db` which is already bind-mounted to all agents and read by Mission Control. One less WAL-mode file, one less file handle, zero new bind-mount configuration.
- Measure memory baseline before v2.10 work starts: `free -m` during peak (6-9 AM PT) and off-peak. Document the headroom.
- Set a hard rule: if available memory during peak drops below 300MB, stop adding features and optimize first.
- If a new Mission Control page is added, ensure it uses the existing SWR polling pattern (30s) and doesn't add a new database connection pool.

**Warning signs:**
- `free -m` shows available < 400MB during off-peak hours (already in trouble)
- Swap usage consistently above 500MB (system is paging constantly)
- Gateway latency increases during morning briefing window
- Mission Control pages loading slowly (Next.js process competing for memory)

**Phase to address:** Database/schema design phase. "Extend coordination.db" is the default. "New database file" requires explicit justification and a memory impact assessment.

---

### Pitfall 6: Voice Notes Pipeline Backlog Compounds — 28 Unprocessed Notes Already Exist

**What goes wrong:**
The morning commute prompt feature assumes voice notes will be processed and available for Bob to reference. But `process-voice-notes.py` already has a 28-note backlog in Google Drive. The Whisper transcription service uses OpenAI API, and the OpenAI API quota is exhausted (documented in MEMORY.md). Adding "respond to commute prompts via voice notes" without fixing the existing pipeline creates a situation where the user records voice responses that never get transcribed, never get stored in coordination.db, and never influence Bob's understanding. The feature appears to work (recording is easy) but the feedback loop is broken.

**Why it happens:**
Voice input is the easiest part of a voice pipeline. Recording a voice note takes 30 seconds. Transcribing it requires an API call. Storing and indexing it requires a working pipeline. The voice-memory-v2 Vercel app is dormant with 28 unprocessed .m4a files. The OpenAI Whisper API is quota-exhausted. The `process-voice-notes.py` cron runs every 2 hours but has nothing to process because the pipeline upstream is broken. Designing "commute prompts answered via voice notes" without first confirming transcription works end-to-end is building on a broken foundation.

**How to avoid:**
- Fix the voice notes pipeline BEFORE designing any voice-input features. Clear the 28-note backlog. Verify Whisper transcription works (or switch to a free/local alternative).
- If OpenAI API quota cannot be restored, evaluate local Whisper (whisper.cpp runs on CPU but will be slow on t3.small) or Superwhisper ($8/mo, already noted in PROJECT.md constraints as optional).
- Alternatively, accept that voice notes are OUT OF SCOPE for v2.10 (they're listed in PROJECT.md as "evaluate at day 60") and design commute prompts with text-based response only.
- The simplest path: commute prompts delivered via Slack DM, responded to via text in Slack. No voice pipeline dependency at all.

**Warning signs:**
- Any design doc that says "user responds via voice note" without addressing the transcription pipeline
- voice-memory-v2 backlog growing (currently 28, check periodically)
- `process-voice-notes.py` cron showing 0 files processed for consecutive runs
- OpenAI API quota still exhausted at time of implementation

**Phase to address:** Pre-implementation audit phase. Voice pipeline health is a gate check before any voice-input feature is scoped.

---

### Pitfall 7: Notification Fatigue — Bob Becomes the Nag You Ignore

**What goes wrong:**
Bob currently sends: morning briefing, evening recap, heartbeat acknowledgments, content pipeline notifications, email notifications, YOLO build results, memory health alerts, and meeting prep summaries. Adding habit nudges, journal prompts, goal check-ins, and commute prompts means Bob could send 8-12 proactive messages per day. Research shows the average smartphone user receives 46-63 push notifications per day, and 55% of users cite "notification overwhelm" as their primary reason for digital detoxes. At some point, Bob's messages stop being helpful and start being noise. The user begins ignoring ALL of Bob's messages — including the useful morning briefing — because the Slack DM channel is flooded.

**Why it happens:**
Each notification is individually justified. The morning briefing is essential. The habit nudge is helpful. The journal prompt is valuable. The commute prompt is timely. But the aggregate effect is that Bob's Slack DM becomes a wall of unread messages. The user opens the DM, sees 6 messages from Bob, and closes it without reading any of them. Frequent notifications increase cognitive load by 37% and reduce task completion efficiency by 28%.

**How to avoid:**
- Set a hard cap: Bob sends a maximum of 4 proactive messages per day via DM. Morning briefing counts as 1 (even though it's long). Everything else competes for the remaining 3 slots.
- Bundle aggressively. Self-improvement content goes INTO the morning briefing, not alongside it. "Section 12: Today's Focus" with habit status + reflection prompt + commute topic is one message, not three.
- Use a priority queue. If there's a meeting prep alert AND a habit nudge AND a journal prompt all due at 8 AM, send meeting prep (time-sensitive), defer habit nudge to 10 AM, skip journal prompt for today.
- Deliver some content via email instead of DM (the dual-delivery infrastructure from v2.2 already exists). Journal prompts could be a quiet email, not a Slack notification.
- Implement "quiet hours" — no proactive messages between 6 PM and 6 AM PT except urgent alerts.

**Warning signs:**
- More than 5 unread messages from Bob in the Slack DM at any given time
- User responds to morning briefing but ignores subsequent messages
- Bob sends more than 4 proactive DMs in a single day
- User starts muting the Bob DM channel

**Phase to address:** Architecture/design phase. Message budget and bundling strategy must be defined before any notification is implemented.

---

### Pitfall 8: Weekly Review Duplicates Existing Weekly Review Cron

**What goes wrong:**
v2.10 targets "weekly review — structured retrospective with Oura energy patterns, what went well / improve." The system already has a `weekly-review` cron that runs weekly. Without careful scoping, the new "self-improvement weekly review" either duplicates the existing review (creating two weekly summaries) or attempts to extend it in ways that make the existing review fragile. Worse, two separate weekly reviews on the same day (one for system status, one for personal reflection) feels like homework.

**Why it happens:**
New milestone features are designed by looking at what's missing, not what already exists. The existing weekly review covers system health, agent status, and operational metrics. The new one is supposed to cover energy patterns and personal reflection. They feel different in design, but to the user they're both "long messages from Bob on Sunday that require reading." The distinction is clear in a planning doc but invisible in the Slack DM.

**How to avoid:**
- EXTEND the existing weekly review, don't create a second one. Add new sections: "Energy Patterns" (Oura weekly trends), "Habit Consistency" (this week's tracking summary), "Reflection" (what went well / what to improve). One weekly review, richer content.
- If the combined review becomes too long (>2000 words), split into two parts delivered 2 hours apart: "Weekly Ops Review" at 9 AM and "Weekly Reflection" at 11 AM. Still one cron, two deliveries.
- Inventory ALL existing crons that touch self-improvement-adjacent domains (morning briefing health section, evening recap, weekly review) and map overlaps before designing new content.

**Warning signs:**
- Two separate crons both named something like "weekly-review" and "weekly-reflection"
- User receives two long weekly messages from Bob on the same day
- New cron duplicates data already in existing weekly review (Oura data appears in both)

**Phase to address:** Design phase. Existing cron inventory and overlap mapping is a prerequisite.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store habits in a flat JSON file instead of SQLite | Fast to implement, no schema design | No querying, no trends, no Mission Control integration, manual backup | Never — coordination.db already exists and is bind-mounted everywhere |
| Hardcode habit list in a reference doc | Bob reads it and knows what to track | Cannot dynamically add/remove habits, no history of changes, no versioning | Only as a v0 prototype for first 3 days of testing |
| Create one cron per self-improvement feature | Clean separation of concerns | 5 new crons on 25 existing = 30 total. Each one is a rate limit ticket. Morning window becomes a traffic jam | Never — bundle into existing crons (morning briefing, evening recap, weekly review) |
| Skip Oura data integration for journal prompts | Simpler prompt generation | Prompts become generic and repetitive. The whole point of having Oura data is context-aware prompts. Without it, Bob is no better than a static prompt list | Never — Oura integration already exists in morning briefing. Reuse it |
| Use OpenAI Whisper for voice note transcription | Best quality, already coded | API quota exhausted, costs money, external dependency. On t3.small, even local Whisper-tiny adds CPU load | Only if quota is restored AND no local alternative is acceptable |
| Separate habits.db database file | Clean data boundary | 7th SQLite file in WAL mode, new bind-mount config, new Mission Control connection, memory overhead | Only if coordination.db schema becomes unwieldy (unlikely for <10 tables) |

---

## Integration Gotchas

Common mistakes when connecting self-improvement features to existing infrastructure.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Habit tracker + Slack DM | Creating a custom "habit log" syntax that Bob must parse from free-text DMs | Use structured responses: Bob asks "Did you meditate today? (yes/no)" and parses the binary. Free-text habit logging fails because LLM parsing is inconsistent across sessions |
| Journal prompts + Oura API | Fetching Oura data in the journal prompt cron separately from morning briefing | Reuse the Oura data already fetched by morning briefing. Store today's health summary in coordination.db during briefing, reference it in journal prompt. One API call, not two |
| Goal tracker + morning briefing | Adding a 14th section to an already 11-section morning briefing | Cap morning briefing at 12 sections maximum. Goal status should replace or merge with the tasks section, not append after it |
| Weekly review + memory flush | Running weekly review and daily memory flush on the same day without coordination | Weekly review day (Sunday) should trigger both the review AND an enhanced flush that captures the review content. Schedule flush 2 hours after review to capture it |
| Commute prompts + meeting prep | Both target 7-8 AM PT window | Merge: meeting prep for the day IS the commute topic on days with meetings. Standalone reflection prompt only on meeting-free mornings |
| Habit data + Mission Control | Creating a new /habits page before the data model stabilizes | Add habit data to the existing /analytics page first. New page only after 30+ days of data and confirmed schema |

---

## Performance Traps

Patterns that work initially but degrade as usage accumulates.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Querying all habit history for trend calculation | Response latency increases, morning briefing slows | Use rolling 30-day window for daily queries, 90-day for weekly. Archive older data to a summary row | After 6 months of daily habit data (~180 rows per habit) |
| QMD indexing journal entries as memory files | QMD collection grows with low-signal entries, search quality degrades | Journal entries go in coordination.db, NOT as .md files in the workspace. Only curated insights go to QMD | After 60+ journal entries dilute the memory-dir-main collection |
| Morning briefing Opus session grows with more sections | Token usage per briefing increases, pushing against rate limits | Set a token budget for the briefing (target: under 4000 output tokens). New sections must displace, not append | When briefing consistently exceeds 3000 words |
| Habit nudge cron retries on failure | Failed nudge retries at next interval, stacking with the next scheduled nudge | Single-attempt delivery with bestEffort=true. If it fails, skip. No retry. The next scheduled nudge covers it | First time cron delivery fails during rate limit window |
| Dashboard SWR polling habits table | More tables polled = more reads = more file handle contention | Habits data included in existing coordination.db poll, not a separate endpoint | When Mission Control polls 7+ database files simultaneously |

---

## UX Pitfalls

Common user experience mistakes in self-improvement companion design.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Tracking too many habits at once | Overwhelm. Research shows juggling multiple goals reduces motivation to stick with any of them. 16 habits to track weekly leads to immediate abandonment | Start with maximum 3 habits. Add one new habit only after 14 consecutive days of tracking the existing ones |
| Asking "how are you feeling?" every day | Becomes rote. User types "good" without thinking. Zero insight value after week 1 | Ask specific, data-informed questions: "Your sleep was 5.2 hours — shorter than usual. What kept you up?" Context transforms generic into meaningful |
| Goal check-in as interrogation | Weekly "did you make progress on Q1 OKR 2.3?" feels like a performance review from your own AI | Frame as reflection, not accountability: "Your goal was to run 3x/week. You ran twice. What got in the way?" Curious, not judgmental |
| Delivering self-improvement content in the same channel as ops alerts | User associates the DM with "stuff I need to act on" not "time for reflection." Journal prompts get treated as tasks to complete, not invitations to reflect | Consider time-boxing: self-improvement messages only in a designated window (7-8 AM), operational messages at other times. Or use email for reflective content, Slack for actionable content |
| No way to pause without quitting | Life gets busy. User wants to pause habit tracking for a week (vacation, illness, crunch). No pause mechanism means the choice is "keep going" or "stop entirely" | Explicit pause: "Bob, pause habits for 5 days." Bob acknowledges, stops nudging, resumes automatically. No streak penalty, no judgment |
| Celebrating every small win | Constant "Great job!" after checking a habit box feels patronizing by day 5 | Celebrate weekly milestones only. Daily acknowledgment should be neutral: "Logged." Weekly: "86% consistency this week, up from 71% last week" — data, not cheerleading |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Habit tracker:** Habits can be logged via DM — verify that habit data actually persists to coordination.db AND can be queried for weekly trends (not just today's status)
- [ ] **Journal prompts:** Bob sends a daily prompt — verify the prompt references today's actual Oura/calendar data (not a generic question). Check 5 consecutive days for variety
- [ ] **Goal tracker:** Goals are stored and check-ins happen — verify goal progress appears in the morning briefing AND weekly review (not just in a standalone check-in)
- [ ] **Weekly review extension:** New sections added to weekly review — verify the review doesn't exceed 2500 words (beyond that, users skim or skip)
- [ ] **Commute prompts:** Prompt delivered by 7:30 AM — verify it arrives BEFORE morning briefing (not buried after it) and adapts to today's calendar (meeting-heavy days get meeting prep, not generic reflection)
- [ ] **Streak resilience:** User misses a day of habit tracking — verify the system does NOT show "streak broken" or reset to zero. Should show consistency rate instead
- [ ] **Silence handling:** User ignores 3 consecutive journal prompts — verify Bob reduces frequency automatically (not continues sending daily prompts into the void)
- [ ] **Data in Mission Control:** Habit data visible somewhere in the dashboard — verify it's on an existing page (analytics or home), not requiring a new page that nobody visits
- [ ] **No new database files:** All self-improvement data stored in coordination.db — verify no new .db files were created on the EC2 instance
- [ ] **Cron count check:** Post-implementation `openclaw cron list` — verify total cron count is 27 or fewer (25 existing + maximum 2 new, with strong justification for each)

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| User abandons habit tracking after 2 weeks | LOW | Pause all habit nudges. After 7 days, send single message: "Want to try a different approach? Fewer habits, different timing?" Redesign based on what caused abandonment |
| Journal prompts become repetitive/generic | LOW | Replace template-based prompts with Oura-data-driven prompts. Delete existing prompt logic and rebuild with context injection. Takes 1 phase of work |
| Rate limits hit during morning window | MEDIUM | Immediate: shift new crons to 10 AM+ window. Permanent: bundle all self-improvement content into morning briefing sections. May require briefing restructuring |
| Notification fatigue — user muting Bob | HIGH | Drastic reduction: cut to morning briefing + evening recap only for 2 weeks. Slowly reintroduce one feature at a time with explicit user consent. This is a trust-rebuilding exercise |
| OOM from resource accumulation | MEDIUM | SSH in, `free -m`, identify the largest consumer. Usually: reduce Mission Control polling frequency, increase QMD update interval, drop any new database connections. `systemctl --user restart openclaw-gateway.service` as immediate fix |
| Weekly review too long / user skips it | LOW | Split into "quick stats" (300 words, always delivered) + "deep reflection" (opt-in, delivered only if user replies "yes" to "Want the full reflection?"). Two-part delivery, user controls depth |
| Voice pipeline still broken when commute prompts launch | LOW | Switch commute prompts to text-only response via Slack DM. Document voice as deferred to v2.11 or later. No user-facing impact if expectations are set correctly |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| System becomes overwhelming (#1) | Phase 1: Scope and architecture | Only 1-2 features in first implementation phase. Second batch requires 14-day usage evidence |
| Streak fragility (#2) | Habit tracker implementation phase | Show "consistency %" in a test session. Simulate missed day. Confirm no "streak broken" message |
| Cron rate limit exhaustion (#3) | Architecture/design phase | Cron timeline map created. New crons bundled into existing ones. Total count <= 27 |
| Journal prompt fatigue (#4) | Journal prompt implementation phase | 5 consecutive days of prompts reference different data sources. No two prompts in same category back-to-back |
| Resource ceiling (#5) | Database schema design phase | `free -m` baseline documented. All data in coordination.db. No new .db files |
| Voice pipeline broken (#6) | Pre-implementation audit phase | voice-notes-processor cron verified working OR voice explicitly descoped to text-only |
| Notification fatigue (#7) | Architecture/design phase | Message budget (max 4/day) documented. Bundling strategy for morning briefing defined |
| Duplicate weekly review (#8) | Design phase | Single weekly-review cron with extended sections. No second cron created |

---

## Phase-Specific Warnings

Summary of which phases carry the highest pitfall density.

| Phase Topic | Likely Pitfalls | Severity | Mitigation |
|-------------|----------------|----------|------------|
| Architecture/design | Cron proliferation (#3), notification fatigue (#7), duplicate weekly review (#8) | CRITICAL | This phase IS the mitigation. Bad architecture here cascades to every subsequent phase. Spend time here |
| Habit tracker implementation | Streak fragility (#2), tracking too many habits (UX), system overwhelm (#1) | HIGH | Constrain to 3 habits maximum. Consistency rate, not streaks. Build silence handling from day 1 |
| Journal prompt implementation | Prompt fatigue (#4), generic prompts (UX) | HIGH | Context-aware prompts non-negotiable. Must reference Oura/calendar data. Test for 5 days of variety before shipping |
| Database/schema design | Resource ceiling (#5), new DB file (debt) | MEDIUM | Extend coordination.db. Measure memory baseline |
| Voice/commute features | Broken pipeline (#6), OpenAI quota exhaustion | MEDIUM | Gate check: is transcription working? If no, text-only. Don't build on broken foundation |
| Mission Control integration | Performance traps (polling overhead) | LOW | Use existing pages and polling patterns. No new database connections |

---

## Sources

- [Why Do 90% of People Quit Habit Trackers Within 30 Days?](https://mooremomentum.com/blog/why-do-90-of-people-quit-habit-trackers-within-30-days/) — 92% failure rate within 60 days, 52% drop off within 30 days
- [The Psychology of Streaks: Why They Work (And When They Backfire)](https://www.cohorty.app/blog/the-psychology-of-streaks-why-they-work-and-when-they-backfire) — Loss aversion, what-the-hell effect, 47% binge-after-break stat
- [Why Most Habit Streaks Fail](https://mooremomentum.com/blog/why-most-habit-streaks-fail-and-how-to-build-ones-that-dont/) — 3.2x binary thinking abandonment rate, non-streak tracker superiority at 6 months
- [Notification Fatigue Is Real and Getting Worse](https://courier-com.medium.com/notification-fatigue-is-real-and-getting-worse-e4fc248dc29f) — 97% increase in notification volume since 2020, 46-63 notifications/day average
- [How to Reduce Notification Fatigue](https://www.courier.com/blog/how-to-reduce-notification-fatigue-7-proven-product-strategies-for-saas) — 37% cognitive load increase, 28% task completion reduction, user control as mitigation
- [3 Ways to Avoid Betterment Burnout](https://www.psychologytoday.com/us/blog/social-instincts/202503/3-ways-to-avoid-betterment-burnout) — Self-improvement burnout as a recognized psychological pattern
- [I'm Officially Un-tracking My Life](https://www.androidpolice.com/stop-excessive-self-tracking/) — Tracking-induced anxiety, metrics replacing genuine feeling
- [Simple Habit Tracker Apps (No Feature Overwhelm)](https://www.cohorty.app/blog/simple-habit-tracker-apps-no-features-overwhelm-2025) — Feature creep in habit apps, simplicity winning over features
- [Is Using AI to Generate Daily Journal Prompts Encouraging Reflection or Just Creating Busywork](https://www.alibaba.com/product-insights/is-using-ai-to-generate-daily-journal-prompts-encouraging-reflection-or-just-creating-busywork.html) — 92 "grateful/proud" entries vs 0 "angry/confused" entries over 12 weeks
- [AI Agent Rate Limiting Strategies](https://fast.io/resources/ai-agent-rate-limiting/) — Multi-call workflows and burst patterns, workflow-aware quota reservation
- [Your AI Agents Need Cron Jobs, Not Just Event Handlers](https://dev.to/askpatrick/your-ai-agents-need-cron-jobs-not-just-event-handlers-feh) — Cron-based agent maintenance patterns
- PROJECT.md (internal) — 25 crons, 7 agents, 6 databases, t3.small constraints, OpenAI quota exhausted, voice notes backlog
- MEMORY.md (internal) — QMD resource profile, existing cron schedule, swap configuration, OOM history
- v2.9 PITFALLS.md (internal) — OOM patterns, gateway restart behavior, QMD CPU saturation, compaction tuning lessons

---

*Pitfalls research for: Self-improvement companion features (pops-claw v2.10)*
*Researched: 2026-03-16*
*Supersedes: v2.9 Memory System Overhaul PITFALLS.md*
