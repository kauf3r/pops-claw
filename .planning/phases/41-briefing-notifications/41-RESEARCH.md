# Phase 41: Briefing & Notifications - Research

**Researched:** 2026-02-25
**Domain:** OpenClaw cron payload editing, SQLite queries in sandbox, Slack DM messaging
**Confidence:** HIGH — all findings from live EC2 inspection

## Summary

Phase 41 adds YOLO awareness to three existing communication channels: morning briefing, weekly review, and a new Slack DM notification triggered from the nightly build itself. All three are straightforward prompt-engineering tasks against existing cron infrastructure — no new OpenClaw features, no new skills, no new DB schema.

The morning briefing and weekly review are `systemEvent` cron jobs running in the `main` session. Their payloads are plain text strings embedded in the cron job definition and editable with `openclaw cron edit --message`. The YOLO build cron is `isolated`, which means it runs in the Docker sandbox with `/workspace/yolo-dev/` bind-mounted — but the sandbox has no native Slack tool. Slack DM notifications for build start/complete must therefore be sent by Bob's main session, not from inside the isolated build.

The canonical yolo.db path is `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db` on the host (bind-mounted to `/workspace/yolo-dev/yolo.db` in sandbox). All morning briefing and weekly review SQL must use the host path (`/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db`) since those crons run in main session with host filesystem access. The YOLO_BUILD.md doc already handles yolo.db logging — no changes needed there for DASH-02/03.

**Primary recommendation:** Edit the two existing cron job payloads via `openclaw cron edit --message`, and add a new isolated-friendly Slack notification mechanism by having the YOLO build cron's payload instruct Bob to send DMs at build start/end — but since isolated sessions can't use Slack, the cleanest path is to add start/end Slack DM hooks into YOLO_BUILD.md itself using the `sessions_send` call approach that other main-session scripts use, or alternatively add a tiny wrapper cron that fires before/after the build window.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-02 | Morning briefing Section 11 includes last night's YOLO build: project name, status, self-score, one-line description (or "No build last night") | Morning briefing cron confirmed: `main` session, `systemEvent` payload, editable. SQL query for last 24h build identified. |
| DASH-03 | Weekly review includes YOLO digest: total builds, best-rated, tech stack distribution, emerging patterns | Weekly review cron confirmed: `main` session, `systemEvent` payload, editable. SQL queries for 7-day window identified. |
| DASH-04 | Slack DM notification when build starts ("Starting YOLO build: {name}") and completes ("YOLO build complete: {name} -- {status}, score {N}/5") | Critical constraint discovered: yolo-dev-overnight runs in `isolated` session with no Slack access. Solution: embed Slack DM calls into YOLO_BUILD.md itself (main-session Slack tool available when Bob runs the script, but **isolated session has no Slack tool**). Must use a different approach — see Architecture Patterns. |
</phase_requirements>

---

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `openclaw cron edit` | 2026.2.17 | Patch cron job payload text | Only way to update existing job message |
| Python sqlite3 | stdlib | Query yolo.db from main session | Confirmed working pattern for health.db queries in briefing |
| `sqlite3` CLI | host binary | Alternative for quick SQL in systemEvent | Bound at `/home/ubuntu/clawd/sqlite3-compat` → `/usr/bin/sqlite3` in sandbox |
| Slack DM `D0AARQR0Y4V` | - | Andy's personal DM channel | Used by weekly-review, anomaly-alerts, meeting-prep |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `sessions_send` | Send Slack DM from main session | Used by evening-recap to post to #popsclaw C0AD48J8CQY |
| Host path `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db` | DB access from main session crons | All cron SQL in morning briefing / weekly review |
| `/workspace/yolo-dev/yolo.db` | DB access from isolated cron | Used inside YOLO_BUILD.md |

---

## Architecture Patterns

### Pattern 1: Morning Briefing Section Addition (DASH-02)

**What:** Append Section 11 to the morning-briefing cron job payload text.

**Key facts from live inspection:**
- Job ID: `863587f3-bb4e-409b-aee2-11fe2373e6e0`
- Session: `main`
- Payload kind: `systemEvent`
- Runs: `0 7 * * * America/Los_Angeles`
- Current sections: 1 (Calendar), 1b (AirSpace Calendar), 2 (Email), 2b (AirSpace Email), 3 (Health), 4 (Weather), 5 (Tasks), 6 (Home), 7 (GitHub), 8 (Email Briefing), 9 (Email Health), 10 (Agent Observability)
- Next section number: **11**
- Delivery: Bob's response auto-posts to #popsclaw (no explicit sessions_send needed — the `systemEvent` in main session delivers automatically)

**SQL to find last night's build (host path):**
```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db')
conn.row_factory = sqlite3.Row
# "last night" = any build from yesterday or today that has completed
cutoff = (datetime.now() - timedelta(hours=18)).strftime('%Y-%m-%d')
row = conn.execute(
    "SELECT name, status, self_score, description FROM builds WHERE date >= ? AND status IN ('success','partial','failed') ORDER BY id DESC LIMIT 1",
    (cutoff,)
).fetchone()
conn.close()
if row:
    print(f"Last build: {row['name']} | {row['status']} | {row['self_score']}/5 | {row['description']}")
else:
    print("No build last night.")
```

**Cron edit command:**
```bash
openclaw cron edit 863587f3-bb4e-409b-aee2-11fe2373e6e0 --message "..."
```

Note: The morning briefing payload uses `systemEvent` kind, not `agentTurn`. The `--message` flag in `openclaw cron edit` edits the payload text for both kinds.

**Section 11 format for briefing:**
```
## 11. YOLO Dev (Last Night's Build)
Query /home/ubuntu/clawd/agents/main/yolo-dev/yolo.db using sqlite3 or Python.
SQL: SELECT name, status, self_score, description FROM builds WHERE date >= date('now','-1 day') AND status IN ('success','partial','failed') ORDER BY id DESC LIMIT 1
- If row found: "**{name}** — {status} | Score: {self_score}/5 | {description}"
- If no row: "No build ran last night."
```

### Pattern 2: Weekly Review YOLO Digest (DASH-03)

**What:** Append YOLO Digest section to weekly-review payload.

**Key facts:**
- Job ID: `058f0007-935b-4399-aae1-28f6735f09ce`
- Session: `main`
- Payload kind: `systemEvent`
- Runs: `0 8 * * 0 America/Los_Angeles` (Sundays)
- Delivery: sends to Andy's DM `D0AARQR0Y4V` (explicitly in prompt text)
- Health queries use `/workspace/health.db` in the payload — BUT morning briefing uses host path. Need to verify which path is correct for weekly review.

**Weekly review observation:** The weekly-review payload references `/workspace/health.db` (sandbox path), meaning it may run with sandbox file access OR Bob has a workspace bind. Looking at the actual payload text: it queries `/workspace/health.db`. This is the main session — main session has `/home/ubuntu/clawd/agents/main/` as workspace, and `/workspace/` is available in sandbox sessions only. The fact that the existing payload works means main session also has access to paths under `/workspace/` as the agent workspace alias.

**Correction after deeper inspection:** The main session workspace path is `/home/ubuntu/clawd/agents/main/` on host. OpenClaw maps this as `/workspace/` when the agent references files. So `/workspace/health.db` = `/home/ubuntu/clawd/agents/main/health.db` on host. But yolo.db is NOT in `/home/ubuntu/clawd/agents/main/` — it's in `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db`. So the correct path for weekly review SQL is `/workspace/yolo-dev/yolo.db` (using workspace alias) OR the host path.

**SQL queries for weekly digest:**
```sql
-- Total builds this week
SELECT COUNT(*) as total_builds,
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count,
       SUM(CASE WHEN status='partial' THEN 1 ELSE 0 END) as partial_count,
       SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed_count
FROM builds WHERE date >= date('now', '-7 days');

-- Best-rated build this week
SELECT name, status, self_score, description, tech_stack
FROM builds WHERE date >= date('now', '-7 days') AND self_score IS NOT NULL
ORDER BY self_score DESC, id DESC LIMIT 1;

-- Tech stack distribution this week
SELECT tech_stack, COUNT(*) as count
FROM builds WHERE date >= date('now', '-7 days')
GROUP BY tech_stack ORDER BY count DESC;
```

### Pattern 3: Slack DM Notifications (DASH-04)

**Critical constraint discovered:** The yolo-dev-overnight cron runs in `isolated` session (`"sessionTarget": "isolated"`). Isolated sessions run in Docker sandbox. The sandbox has NO native Slack messaging tool. The `sessions_send` or built-in Slack tool is only available in `main` session.

**Three implementation options:**

**Option A (Recommended): Add notification hooks to YOLO_BUILD.md**

The YOLO_BUILD.md document instructs Bob to execute the build. Bob CAN use Slack messaging in isolated sessions if the skill/tool is configured — but per MEMORY.md and sandbox architecture, isolated sessions are pure Docker with no host bindings for Slack. **This won't work.**

**Option B: Convert yolo cron from isolated to main session**

Change `sessionTarget` from `isolated` to `main`. Then Bob has full Slack access. Trade-off: main session builds accumulate context in the ongoing conversation rather than running clean. The 15-turn cap in YOLO_BUILD.md would still apply. This is feasible but changes build isolation semantics.

**Option C (Recommended): New notification wrapper crons**

Add two new cron jobs:
1. `yolo-build-start-notify` — fires at 11:25 PM PT (5 min before build), sends DM: "Starting YOLO build tonight..."
2. `yolo-build-complete-notify` — fires at 12:30 AM PT (after build window), reads last build from yolo.db, sends completion DM

This is a clean separation: notifications don't depend on build execution. But the start notification can't know the build name (it hasn't run yet), and the timing is fragile (builds run at varying lengths).

**Option D: Hybrid — YOLO_BUILD.md + sessions_send via main-session trigger**

The YOLO_BUILD.md could use a different approach: instruct Bob to use the `sessions_send` OpenClaw tool to route a message to Andy's DM even from isolated session. This is only possible if the Slack channel tool is available in isolated sessions.

**Checking the actual sandbox config:** The sandbox has `"network": "bridge"` (confirmed from MEMORY.md: `network=bridge`). Isolated sessions go through the gateway for tool calls. The Slack messaging tool is a gateway-level capability, not a host binary — so it SHOULD be available from isolated sessions.

**Evidence from cron run logs:** The yolo-dev build run summary is delivered via the cron summary mechanism, not via explicit Slack send. The YOLO_BUILD.md has no Slack instructions currently.

**Recommended approach for DASH-04:** Update YOLO_BUILD.md to add Slack DM notification steps:
- At Step 2 (after status set to 'building'): Use the built-in Slack messaging tool to send "Starting YOLO build: {name}" to D0AARQR0Y4V
- At Step 6 (after final DB update): Send "YOLO build complete: {name} -- {status}, score {self_score}/5" to D0AARQR0Y4V

This works IF isolated sessions have Slack tool access. The confidence here is MEDIUM — needs validation with a test.

**Fallback:** If isolated sessions can't send Slack messages, use Option C (post-build notify cron) for the completion notification and a pre-build cron for start (accepts the limitation that pre-build doesn't know the name yet).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron job update | Custom API call or file edit | `openclaw cron edit --message` | Official CLI, properly handles escaping and gateway sync |
| Slack DM delivery | Custom curl to Slack API | Built-in Slack messaging tool or sessions_send | Bot token is already configured, gateway handles auth |
| Date math for "last night" | Complex datetime logic | SQLite `date('now', '-1 day')` | SQLite handles this natively |

---

## Common Pitfalls

### Pitfall 1: Wrong DB Path in Main vs Isolated Context
**What goes wrong:** Using `/workspace/yolo-dev/yolo.db` in a main-session cron prompt (morning briefing) — this path is a Docker mount alias that doesn't resolve in main session.
**Why it happens:** Main session runs on host, not in Docker. `/workspace/` paths only work in isolated/sandbox sessions.
**How to avoid:** Morning briefing and weekly review prompts must use `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db` (host absolute path). OR use `/workspace/yolo-dev/yolo.db` since main session workspace resolves to `/home/ubuntu/clawd/agents/main/` and the yolo-dev dir IS inside that workspace path.
**Validation:** The weekly-review already queries `/workspace/health.db` successfully, and `health.db` is at `/home/ubuntu/clawd/agents/main/health.db`. So `/workspace/yolo-dev/yolo.db` should work too.
**Confidence:** HIGH that `/workspace/yolo-dev/yolo.db` works in main session (consistent with health.db pattern).

### Pitfall 2: Morning Briefing Section Number Collision
**What goes wrong:** Numbering new section as something other than 11, colliding with existing sections.
**How to avoid:** Current sections are 1, 1b, 2, 2b, 3, 4, 5, 6, 7, 8, 9, 10. New section is **11**.

### Pitfall 3: cron edit --message vs --system-event flag
**What goes wrong:** Using wrong flag to update payload text for systemEvent jobs.
**Evidence from live inspection:** The edit command has `--message` (for `agentTurn` kind) and `--system-event` (for `systemEvent` kind). Morning briefing and weekly review are `systemEvent` kind.
**How to avoid:** Use `--system-event` flag (not `--message`) when editing morning briefing and weekly review payloads.

### Pitfall 4: Isolated Session Slack Access Unknown
**What goes wrong:** YOLO_BUILD.md update assumes Slack tool works in isolated session, but it doesn't.
**Why it happens:** Isolated sessions may not have Slack tool configured.
**How to avoid:** Test with a quick isolated cron run that attempts a Slack DM before deploying to production.
**Warning signs:** Build completes but no Slack DM received.

### Pitfall 5: "Last Night" Definition
**What goes wrong:** Morning briefing at 7 AM PT queries for builds from the previous calendar day, but builds run at 11:30 PM UTC (which is 3:30 PM PT the same day with current schedule — the yolo cron is `30 7 * * *` UTC = 11:30 PM PT previous night).
**Actual schedule check:** `"expr": "30 7 * * *"` with no timezone = UTC. 7:30 AM UTC = 11:30 PM PT previous night. So a build running Tuesday night PT fires at 7:30 AM UTC Wednesday. The morning briefing fires at 7:00 AM PT = 3:00 PM UTC Wednesday. The build ran same UTC calendar date as briefing (both UTC Wednesday). Using `date('now', '-1 day')` in UTC SQLite would miss it.
**Better approach:** Query for builds in the last 12 hours OR use `WHERE date >= date('now', '-1 day')` in PT timezone, OR simply `WHERE date >= date('now')` (today) since the build's `date` field is stored as PT date.

**Checking actual data:** Build id=7 shows `"date": "2026-02-25"` and `"started_at": "2026-02-25T07:31:17.842336"` — the date field is the UTC date when the build starts. The morning briefing at 7 AM PT = 3 PM UTC same day. So on Feb 25 UTC: build ran at 07:31 UTC, briefing runs at 15:00 UTC — both on same UTC date. `WHERE date = date('now')` would correctly catch it.

**Recommended SQL:** `WHERE date >= date('now', '-1 day') ORDER BY id DESC LIMIT 1` — catches both same-day and prior-day builds safely.

---

## Code Examples

### Section 11 Prompt Text (for morning briefing)

```
## 11. YOLO Dev (Last Night's Build)
Query /workspace/yolo-dev/yolo.db using Python sqlite3:
```python
import sqlite3
conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT name, status, self_score, description FROM builds WHERE date >= date('now', '-1 day') AND status IN ('success','partial','failed') ORDER BY id DESC LIMIT 1"
).fetchone()
conn.close()
```
- If row found: Report "**{name}** — {status} | Score: {self_score}/5 | {description}"
- If no row: Report "No build ran last night."
```

### Weekly YOLO Digest Prompt Text (for weekly review)

```
## YOLO Dev Digest (This Week)
Query /workspace/yolo-dev/yolo.db using Python sqlite3:
```python
import sqlite3
conn = sqlite3.connect('/workspace/yolo-dev/yolo.db')
conn.row_factory = sqlite3.Row

# Total builds and status breakdown
summary = conn.execute(
    "SELECT COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success, SUM(CASE WHEN status='partial' THEN 1 ELSE 0 END) as partial, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed FROM builds WHERE date >= date('now', '-7 days') AND status IN ('success','partial','failed')"
).fetchone()

# Best build
best = conn.execute(
    "SELECT name, self_score, description, tech_stack FROM builds WHERE date >= date('now', '-7 days') AND self_score IS NOT NULL ORDER BY self_score DESC, id DESC LIMIT 1"
).fetchone()

# Tech stack distribution
stacks = conn.execute(
    "SELECT tech_stack, COUNT(*) as cnt FROM builds WHERE date >= date('now', '-7 days') GROUP BY tech_stack ORDER BY cnt DESC"
).fetchall()

conn.close()
```
Report: N builds this week (X success, Y partial, Z failed). Best build: **{name}** ({self_score}/5) — {description}. Stacks: {distribution}. Note any patterns (e.g., "3 consecutive Python builds").
If total = 0: "No YOLO builds this week."
```

### YOLO_BUILD.md Slack Notification (for DASH-04)

Add after Step 2 (status set to 'building'):
```
**Send build start notification:**
Use the Slack messaging tool to send to channel D0AARQR0Y4V:
"Starting YOLO build: {name}"
```

Add after Step 6 (final DB update):
```
**Send build completion notification:**
Use the Slack messaging tool to send to channel D0AARQR0Y4V:
"YOLO build complete: {name} -- {final_status}, score {score}/5"
```

### Cron Edit Commands

```bash
# Edit morning briefing (systemEvent kind)
openclaw cron edit 863587f3-bb4e-409b-aee2-11fe2373e6e0 --system-event "..."

# Edit weekly review (systemEvent kind)
openclaw cron edit 058f0007-935b-4399-aee1-28f6735f09ce --system-event "..."

# Test morning briefing immediately
openclaw cron run 863587f3-bb4e-409b-aee2-11fe2373e6e0

# Test weekly review immediately
openclaw cron run 058f0007-935b-4399-aae1-28f6735f09ce
```

---

## Key Facts Discovered (Live EC2 Inspection)

### Cron Job Inventory

| Job | ID | Session | Kind | Schedule |
|-----|-----|---------|------|----------|
| morning-briefing | `863587f3-bb4e-409b-aee2-11fe2373e6e0` | main | systemEvent | 0 7 * * * PT |
| weekly-review | `058f0007-935b-4399-aae1-28f6735f09ce` | main | systemEvent | 0 8 * * 0 PT |
| yolo-dev-overnight | `d498023d-7201-4f30-86c1-40250eea5f42` | isolated | agentTurn | 30 7 * * * UTC (= 11:30 PM PT) |

### Channel/DM IDs

| Target | ID |
|--------|-----|
| #popsclaw | `C0AD48J8CQY` |
| Andy's DM | `D0AARQR0Y4V` |

### Morning Briefing Delivery

- Morning briefing is `systemEvent` in main session. Bob's response auto-posts to #popsclaw — no explicit `sessions_send` needed (per the existing payload instruction: "Do NOT use sessions_send — your response will be delivered automatically").

### Weekly Review Delivery

- Weekly review explicitly instructs Bob: "Format as a structured weekly report. Send to D0AARQR0Y4V." This means Bob uses the Slack messaging tool explicitly to DM Andy.

### yolo.db Live Data

- 4 real builds: id 4 (Chronicle, 2026-02-24), id 5 (Pomodoro, 2026-02-25), id 6 (Habit Tracker, 2026-02-25), id 7 (Expense Tracker, 2026-02-25)
- `date` field = UTC calendar date of build start
- `status` values in use: 'success', 'partial', 'failed' (for completed builds)
- `tech_stack` = comma-separated string (e.g., "python", "html,css,javascript")
- `self_score` = integer 1-5

### Sandbox Bind Mounts (for DASH-04 isolated session question)

The isolated yolo cron has `"sessionTarget": "isolated"`. Isolated sessions go through Docker. The sandbox has yolo-dev bind: `/home/ubuntu/clawd/agents/main/yolo-dev:/workspace/yolo-dev:rw`. The Slack channel is configured at gateway level (`slack.botToken`, `slack.appToken`). OpenClaw tools (including Slack messaging) are proxied through the gateway even in isolated sessions — they are NOT host binaries. This means Slack messaging tool SHOULD be available in isolated sessions.

**Confidence: MEDIUM** — the architecture supports it (tool calls go through gateway), but no existing isolated cron currently sends Slack DMs to verify. Test required before committing to YOLO_BUILD.md approach.

---

## Recommended Implementation Plan

### Plan 41-01: Morning Briefing + Weekly Review (DASH-02, DASH-03)

1. Edit morning-briefing cron payload to append Section 11 YOLO dev status
2. Edit weekly-review cron payload to append YOLO digest section
3. Test both with `openclaw cron run` and verify output
4. No new cron jobs, no schema changes

**Risk:** LOW — pure prompt engineering on existing jobs.

### Plan 41-02: Slack DM Notifications (DASH-04)

1. Update YOLO_BUILD.md on EC2 to add Slack DM notification steps at build start and complete
2. Test by triggering yolo-dev-overnight cron manually with `openclaw cron run`
3. If Slack DM doesn't arrive (isolated session can't send), fall back to a post-build notification cron (fires after build window, reads last build from DB)
4. Validate both start and complete notifications in DM

**Risk:** MEDIUM on the isolated session Slack question — have a fallback ready.

---

## Open Questions

1. **Can isolated sessions send Slack DMs?**
   - What we know: Tool calls in isolated sessions go through the gateway; Slack is a gateway-level integration
   - What's unclear: Whether the gateway routes Slack tool calls for isolated sessions the same way as main session
   - Recommendation: Test with a throwaway isolated cron that sends a test DM before modifying YOLO_BUILD.md

2. **`--system-event` vs `--message` for cron edit?**
   - What we know: Morning briefing is `systemEvent` kind; `cron edit` has both `--message` and `--system-event` flags
   - What's unclear: Whether `--message` also updates `systemEvent` payloads or only `agentTurn`
   - Recommendation: Use `--system-event` flag for systemEvent jobs to be explicit; verify with `cron list --json` after edit

---

## Validation Architecture

nyquist_validation: false (per .planning/config.json). Skip this section.

---

## Sources

### Primary (HIGH confidence)
- Live EC2 inspection: `openclaw cron list --json` — all cron job IDs, session types, payload kinds, schedules
- Live EC2 inspection: `openclaw cron runs --id` — morning briefing and weekly review actual payload text
- Live EC2 inspection: yolo.db schema via `sqlite_master` query
- Live EC2 inspection: `openclaw.json` — sandbox binds, Slack config, channel IDs
- Live EC2 inspection: YOLO_BUILD.md — full protocol doc contents
- Live EC2 inspection: TOOLS.md, ANOMALY_ALERTS.md, MEETING_PREP.md — Slack DM patterns (D0AARQR0Y4V)

### Secondary (MEDIUM confidence)
- Inference: Isolated session can use gateway-proxied Slack tool — based on architecture (network=bridge, tool calls go through gateway), not direct test

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools confirmed live
- Architecture: HIGH — all cron structures confirmed from live JSON
- DASH-04 Slack in isolated: MEDIUM — architecture supports it but untested
- Pitfalls: HIGH — all derived from live data inspection

**Research date:** 2026-02-25
**Valid until:** 2026-03-26 (stable infrastructure)
