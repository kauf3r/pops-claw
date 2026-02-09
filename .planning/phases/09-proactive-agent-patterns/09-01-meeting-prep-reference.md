# Meeting Prep Scanner

This document is read by the meeting-prep-scan cron job (every 15 minutes).
Follow these instructions exactly when triggered.

## 1. Calendar Scan

Run the following command to find events starting in the next 15-45 minutes:

```
gog calendar events --from now --to "+45 minutes"
```

- If **NO events** are found in that window, respond with a single line: "No upcoming meetings." and **STOP**. Do not send any Slack message.
- If events are found, proceed to Section 2 for each event.

## 2. Context Assembly

For each event starting within 15-45 minutes, gather the following context:

### Event Details
- **Title:** full event title
- **Start time:** exact start time
- **End time:** exact end time
- **Location/Link:** meeting link (Zoom, Google Meet, etc.) or physical location

### Attendees
- List all attendees from the event invitation
- Note who organized the meeting

### Prior Interactions
- Search memory for previous interactions with key attendees
- Look for relevant context: past meeting notes, decisions, action items

### Related Emails
For each key attendee, check recent email context:
```
gog gmail search "from:{attendee_email} OR to:{attendee_email}" --max 3
```
Summarize any relevant recent threads (last 7 days).

### Agenda
- Check if the event description contains agenda items
- If no formal agenda, note the meeting topic from the title/description

## 3. Context-Aware Reminders

After processing imminent meetings, also scan for preparation needs:

```
gog calendar events --from "+1 hour" --to "+2 hours"
```

For events starting in 1-2 hours:
- Check if the event description mentions preparation tasks (e.g., "prepare slides", "review PR", "read document", "bring", "prepare", "review", "update")
- Flag any event where the description mentions action items the user should complete before the meeting
- These are "heads up" reminders, not full context assembly

## 4. Slack Delivery

Send assembled context to Andy's Slack DM (channel: D0AARQR0Y4V).

### Formatting Rules
- **Bold** the event title
- Include start time in 12-hour format with timezone (e.g., "2:30 PM PT")
- Use bullet points for context items
- Keep it concise: 3-5 bullet points per meeting
- Only send if there are actual meetings or actionable reminders
- For prep-needed events (1-2 hours out), prefix the message with "**Heads up:**"

### Example Output (to Slack DM)

**Weekly Team Sync** - 2:30 PM PT
- Attendees: Alice, Bob, Charlie
- Last week Alice mentioned shipping the auth refactor by Friday
- Recent email thread about API rate limits from Charlie (Feb 7)
- Agenda: Sprint review, blockers, next week planning

**Heads up:** Product Review at 4:00 PM PT
- Description mentions "review Q1 metrics doc" -- make sure you have it ready

## Important Notes

- This runs in **embedded mode** (cron-triggered). Use HOST paths only.
- Calendar: `gog calendar events` (available on host PATH)
- Gmail: `gog gmail search` (available on host PATH)
- Memory: Use built-in memory search tool
- Slack: Use built-in Slack messaging tool
- Do NOT use /workspace/ paths. All file references must be absolute host paths starting with /home/ubuntu/.
- If calendar or Gmail commands fail, note the error in your response but do not retry or error out.
