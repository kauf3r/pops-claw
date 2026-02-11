---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - "~/.openclaw/cron/jobs.json (on EC2)"
  - "~/.config/gogcli/config.json (on EC2)"
  - "~/.config/gogcli/keyring/ (on EC2)"
autonomous: false
user_setup:
  - service: google-oauth
    why: "Kaufman@AirSpaceIntegration.com OAuth authorization requires browser login"
    env_vars: []
    dashboard_config:
      - task: "Authorize AirSpace Google account in gog CLI (interactive browser flow)"
        location: "EC2 via SSH -- gog auth add with --manual flag"
must_haves:
  truths:
    - "gog gmail search --account=Kaufman@AirSpaceIntegration.com returns AirSpace emails"
    - "Morning briefing includes AirSpace email summary section"
    - "Dedicated AirSpace email monitor runs every 30 min during business hours and alerts on important emails"
  artifacts:
    - path: "~/.config/gogcli/keyring/token:pops-claw:Kaufman@AirSpaceIntegration.com"
      provides: "OAuth refresh token for AirSpace Gmail"
    - path: "~/.openclaw/cron/jobs.json"
      provides: "Updated morning briefing + new airspace-email-monitor cron job"
  key_links:
    - from: "airspace-email-monitor cron"
      to: "gog gmail search --account=Kaufman@AirSpaceIntegration.com"
      via: "cron payload message text"
      pattern: "--account=Kaufman@AirSpaceIntegration.com"
---

<objective>
Add Gmail monitoring for Kaufman@AirSpaceIntegration.com to Bob's daily workflow.

Purpose: Andy needs visibility into his AirSpace work email, especially incident ticket replies and important communications, surfaced proactively through Bob.
Output: OAuth-authorized second Google account + updated morning briefing + dedicated email monitor cron job.
</objective>

<execution_context>
@/Users/andykaufman/.claude/get-shit-done/workflows/execute-plan.md
@/Users/andykaufman/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
EC2 access: ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
GOG keyring password: export GOG_KEYRING_PASSWORD=$(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env | cut -d= -f2)

Current state:
- gog v0.9.0 at /usr/local/bin/gog on EC2
- One account authorized: theandykaufman@gmail.com (client: pops-claw)
- Config: ~/.config/gogcli/config.json has account_clients mapping
- Keyring: file-based at ~/.config/gogcli/keyring/
- OAuth client: ~/.config/gogcli/credentials-pops-claw.json (project: pops-claw)
- Client secret: ~/.config/gogcli/client_secret.json (project_id: pops-claw, type: installed)
- gog supports --account=EMAIL flag for multi-account queries
- gog auth add EMAIL --manual enables browserless OAuth (paste redirect URL)
- Morning briefing cron: isolated session, 7 AM PT, delivers to #popsclaw (C0AD48J8CQY)
- Meeting prep cron: every 15 min, checks calendar + email for upcoming meetings
- Cron runs embedded mode: use HOST paths (/home/ubuntu/...), not /workspace/

IMPORTANT Google Workspace consideration:
- The OAuth client (pops-claw, project_id: pops-claw) is an "installed app" type
- AirSpace Google Workspace may require the pops-claw project's client_id to be whitelisted
  in the AirSpace Google Admin console (Security > API Controls > App access control)
- If "This app isn't verified" screen appears during OAuth, user must click "Advanced" > "Go to pops-claw (unsafe)"
- If Workspace admin has blocked third-party apps, this will fail -- user needs admin access to whitelist
</context>

<tasks>

<task type="checkpoint:human-action" gate="blocking">
  <name>Task 1: Authorize Kaufman@AirSpaceIntegration.com in gog</name>
  <action>
The user must complete an interactive OAuth flow to authorize the AirSpace Google account.
This cannot be automated because it requires browser-based Google login + consent.

SSH into EC2 and run:
```bash
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
export GOG_KEYRING_PASSWORD=$(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env | cut -d= -f2)
gog auth add Kaufman@AirSpaceIntegration.com --manual --services=gmail,calendar --client=pops-claw
```

The `--manual` flag will print an OAuth URL. Open it in your browser, sign in as Kaufman@AirSpaceIntegration.com,
grant access, then paste the redirect URL back into the terminal.

If you see "This app isn't verified": Click Advanced > Go to pops-claw (unsafe).
If blocked by Workspace admin: You need to whitelist the pops-claw OAuth client ID
(724299093000-brur22l60a4bguvgina3khc9iouq091t.apps.googleusercontent.com) in
Google Admin > Security > API Controls > App access control.

After auth completes, verify it worked:
```bash
gog auth list
```
Should show TWO accounts: theandykaufman@gmail.com and Kaufman@AirSpaceIntegration.com.

Then test email access:
```bash
gog gmail search --account=Kaufman@AirSpaceIntegration.com "newer_than:1d" --max 3 --json
```
Should return recent AirSpace emails.
  </action>
  <verify>
`gog auth list` shows Kaufman@AirSpaceIntegration.com with gmail,calendar services.
`gog gmail search --account=Kaufman@AirSpaceIntegration.com "newer_than:1d" --max 3` returns results without errors.
  </verify>
  <done>Kaufman@AirSpaceIntegration.com OAuth token stored in gog keyring and email queries work.</done>
  <resume-signal>Type "authorized" when gog auth list shows the AirSpace account and email search works, or describe any issues.</resume-signal>
</task>

<task type="auto">
  <name>Task 2: Update morning briefing + add AirSpace email monitor cron</name>
  <files>~/.openclaw/cron/jobs.json (on EC2)</files>
  <action>
Two changes to cron jobs, both done by patching jobs.json on EC2:

**A. Update morning-briefing cron payload**

Find the morning-briefing job (id: 863587f3-bb4e-409b-aee2-11fe2373e6e0) in jobs.json.
In its payload.text and payload.message fields, ADD a new section between the existing
"## 2. Email (BR-03)" section and "## 3. Health (BR-04)" section:

```
## 2b. AirSpace Email (NEW)
Check Kaufman@AirSpaceIntegration.com for unread emails from the last 24 hours:
  gog gmail search --account=Kaufman@AirSpaceIntegration.com "is:unread newer_than:1d" --max 10 --json
Summarize important emails. Highlight with BOLD any:
- Incident ticket replies or updates (keywords: incident, ticket, P1, P2, outage, alert, escalation)
- Emails from leadership or management
- Action-required items (keywords: action required, please review, approval needed, urgent, ASAP)
- Calendar invites or meeting requests
Skip newsletters, automated notifications, and marketing. If no important emails, say "No important AirSpace emails."
Format as a separate section with header: **AirSpace Email (Kaufman@AirSpaceIntegration.com)**
```

**B. Add new airspace-email-monitor cron job**

Add a new job to the jobs array in jobs.json with this structure:
```json
{
  "id": "airspace-email-monitor",
  "agentId": "main",
  "name": "airspace-email-monitor",
  "description": "Monitor AirSpace Gmail for important emails every 30 min during business hours",
  "enabled": true,
  "createdAtMs": <current_epoch_ms>,
  "updatedAtMs": <current_epoch_ms>,
  "schedule": {
    "kind": "cron",
    "expr": "0,30 8-18 * * 1-5",
    "tz": "America/Los_Angeles"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "AirSpace Email Check -- scan Kaufman@AirSpaceIntegration.com for important new emails.\n\nRun: gog gmail search --account=Kaufman@AirSpaceIntegration.com \"is:unread newer_than:1h\" --max 20 --json\n\nClassify each unread email:\n- URGENT: incident tickets, P1/P2 alerts, outage notifications, escalations\n- ACTION: requires response or approval (keywords: action required, please review, approval needed)\n- FYI: informational but noteworthy (from leadership, meeting invites, project updates)\n- SKIP: newsletters, automated notifications, marketing, noreply senders\n\nIf ANY emails are classified URGENT or ACTION:\n- Send a Slack DM to Andy (channel: D0AARQR0Y4V) with subject, sender, and 1-line summary for each\n- Prefix URGENT emails with a red circle emoji, ACTION with orange diamond emoji\n- Include direct link format: https://mail.google.com/mail/u/?authuser=Kaufman@AirSpaceIntegration.com#inbox/THREAD_ID\n\nIf only FYI or SKIP emails, do NOT send a Slack message. Respond with a brief count only.\nIf no unread emails, respond: \"No new AirSpace emails.\"\n\nIMPORTANT: This runs in isolated session. Use Slack messaging tool to DM Andy directly.",
    "text": "AirSpace Email Check -- scan Kaufman@AirSpaceIntegration.com for important new emails.\n\nRun: gog gmail search --account=Kaufman@AirSpaceIntegration.com \"is:unread newer_than:1h\" --max 20 --json\n\nClassify each unread email:\n- URGENT: incident tickets, P1/P2 alerts, outage notifications, escalations\n- ACTION: requires response or approval (keywords: action required, please review, approval needed)\n- FYI: informational but noteworthy (from leadership, meeting invites, project updates)\n- SKIP: newsletters, automated notifications, marketing, noreply senders\n\nIf ANY emails are classified URGENT or ACTION:\n- Send a Slack DM to Andy (channel: D0AARQR0Y4V) with subject, sender, and 1-line summary for each\n- Prefix URGENT emails with a red circle emoji, ACTION with orange diamond emoji\n- Include direct link format: https://mail.google.com/mail/u/?authuser=Kaufman@AirSpaceIntegration.com#inbox/THREAD_ID\n\nIf only FYI or SKIP emails, do NOT send a Slack message. Respond with a brief count only.\nIf no unread emails, respond: \"No new AirSpace emails.\"\n\nIMPORTANT: This runs in isolated session. Use Slack messaging tool to DM Andy directly.",
    "model": "sonnet"
  },
  "delivery": {
    "mode": "silent"
  }
}
```

Key design decisions:
- Schedule: Every 30 min, Mon-Fri 8AM-6PM PT only (no weekend/night noise)
- delivery.mode: "silent" -- the agent itself decides whether to DM based on email importance
- The agent uses Slack DM (D0AARQR0Y4V) for urgent/action items, stays quiet otherwise
- Model: sonnet (good enough for email classification, cost-effective at 2x/hour)
- newer_than:1h window prevents re-alerting on already-seen emails
- Isolated session so it doesn't pollute main Bob session

After writing jobs.json, restart the gateway to pick up changes:
```bash
systemctl --user restart openclaw-gateway.service
```

Wait 5 seconds, then verify the gateway is healthy:
```bash
systemctl --user status openclaw-gateway.service
```

Then verify both jobs are registered:
```bash
/home/ubuntu/.npm-global/bin/openclaw cron list 2>&1 | grep -E "morning-briefing|airspace-email"
```
  </action>
  <verify>
1. `systemctl --user status openclaw-gateway.service` shows active (running)
2. `openclaw cron list` shows both morning-briefing and airspace-email-monitor jobs
3. Read back jobs.json and confirm:
   - morning-briefing payload contains "AirSpace Email" section with --account=Kaufman@AirSpaceIntegration.com
   - airspace-email-monitor job exists with correct schedule (0,30 8-18 * * 1-5) and tz (America/Los_Angeles)
  </verify>
  <done>
Morning briefing includes AirSpace email section. Dedicated email monitor runs every 30 min during business hours
and DMs Andy only when urgent/action-required emails arrive. Gateway restarted and healthy.
  </done>
</task>

<task type="checkpoint:human-verify" gate="soft">
  <name>Task 3: Verify AirSpace email monitoring works end-to-end</name>
  <what-built>
AirSpace Gmail monitoring with two integration points:
1. Morning briefing now includes AirSpace email summary section
2. New airspace-email-monitor cron runs every 30 min during business hours (Mon-Fri 8AM-6PM PT)
  </what-built>
  <how-to-verify>
**Quick test** (can do now):
1. SSH to EC2 and manually trigger the email monitor:
   ```bash
   ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
   /home/ubuntu/.npm-global/bin/openclaw cron run airspace-email-monitor --timeout 120000
   ```
2. Check the output -- it should query AirSpace Gmail and either:
   - DM you on Slack if urgent/action emails found, OR
   - Return a quiet "No new AirSpace emails" or email count

**Full test** (wait for next morning):
- Check tomorrow's 7 AM briefing in #popsclaw for the new "AirSpace Email" section

**Things to watch for:**
- OAuth token refresh working (gog handles this automatically)
- Email classification accuracy (urgent vs FYI vs skip)
- DM delivery for important emails
  </how-to-verify>
  <resume-signal>Type "verified" if the email monitor test ran successfully, or describe any issues.</resume-signal>
</task>

</tasks>

<verification>
- `gog auth list` on EC2 shows two accounts (theandykaufman@gmail.com + Kaufman@AirSpaceIntegration.com)
- `gog gmail search --account=Kaufman@AirSpaceIntegration.com "newer_than:1d" --max 3` returns results
- Morning briefing cron payload includes AirSpace email section
- airspace-email-monitor cron job registered with correct schedule
- Gateway service running after restart
</verification>

<success_criteria>
1. AirSpace Gmail OAuth authorized and email queries work
2. Morning briefing (7 AM daily) includes AirSpace email summary
3. Dedicated monitor (every 30 min M-F 8-6 PT) DMs Andy on urgent/action emails
4. No noise -- quiet when no important emails
</success_criteria>

<output>
After completion, update .planning/STATE.md with:
- New cron job: airspace-email-monitor (every 30 min M-F 8-6 PT, isolated, sonnet)
- Total cron jobs: 19
- New gog account: Kaufman@AirSpaceIntegration.com
- Morning briefing updated with AirSpace email section
</output>
