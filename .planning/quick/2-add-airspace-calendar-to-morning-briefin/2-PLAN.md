---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - ~/.openclaw/cron/jobs.json (on EC2)
  - ~/clawd/agents/main/MEETING_PREP.md (on EC2)
autonomous: true
must_haves:
  truths:
    - "Morning briefing includes AirSpace calendar events alongside personal calendar"
    - "Meeting prep scanner checks AirSpace calendar for upcoming meetings"
    - "Evening recap includes AirSpace calendar in tomorrow preview"
  artifacts:
    - path: "~/.openclaw/cron/jobs.json"
      provides: "Updated morning-briefing and evening-recap payloads with AirSpace calendar"
    - path: "~/clawd/agents/main/MEETING_PREP.md"
      provides: "Updated meeting prep instructions scanning both calendars"
  key_links:
    - from: "morning-briefing cron payload"
      to: "gog calendar events --account=Kaufman@AirSpaceIntegration.com"
      via: "Section 1b in briefing prompt"
    - from: "MEETING_PREP.md Section 1"
      to: "gog calendar events --account=Kaufman@AirSpaceIntegration.com"
      via: "Second calendar scan command"
---

<objective>
Add AirSpace calendar (Kaufman@AirSpaceIntegration.com) to morning briefing, meeting prep scanner, and evening recap.

Purpose: Andy needs work calendar events surfaced alongside personal calendar for complete daily awareness.
Output: Updated cron payloads + MEETING_PREP.md on EC2.
</objective>

<execution_context>
@/Users/andykaufman/.claude/get-shit-done/workflows/execute-plan.md
@/Users/andykaufman/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
All work is on EC2 (100.72.143.9) via SSH.
SSH: ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
OAuth for Kaufman@AirSpaceIntegration.com is already authorized with calendar scope.
gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --today --max=30 WORKS.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update morning briefing and evening recap cron payloads</name>
  <files>~/.openclaw/cron/jobs.json (on EC2)</files>
  <action>
SSH into EC2. Read current jobs.json. Update THREE cron job payloads:

**1. morning-briefing (id: 863587f3-bb4e-409b-aee2-11fe2373e6e0)**

In both `payload.text` and `payload.message`, add a new section after "## 1. Calendar (BR-02)":

```
## 1b. AirSpace Calendar (Kaufman@AirSpaceIntegration.com)
Run: gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --today --max=30
Format: all-day events grouped first, then timed events in chronological order, times in PT.
Add brief prep notes for meetings (attendees, topic from title).
If no events, say "No AirSpace calendar events today."
Format as a separate section with header: **AirSpace Calendar (Kaufman@AirSpaceIntegration.com)**
```

**2. evening-recap (id: 1914a2ba-5d4d-49c4-a884-a7e7b7aee17b)**

In `payload.text`, update the "## Tomorrow Preview" section to also run:
```
Also run: gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --date=tomorrow --max=20
List AirSpace events separately under "**AirSpace Calendar**" header. Merge with personal calendar events into one chronological timeline, labeling AirSpace events with [ASI] prefix.
```

**3. weekly-review (id: 058f0007-935b-4399-aae1-28f6735f09ce)**

In `payload.text`, update the "## Upcoming Week" section to also run:
```
Also run: gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --days=7 --max=50
Merge AirSpace events into the weekly overview, labeling with [ASI] prefix. Flag scheduling conflicts between personal and work calendars.
```

Use `python3 -c "import json; ..."` to safely read, modify, and write jobs.json (avoids heredoc/quoting issues over SSH). Write a Python script to /tmp/ on EC2, then execute it.

After writing jobs.json, restart the gateway service:
  systemctl --user restart openclaw-gateway.service

Wait 5 seconds, then verify service is running:
  systemctl --user status openclaw-gateway.service
  </action>
  <verify>
1. SSH in and read jobs.json, confirm morning-briefing payload contains "AirSpace Calendar" section with gog calendar events --account=Kaufman@AirSpaceIntegration.com
2. Confirm evening-recap payload mentions AirSpace calendar for tomorrow preview
3. Confirm weekly-review payload mentions AirSpace calendar for upcoming week
4. systemctl --user status openclaw-gateway.service shows active (running)
  </verify>
  <done>
Morning briefing, evening recap, and weekly review cron payloads all include AirSpace calendar queries. Gateway service restarted and running.
  </done>
</task>

<task type="auto">
  <name>Task 2: Update MEETING_PREP.md to scan AirSpace calendar</name>
  <files>~/clawd/agents/main/MEETING_PREP.md (on EC2)</files>
  <action>
SSH into EC2. Update /home/ubuntu/clawd/agents/main/MEETING_PREP.md:

**Section 1 (Calendar Scan):** Add a SECOND calendar scan command after the existing one:

```
Also run for AirSpace calendar:
gog calendar events --account=Kaufman@AirSpaceIntegration.com --from now --to "+45 minutes"
```

Update the logic: "If NO events are found in that window FROM EITHER CALENDAR..." (both must be empty to stop).

**Section 2 (Context Assembly):** Add note that AirSpace meetings may have different attendee patterns. For AirSpace meetings, also note:
- Label the meeting as [ASI] in the Slack message
- Check AirSpace email for related threads: `gog gmail search --account=Kaufman@AirSpaceIntegration.com "from:{attendee} OR to:{attendee}" --max 3`

**Section 3 (Context-Aware Reminders):** Add the same second scan:
```
Also run: gog calendar events --account=Kaufman@AirSpaceIntegration.com --from "+1 hour" --to "+2 hours"
```

Use a Python script written to /tmp/ on EC2 to safely read, modify, and write the file (avoid heredoc issues over SSH). The script should read the current content, make targeted insertions, and write back.
  </action>
  <verify>
1. SSH in and read MEETING_PREP.md, confirm it contains "Kaufman@AirSpaceIntegration.com" in sections 1, 2, and 3
2. Confirm the "no events" stop condition requires BOTH calendars to be empty
3. Confirm AirSpace email search is referenced for AirSpace meeting attendees
  </verify>
  <done>
MEETING_PREP.md scans both personal and AirSpace calendars for upcoming meetings. AirSpace meetings labeled [ASI] in Slack delivery.
  </done>
</task>

</tasks>

<verification>
1. Read jobs.json on EC2 -- morning-briefing, evening-recap, and weekly-review all reference AirSpace calendar
2. Read MEETING_PREP.md on EC2 -- references AirSpace calendar in scan, context assembly, and reminders
3. Gateway service is running after restart
4. Quick smoke test: `ssh ... 'gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --today --max=5'` returns results (confirms OAuth still works post-restart)
</verification>

<success_criteria>
- Morning briefing will include AirSpace calendar events as section 1b starting next run
- Meeting prep scanner will detect AirSpace meetings within 15-45 minutes
- Evening recap will include AirSpace calendar in tomorrow preview
- Weekly review will include AirSpace calendar in upcoming week overview
- Gateway service healthy after changes
</success_criteria>

<output>
After completion, create `.planning/quick/2-add-airspace-calendar-to-morning-briefin/2-SUMMARY.md`
</output>
