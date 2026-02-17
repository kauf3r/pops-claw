# Phase 22: Domain Warmup & Production Hardening - Research

**Researched:** 2026-02-17
**Domain:** Email domain reputation (SPF/DKIM/DMARC verification), send quota monitoring with alerts, catch-up cron for webhook downtime, bounce/complaint rate monitoring via SQLite
**Confidence:** HIGH

## Summary

This phase hardens the existing Resend email integration from Phases 19-21. No new email capabilities are added. Four workstreams: (1) WARMUP.md checklist for Bob to verify SPF/DKIM pass, confirm inbox placement, and escalate DMARC from p=none to p=quarantine after 2 clean weeks; (2) quota monitoring with threshold alerts at 80/day and 95/day (hard-block) plus monthly tracking at 2700/3000; (3) a catch-up cron polling `GET /emails/receiving` every 30 minutes to recover missed webhook deliveries; and (4) bounce/complaint rate monitoring via SQL queries on email.db with threshold alerts.

All four workstreams follow established project patterns: reference doc (like STUCK_DETECTION.md, PIPELINE_REPORT.md), cron job (like airspace-email-monitor), SQL queries on existing DB (like stuck-check queries on content.db), and JSON config tracking (like daily_send_count in email-config.json). No new external services, no new databases, no new skills.

**Primary recommendation:** Single plan with 4 tasks: (1) WARMUP.md reference doc, (2) quota monitoring additions to SKILL.md + email-config.json, (3) catch-up cron job, (4) email health monitoring additions to ops reporting. All work is on EC2 via SSH, modifying existing files.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Warmup Strategy
- No formal warmup schedule -- volume is 5-10 emails/day to 1-2 known recipients on Resend shared IPs
- WARMUP.md reference doc in Bob's workspace: checklist to verify SPF/DKIM pass, confirm Gmail inbox placement, escalate DMARC to p=quarantine after 2 clean weeks
- Not a cron -- a one-time checklist Bob works through manually

#### Quota & Alerting
- Daily send quota tracking already exists in email-config.json (daily_send_count)
- Add threshold alert at 80/day (warning) and hard-block at 95/day (safety margin below 100 free tier limit)
- Add monthly_send_count to email-config.json, alert at 2700/month (90% of 3000)
- Alert channel: #popsclaw (same as all Bob alerts)
- When limit hit: Bob refuses to send, logs refusal, notifies Andy -- no silent failures

#### Catch-up Cron
- Poll Resend Received Emails API every 30 minutes (isolated session, sonnet, 120s timeout)
- Dedup: query email.db for existing resend_email_id, skip already-processed
- Lookback window: 2 hours (covers brief outages; Svix retries cover up to 27.5hr)
- Silent when healthy -- only notify if catch-up actually recovers missed emails

#### Monitoring Scope
- Bounce/complaint rates via SQL queries on email.db (same pattern as stuck-detection)
- Weekly section in ops reporting: bounce rate, complaint rate, total sent week/month, delivery success %
- Threshold alerts: bounce >2% or complaint >0.08% -> immediate #popsclaw alert
- No dashboard -- SQLite queries + cron alerts sufficient at this volume

### Claude's Discretion
- Exact SQL queries for rate calculations
- Whether to add email health to existing PIPELINE_REPORT.md or create separate EMAIL_HEALTH.md
- Catch-up cron session naming and timeout tuning
- WARMUP.md checklist ordering and wording

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| Resend Received Emails API | v1 (`GET /emails/receiving`) | Poll for missed inbound emails (catch-up cron) | Already used in Phase 20-21. Cursor-based pagination, returns metadata per email |
| Resend API Rate Limit Headers | v1 | `x-resend-daily-quota` + `x-resend-monthly-quota` response headers | Free tier quota tracking built into every API response |
| SQLite (`email.db`) | 3.x (bind-mounted) | Bounce/complaint rate queries, dedup for catch-up cron | Already deployed in Phase 21. All email conversations recorded here |
| `email-config.json` | n/a | Quota counters (`daily_send_count`, `monthly_send_count`) | Already tracks daily count (Phase 19). Adding monthly counter |
| SKILL.md (resend-email) | 13 sections | Quota enforcement logic additions | Existing skill -- just adding threshold checks to Section 7 and Section 9 |

### Supporting

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| `curl` (in sandbox) | built-in | Poll Resend API for catch-up cron, verify SPF/DKIM | Every catch-up cron run |
| `sqlite3` (in sandbox) | bind-mounted | Rate calculation queries, dedup checks | Catch-up cron dedup + weekly health report |
| `dig` (on EC2 host) | built-in | DNS record verification (SPF, DKIM, DMARC) | One-time warmup checklist |
| Reference doc pattern | n/a | WARMUP.md + EMAIL_HEALTH.md workspace documents | Bob reads for instructions, same as STUCK_DETECTION.md |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Polling `GET /emails/receiving` | Resend webhook retry (Svix) as sole mechanism | Svix retries up to ~34 hours with exponential backoff, but if endpoint is down for extended maintenance, emails are lost. Catch-up cron is belt-and-suspenders |
| JSON config for monthly counter | SQLite table for quota tracking | Overkill -- email-config.json already tracks daily count. Monthly is one more field |
| Separate quota-check cron | Inline checks in SKILL.md before every send | Inline is simpler -- Bob already reads email-config.json before sending. No separate cron needed for quota |
| Resend Metrics dashboard page | SQL queries on email.db | Dashboard requires browser access. SQL queries run in cron, produce actionable alerts. At 5-10 emails/day, SQL is sufficient |

**Installation:** No new packages. All components exist:
1. `GET /emails/receiving` API -- already authorized with `full_access` key
2. email.db -- already deployed and bind-mounted (Phase 21)
3. email-config.json -- already deployed (Phase 19)
4. resend-email SKILL.md -- already has 13 sections
5. Cron infrastructure -- already running 19+ cron jobs

## Architecture Patterns

### Workstream Overview

```
WARMUP.md (one-time checklist)
  |-- Bob verifies SPF/DKIM pass via dig + Gmail "Show original"
  |-- Bob confirms inbox placement (not spam folder)
  |-- After 2 clean weeks: Andy manually escalates DMARC p=none -> p=quarantine

Quota Monitoring (inline in SKILL.md)
  |-- Before every send: read email-config.json
  |-- Check daily_send_count vs thresholds (80 warn, 95 block)
  |-- Check monthly_send_count vs threshold (2700 warn/block)
  |-- After every send: increment counters, write config back
  |-- Optional: parse x-resend-daily-quota / x-resend-monthly-quota headers

Catch-up Cron (every 30 min)
  |-- GET /emails/receiving?limit=100
  |-- For each email: check email.db for existing resend_email_id
  |-- If not found: process as new inbound (same as webhook pipeline)
  |-- If found: skip (already processed)
  |-- Only notify if recovery happened

Email Health Monitoring (weekly ops cron)
  |-- SQL: bounce rate = bounced / total_outbound
  |-- SQL: complaint rate = complained / total_outbound
  |-- SQL: delivery success = delivered / total_outbound
  |-- SQL: sent this week, sent this month
  |-- Threshold alerts: bounce >2% or complaint >0.08%
```

### Pattern 1: Catch-up Cron -- Polling Received Emails API

**What:** Periodically poll Resend's list endpoint to find emails that may have been missed by webhooks.
**When to use:** Every 30 minutes via cron.
**Source:** [Resend List Received Emails](https://resend.com/docs/api-reference/emails/list-received-emails) (Context7 verified)

```bash
# Fetch recent received emails from Resend API
RECEIVED=$(curl -s -X GET 'https://api.resend.com/emails/receiving?limit=100' \
  -H "Authorization: Bearer $RESEND_API_KEY")

# Parse and check each against email.db
python3 << 'PYEOF'
import json, subprocess, sys

received = json.loads('''RECEIVED_DATA''')
emails = received.get('data', [])
recovered = 0

for email in emails:
    email_id = email['id']
    created_at = email['created_at']

    # Check if already processed
    result = subprocess.run(
        ['sqlite3', '/workspace/email.db',
         f"SELECT COUNT(*) FROM email_conversations WHERE resend_email_id='{email_id}';"],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip())

    if count == 0:
        # Not in DB -- this is a missed email, process it
        # (Bob would then run the full inbound processing pipeline from Section 8)
        print(f'RECOVERED: {email["from"]} -- {email["subject"]} ({email_id})')
        recovered += 1
    # else: already processed, skip silently

if recovered > 0:
    print(f'\nTotal recovered: {recovered} missed email(s)')
else:
    print('All clear -- no missed emails')
PYEOF
```

**API Response Format:**
```json
{
  "object": "list",
  "has_more": true,
  "data": [
    {
      "id": "a39999a6-88e3-48b1-888b-beaabcde1b33",
      "to": ["bob@mail.andykaufman.net"],
      "from": "sender@example.com",
      "created_at": "2026-02-17T14:37:40.951732+00",
      "subject": "Hello World",
      "message_id": "<111-222-333@email.provider.example.com>",
      "attachments": []
    }
  ]
}
```

**Key API details:**
- Endpoint: `GET /emails/receiving`
- Pagination: `limit` (default 20, max 100), `after` (cursor ID), `before` (cursor ID)
- No date filter parameter -- must filter by `created_at` client-side
- Returns newest-first by default
- `has_more: true` indicates more pages available
- Each item has `id` (Resend UUID, same as `resend_email_id` in DB) for dedup

**Lookback window implementation:** Since the API has no date filter, Bob fetches up to 100 recent emails and filters client-side by `created_at` within the last 2 hours. At 5-10 emails/day volume, 100 is more than sufficient for any 2-hour window.

### Pattern 2: Quota Threshold Enforcement

**What:** Add monthly counter and threshold checks to the existing quota tracking in SKILL.md.
**When to use:** Before every outbound email send.

```python
import json
from datetime import datetime

with open('/workspace/email-config.json') as f:
    config = json.load(f)

today = datetime.utcnow().strftime('%Y-%m-%d')
this_month = datetime.utcnow().strftime('%Y-%m')

# Reset daily counter if new day
if config.get('daily_send_date') != today:
    config['daily_send_count'] = 0
    config['daily_send_date'] = today
    config['alert_count_today'] = 0

# Reset monthly counter if new month
if config.get('monthly_send_month') != this_month:
    config['monthly_send_count'] = 0
    config['monthly_send_month'] = this_month

daily = config.get('daily_send_count', 0)
monthly = config.get('monthly_send_count', 0)

# Threshold checks
if daily >= 95:
    print(f'HARD BLOCK: {daily}/100 daily emails sent. Refusing to send.')
    print('Safety margin: 5 remaining for critical alerts only.')
    # Notify Andy in #popsclaw
elif daily >= 80:
    print(f'WARNING: {daily}/100 daily emails sent. Approaching daily limit.')
    # Continue sending but warn in #popsclaw

if monthly >= 2700:
    print(f'MONTHLY WARNING: {monthly}/3000 monthly emails sent.')
    # Notify Andy in #popsclaw

# After successful send:
config['daily_send_count'] = daily + 1
config['monthly_send_count'] = monthly + 1
with open('/workspace/email-config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

**Updated email-config.json structure:**
```json
{
  "recipients": [
    {"email": "theandykaufman@gmail.com", "name": "Andy"}
  ],
  "daily_send_count": 3,
  "daily_send_date": "2026-02-17",
  "alert_count_today": 0,
  "monthly_send_count": 45,
  "monthly_send_month": "2026-02",
  "sender_allowlist": [
    "theandykaufman@gmail.com",
    "kaufman@airspaceintegration.com"
  ]
}
```

### Pattern 3: Resend API Quota Response Headers

**What:** Parse quota remaining from API response headers on every send.
**When to use:** After every `POST /emails` call (optional validation of local counters).
**Source:** [Resend Usage Limits](https://resend.com/docs/api-reference/rate-limit) (Context7 verified)

```bash
# Send email and capture response headers
RESPONSE=$(curl -s -D - -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }')

# Headers returned (free tier):
# x-resend-daily-quota: 97    (remaining daily)
# x-resend-monthly-quota: 2955  (remaining monthly)
```

**Key details:**
- `x-resend-daily-quota`: remaining daily sending quota (free tier only)
- `x-resend-monthly-quota`: remaining monthly sending quota
- Both sent and received emails count toward quotas
- Exceeding quota returns HTTP 429 with `daily_quota_exceeded` or `monthly_quota_exceeded`
- Rate limit: 2 requests/second (HTTP 429 `rate_limit_exceeded`)

**Recommendation:** Use local counters in email-config.json as primary tracking (works offline, no API call needed for check). Optionally validate against API headers when they're available in the response -- but don't add a separate "check quota" API call.

### Pattern 4: Bounce/Complaint Rate SQL Queries

**What:** Calculate email health metrics from email_conversations table.
**When to use:** Weekly ops report + threshold-based alerting.

```sql
-- Bounce rate (last 7 days)
SELECT
    ROUND(
        CAST(SUM(CASE WHEN delivery_status = 'bounced' THEN 1 ELSE 0 END) AS REAL) /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS bounce_rate_pct,
    SUM(CASE WHEN delivery_status = 'bounced' THEN 1 ELSE 0 END) AS bounced,
    COUNT(*) AS total_outbound
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days');

-- Complaint rate (last 7 days)
SELECT
    ROUND(
        CAST(SUM(CASE WHEN delivery_status = 'complained' THEN 1 ELSE 0 END) AS REAL) /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS complaint_rate_pct,
    SUM(CASE WHEN delivery_status = 'complained' THEN 1 ELSE 0 END) AS complained,
    COUNT(*) AS total_outbound
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days');

-- Delivery success rate (last 7 days)
SELECT
    ROUND(
        CAST(SUM(CASE WHEN delivery_status = 'delivered' THEN 1 ELSE 0 END) AS REAL) /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS delivery_rate_pct,
    SUM(CASE WHEN delivery_status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
    SUM(CASE WHEN delivery_status = 'bounced' THEN 1 ELSE 0 END) AS bounced,
    SUM(CASE WHEN delivery_status = 'complained' THEN 1 ELSE 0 END) AS complained,
    SUM(CASE WHEN delivery_status = 'delayed' THEN 1 ELSE 0 END) AS delayed,
    SUM(CASE WHEN delivery_status = 'unknown' THEN 1 ELSE 0 END) AS unknown,
    COUNT(*) AS total
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days');

-- Volume stats
SELECT
    COUNT(*) FILTER (WHERE created_at >= datetime('now', '-7 days')) AS sent_this_week,
    COUNT(*) FILTER (WHERE created_at >= datetime('now', '-30 days')) AS sent_this_month,
    COUNT(*) AS sent_all_time
FROM email_conversations
WHERE direction = 'outbound';
```

**Note:** SQLite does not support `FILTER (WHERE ...)` syntax. Use `CASE WHEN` equivalent:

```sql
-- Volume stats (SQLite-compatible)
SELECT
    SUM(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 ELSE 0 END) AS sent_this_week,
    SUM(CASE WHEN created_at >= datetime('now', '-30 days') THEN 1 ELSE 0 END) AS sent_this_month,
    COUNT(*) AS sent_all_time
FROM email_conversations
WHERE direction = 'outbound';
```

### Pattern 5: WARMUP.md Checklist Structure

**What:** One-time reference doc for Bob to verify email authentication and inbox placement.
**When to use:** Bob works through it once; Andy reviews results.
**Pattern:** Same as STUCK_DETECTION.md / PIPELINE_REPORT.md -- reference doc with instructions + commands.

```markdown
# Email Domain Warmup Checklist

## Status: [PENDING / IN PROGRESS / COMPLETE]

## Step 1: Verify DNS Authentication
Run these commands and confirm all PASS:

### SPF Check
dig TXT send.mail.andykaufman.net
# Expected: "v=spf1 include:amazonses.com ~all"

### DKIM Check
dig CNAME [hash1]._domainkey.mail.andykaufman.net
dig CNAME [hash2]._domainkey.mail.andykaufman.net
dig CNAME [hash3]._domainkey.mail.andykaufman.net
# All should resolve to *.dkim.amazonses.com

### DMARC Check
dig TXT _dmarc.mail.andykaufman.net
# Expected: "v=DMARC1; p=none;"

## Step 2: Verify Email Authentication Headers
Send a test email to theandykaufman@gmail.com. In Gmail, "Show original" and verify:
- SPF: PASS
- DKIM: PASS
- DMARC: PASS (or no record -- p=none is expected initially)

## Step 3: Confirm Inbox Placement
- [ ] Test email arrived in inbox (NOT spam folder)
- [ ] Subject, From name ("Bob"), and From address (bob@mail.andykaufman.net) display correctly
- [ ] HTML formatting renders properly in Gmail web and mobile

## Step 4: Monitor for 2 Weeks
- [ ] All outbound emails deliver to inbox (spot-check daily via Andy)
- [ ] No bounce notifications received
- [ ] No complaint notifications received
- [ ] Resend dashboard shows healthy sending metrics

## Step 5: Escalate DMARC (After 2 Clean Weeks)
When Andy confirms Steps 1-4 are clean for 2 weeks:
1. Update DNS record: _dmarc.mail.andykaufman.net
2. Change from: v=DMARC1; p=none;
3. Change to: v=DMARC1; p=quarantine; pct=100;
4. Monitor for 1 more week to confirm no legitimate emails affected

NOTE: DMARC escalation is MANUAL -- Andy updates DNS when ready.
```

### Pattern 6: Catch-up Cron Job Configuration

**What:** Isolated cron job polling Resend for missed inbound emails.
**When to use:** Every 30 minutes, 24/7.
**Pattern:** Same as airspace-email-monitor (isolated, sonnet, silent when healthy).

```json
{
  "id": "email-catchup",
  "agentId": "main",
  "name": "email-catchup",
  "description": "Poll Resend for missed inbound emails (webhook downtime fallback)",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "15,45 * * * *",
    "tz": "America/Los_Angeles"
  },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Email catch-up check: poll Resend Received Emails API for missed inbound emails.\n\n1. Fetch recent emails: curl -s -X GET 'https://api.resend.com/emails/receiving?limit=100' -H \"Authorization: Bearer $RESEND_API_KEY\"\n2. For each email in the response, check email.db: SELECT COUNT(*) FROM email_conversations WHERE resend_email_id='EMAIL_ID';\n3. If count=0 AND created_at is within last 2 hours: this email was missed by webhooks. Process it using Section 8 (Inbound Email Processing) of the resend-email skill.\n4. If ALL emails already exist in DB: no action needed. Respond briefly: 'Catch-up check: all clear.'\n5. If any emails were recovered: notify Andy in #popsclaw with count and sender/subject summary.\n\nIMPORTANT: Only process emails with created_at within the last 2 hours. Older emails were either already processed or intentionally skipped.",
    "model": "sonnet"
  },
  "delivery": {
    "mode": "silent"
  }
}
```

**Schedule choice:** `15,45 * * * *` (offset from :00 and :30 to avoid collision with existing cron jobs that run on the hour and half-hour). Runs 24/7 because email can arrive anytime. Every 30 minutes is sufficient -- Svix retries webhooks over 34 hours, so a 30-minute poll gap is well within the safety window.

**Timeout:** 120s (120000ms). Sufficient for: 1 API call (~500ms) + up to 100 dedup checks (~2s total) + processing any recovered emails (~30s each if any).

### Anti-Patterns to Avoid

- **Building a dedicated quota-tracking database:** Overkill for 5-10 emails/day. email-config.json counters are sufficient.
- **Creating a separate quota-check cron:** Quota checks are inline -- Bob checks before every send. No separate cron needed.
- **Fetching ALL received emails in catch-up cron:** Only look back 2 hours (client-side filter on `created_at`). Don't process the entire email history every 30 minutes.
- **Using `has_more` pagination in catch-up cron:** At 5-10 emails/day, 100 per page covers weeks of email. Pagination is unnecessary but code should handle `has_more: true` gracefully (log a warning, don't infinitely paginate).
- **Sending warmup emails to strangers or test services:** This is 5-10 emails/day to known recipients on shared IPs. No artificial warmup needed -- just verify authentication and monitor naturally.
- **Separate EMAIL_HEALTH.md cron:** Adding email health to existing ops reporting (PIPELINE_REPORT.md or stuck-check) avoids yet another cron job.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Quota tracking | Custom SQLite quota table | JSON counters in email-config.json + Resend response headers | 2 counter fields are simpler than a table. Resend headers provide server-side validation |
| DNS verification | Custom DNS query tool | `dig` CLI on EC2 host | Standard tool, one-time use, no dependencies |
| Email authentication check | Parse raw email headers manually | Gmail "Show original" (human verification) | One-time check, not automatable. Andy eyeballs SPF/DKIM/DMARC pass |
| Catch-up dedup | Custom dedup data structure | SQL query on existing email_conversations.resend_email_id | Table already has the column and an index (`idx_conversations_resend_id`) |
| Rate calculations | Custom metrics pipeline | Simple SQL COUNT + CASE on email_conversations | 5 rows of SQL produce all needed metrics at this volume |

**Key insight:** Every piece of this phase is achievable with existing infrastructure: JSON config files, SQLite queries, cron jobs, and reference docs. Zero new tools, zero new databases, zero new external services.

## Common Pitfalls

### Pitfall 1: Resend List API Has No Date Filter

**What goes wrong:** Developer assumes `GET /emails/receiving` accepts a `since` or `created_after` query parameter. It does not. The only parameters are `limit`, `after` (cursor), and `before` (cursor).
**Why it happens:** Many APIs have date range filters. Resend's list endpoints use cursor-based pagination only.
**How to avoid:** Fetch with `limit=100` and filter `created_at` client-side in Python. At 5-10 emails/day, 100 results covers ~2 weeks. Parse `created_at` timestamps and compare against `datetime.utcnow() - timedelta(hours=2)` for the 2-hour lookback window.
**Warning signs:** Catch-up cron processes ancient emails. Or, developer adds invalid query params that are silently ignored.
**Confidence:** HIGH (Context7 verified -- only `limit`, `after`, `before` parameters documented)

### Pitfall 2: Monthly Counter Never Resets

**What goes wrong:** `monthly_send_count` reaches 2700 and blocks all sending. But it never resets because no reset logic exists.
**Why it happens:** The daily counter resets when `daily_send_date` changes. Monthly needs similar reset when month changes.
**How to avoid:** Add `monthly_send_month` field (e.g., "2026-02"). Before every send, check if current month matches. If not, reset `monthly_send_count` to 0 and update `monthly_send_month`. This mirrors the existing `daily_send_date` reset pattern.
**Warning signs:** Bob refuses to send at the start of a new month, citing quota limit.
**Confidence:** HIGH (logic gap in current implementation -- must add month-boundary reset)

### Pitfall 3: Catch-up Cron Creates Duplicate Processing

**What goes wrong:** An email arrives via webhook AND is picked up by the catch-up cron, resulting in duplicate Slack notifications.
**Why it happens:** Race condition -- webhook processes the email and inserts into DB, but catch-up cron started its API fetch before the DB insert completed.
**How to avoid:** The dedup query (`SELECT COUNT(*) FROM email_conversations WHERE resend_email_id=?`) runs immediately before processing. Even if the API fetch happened before the webhook insert, the dedup check will see the record by the time it runs. SQLite writes are atomic. The 30-minute poll interval means the window for race conditions is effectively zero.
**Warning signs:** Same email appears twice in #popsclaw. Check email.db for duplicate `resend_email_id` entries.
**Confidence:** HIGH (dedup pattern is robust at this volume/frequency)

### Pitfall 4: Bounce/Complaint Rates Misleading at Low Volume

**What goes wrong:** 1 bounce out of 10 emails shows 10% bounce rate, triggering panic. But 1/10 is statistically meaningless.
**Why it happens:** Rate calculations at very low volume produce extreme percentages from single events.
**How to avoid:** Add minimum volume thresholds to alerts:
- Bounce alert: only fire if `total_outbound >= 10 AND bounce_rate > 2%`
- Complaint alert: only fire if `total_outbound >= 20 AND complaint_rate > 0.08%`
- Below minimum volume: report absolute numbers instead of percentages ("1 bounce this week" not "10% bounce rate")
**Warning signs:** Alert fatigue from percentage-based alerts on tiny sample sizes.
**Confidence:** HIGH (standard practice for email metrics -- Resend's own threshold is 4% bounce with sufficient volume)

### Pitfall 5: DMARC Escalation Breaks Delivery

**What goes wrong:** DMARC is changed from p=none to p=quarantine, but some legitimate mechanism (forwarding, mailing list) causes DKIM/SPF misalignment. Emails go to spam.
**Why it happens:** DMARC quarantine tells receiving servers to treat authentication failures as suspicious. If DKIM alignment is imperfect (e.g., intermediate server modifies headers), quarantine catches it.
**How to avoid:** This is mitigated by the 2-week monitoring period before escalation. However:
- Before escalation, confirm ALL test emails show SPF PASS + DKIM PASS in Gmail "Show original"
- Start with `pct=100` (not partial -- volume is too low for percentage-based rollout to be meaningful)
- After escalation, immediately send a test email and verify inbox placement
- Keep monitoring for 1 week after change
**Warning signs:** Emails start arriving in spam folder after DMARC change.
**Confidence:** HIGH (well-documented DMARC escalation risk)

### Pitfall 6: Catch-up Cron Hits Rate Limit

**What goes wrong:** Catch-up cron processes 10+ missed emails at once, each triggering a `GET /emails/receiving/{id}` API call for full headers, exceeding Resend's 2 req/s rate limit.
**Why it happens:** If webhook was down for 2 hours and 10+ emails arrived, catch-up cron tries to process all at once.
**How to avoid:** Add a 1-second delay between processing recovered emails. At 5-10 emails/day, even a 2-hour outage produces at most 1-2 missed emails. But the delay is cheap insurance. The 120s cron timeout is ample for sequential processing with delays.
**Warning signs:** HTTP 429 errors from Resend API during catch-up processing.
**Confidence:** MEDIUM (unlikely at current volume, but defensive coding)

## Code Examples

### Example 1: Catch-up Cron Full Implementation

```python
#!/usr/bin/env python3
"""
Email catch-up: poll Resend for missed inbound emails.
Run by cron every 30 minutes.
"""
import json, subprocess, os, sys
from datetime import datetime, timedelta, timezone

RESEND_KEY = os.environ.get('RESEND_API_KEY', '')
DB_PATH = '/workspace/email.db'
LOOKBACK_HOURS = 2

# Step 1: Fetch recent received emails
result = subprocess.run(
    ['curl', '-s', '-X', 'GET',
     'https://api.resend.com/emails/receiving?limit=100',
     '-H', f'Authorization: Bearer {RESEND_KEY}'],
    capture_output=True, text=True
)
response = json.loads(result.stdout)
emails = response.get('data', [])

# Step 2: Filter to lookback window
cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
recent_emails = []
for email in emails:
    # Parse created_at (format: "2026-02-17T14:37:40.951732+00")
    created = email['created_at'].replace('+00', '+00:00')
    try:
        dt = datetime.fromisoformat(created)
        if dt >= cutoff:
            recent_emails.append(email)
    except ValueError:
        continue  # skip unparseable timestamps

# Step 3: Dedup against email.db
recovered = []
for email in recent_emails:
    eid = email['id']
    check = subprocess.run(
        ['sqlite3', DB_PATH,
         f"SELECT COUNT(*) FROM email_conversations WHERE resend_email_id='{eid}';"],
        capture_output=True, text=True
    )
    if check.stdout.strip() == '0':
        recovered.append(email)

# Step 4: Report
if recovered:
    print(f'RECOVERED {len(recovered)} missed email(s):')
    for e in recovered:
        print(f'  From: {e["from"]} | Subject: {e["subject"]} | ID: {e["id"]}')
    # Bob then processes each via Section 8 of resend-email skill
else:
    print('Catch-up check: all clear.')
```

### Example 2: Quota Enforcement (SKILL.md Addition)

```python
import json
from datetime import datetime

def check_quota():
    with open('/workspace/email-config.json') as f:
        config = json.load(f)

    today = datetime.utcnow().strftime('%Y-%m-%d')
    this_month = datetime.utcnow().strftime('%Y-%m')

    # Daily reset
    if config.get('daily_send_date') != today:
        config['daily_send_count'] = 0
        config['daily_send_date'] = today
        config['alert_count_today'] = 0

    # Monthly reset
    if config.get('monthly_send_month') != this_month:
        config['monthly_send_count'] = 0
        config['monthly_send_month'] = this_month

    daily = config.get('daily_send_count', 0)
    monthly = config.get('monthly_send_count', 0)

    # Hard blocks
    if daily >= 95:
        return 'BLOCK', f'Daily limit reached ({daily}/100). Only 5 remaining for critical alerts.', config
    if monthly >= 2700:
        return 'BLOCK', f'Monthly limit approaching ({monthly}/3000). Refusing non-critical sends.', config

    # Warnings
    if daily >= 80:
        return 'WARN', f'Daily sends at {daily}/100. Approaching limit.', config

    return 'OK', f'Daily: {daily}/100, Monthly: {monthly}/3000', config


def after_send(config):
    config['daily_send_count'] = config.get('daily_send_count', 0) + 1
    config['monthly_send_count'] = config.get('monthly_send_count', 0) + 1
    with open('/workspace/email-config.json', 'w') as f:
        json.dump(config, f, indent=2)
```

### Example 3: Email Health SQL Report

```sql
-- Weekly email health summary
-- Run by ops agent, host path: /home/ubuntu/clawd/agents/main/email.db
-- (embedded mode uses host paths, NOT /workspace/)

-- Section 1: Volume
SELECT
    SUM(CASE WHEN direction='outbound' AND created_at >= datetime('now', '-7 days') THEN 1 ELSE 0 END) AS outbound_week,
    SUM(CASE WHEN direction='inbound' AND created_at >= datetime('now', '-7 days') THEN 1 ELSE 0 END) AS inbound_week,
    SUM(CASE WHEN direction='outbound' AND created_at >= datetime('now', '-30 days') THEN 1 ELSE 0 END) AS outbound_month,
    SUM(CASE WHEN direction='inbound' AND created_at >= datetime('now', '-30 days') THEN 1 ELSE 0 END) AS inbound_month
FROM email_conversations;

-- Section 2: Delivery outcomes (last 7 days, outbound only)
SELECT
    delivery_status,
    COUNT(*) AS count
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days')
GROUP BY delivery_status;

-- Section 3: Bounce rate
SELECT
    CASE
        WHEN COUNT(*) < 10 THEN 'LOW_VOLUME'
        ELSE CAST(ROUND(
            CAST(SUM(CASE WHEN delivery_status='bounced' THEN 1 ELSE 0 END) AS REAL) /
            COUNT(*) * 100, 2
        ) AS TEXT) || '%'
    END AS bounce_rate,
    SUM(CASE WHEN delivery_status='bounced' THEN 1 ELSE 0 END) AS bounced,
    COUNT(*) AS total
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days');

-- Section 4: Complaint rate
SELECT
    CASE
        WHEN COUNT(*) < 20 THEN 'LOW_VOLUME'
        ELSE CAST(ROUND(
            CAST(SUM(CASE WHEN delivery_status='complained' THEN 1 ELSE 0 END) AS REAL) /
            COUNT(*) * 100, 2
        ) AS TEXT) || '%'
    END AS complaint_rate,
    SUM(CASE WHEN delivery_status='complained' THEN 1 ELSE 0 END) AS complained,
    COUNT(*) AS total
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at >= datetime('now', '-7 days');
```

### Example 4: DMARC DNS Record Update

```bash
# Step 1: Verify current DMARC (should be p=none)
dig TXT _dmarc.mail.andykaufman.net +short
# Expected: "v=DMARC1; p=none;"

# Step 2: After 2 clean weeks, update DNS to:
# Name: _dmarc.mail.andykaufman.net
# Type: TXT
# Value: "v=DMARC1; p=quarantine; pct=100;"

# Step 3: Verify the change propagated
dig TXT _dmarc.mail.andykaufman.net +short
# Expected: "v=DMARC1; p=quarantine; pct=100;"

# Step 4: Send test email and verify inbox placement
# (manual -- Andy checks Gmail)
```

## Discretion Recommendations

### SQL Queries for Rate Calculations

**Recommendation:** Use the queries from Pattern 4 above, with the low-volume threshold guard (Pitfall 4). Key design choices:
- `NULLIF(COUNT(*), 0)` prevents division by zero
- `CASE WHEN COUNT(*) < N THEN 'LOW_VOLUME'` avoids misleading percentages on tiny samples
- All queries use `datetime('now', '-7 days')` for rolling window (UTC, timezone-agnostic)
- `CASE WHEN` instead of `FILTER (WHERE ...)` for SQLite compatibility

### Email Health Reporting: Separate EMAIL_HEALTH.md

**Recommendation:** Create a separate EMAIL_HEALTH.md in Bob's workspace (not ops/Sentinel workspace), NOT modify PIPELINE_REPORT.md. Rationale:
- PIPELINE_REPORT.md is Sentinel's reference doc for content pipeline reporting, targeting #ops
- Email health is Bob's domain, targeting #popsclaw
- Different agents, different channels, different concerns
- Add email health to the existing morning briefing section (a brief "email health" line at the end) rather than creating a separate cron. The weekly deep-dive can be triggered manually or added as a section to the weekly review cron.
- If a separate cron is desired later, EMAIL_HEALTH.md follows the same pattern as STUCK_DETECTION.md

Actually, reconsidering: the user said "weekly section in ops reporting." This suggests adding to an existing ops cron, not Bob's briefing. But PIPELINE_REPORT.md targets Sentinel on #ops -- email health should go to #popsclaw via Bob. **Final recommendation:** Create EMAIL_HEALTH.md in Bob's workspace (`~/clawd/agents/main/EMAIL_HEALTH.md`), add a weekly email-health-check cron targeting main (Bob), posting to #popsclaw. This keeps the ops boundary clean. Alternatively, add a brief email health check to the morning briefing (Bob already checks counters). Simplest: add daily email health check as a subsection of the morning briefing cron. Weekly deep-dive as manual request.

**Simplest approach that satisfies the requirement:** Add email health metrics to Bob's morning briefing as a brief section. Bob already reads email-config.json for the email send step. Add a "Section N: Email Health Check" that runs the bounce/complaint SQL queries, reports numbers, and fires alerts if thresholds are crossed. No separate cron needed.

### Catch-up Cron Session Naming and Timeout

**Recommendation:**
- Name: `email-catchup` (concise, descriptive, consistent with existing cron naming: `stuck-check`, `pipeline-report`)
- Session target: `isolated` (ephemeral, doesn't pollute Bob's main session)
- Timeout: `120000` ms (120s). Sufficient for 1 API call + 100 dedup checks + processing up to 5 recovered emails
- Schedule: `15,45 * * * *` (offset from :00/:30 to avoid collision with airspace-email-monitor at `0,30`)
- Delivery mode: `silent` (agent decides whether to notify based on recovery count)
- Model: `sonnet` (simple API + SQL logic, no need for opus)

### WARMUP.md Checklist Ordering

**Recommendation:** Order by dependency chain:
1. DNS verification first (SPF, DKIM, DMARC records exist)
2. Authentication headers second (SPF/DKIM PASS in Gmail "Show original")
3. Inbox placement third (not spam)
4. 2-week monitoring period fourth (ongoing)
5. DMARC escalation last (requires all above to be clean)

Each step has a checkbox. Bob can update the status field at the top of the doc. The checklist is a reference doc in Bob's workspace, not an ops doc -- Bob owns the warmup process.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual warmup schedules (day 1: 50 emails, day 2: 100...) | Shared IP warmup is mostly handled by provider | 2024+ (Resend shared IPs) | At 5-10 emails/day on shared IPs, formal warmup schedule is unnecessary. Just verify authentication |
| Dedicated IP for all senders | Shared IP for low-volume, dedicated for high-volume | Always | Free tier uses shared IPs. Warmup is already done by other senders on the pool |
| Manual daily quota tracking spreadsheet | API response headers + local JSON counters | 2024+ (Resend API headers) | `x-resend-daily-quota` and `x-resend-monthly-quota` headers provide real-time remaining quota |
| DMARC p=reject from day 1 | Progressive enforcement (none -> quarantine -> reject) | Best practice since RFC 7489 | Prevents accidental self-blocking during authentication setup |

**Deprecated/outdated:**
- Formal 30-60 day warmup schedules for shared IP senders: only needed for dedicated IPs or high-volume senders (1000+ emails/day). At 5-10/day on shared IPs, not applicable.
- Warmup services (third-party tools that send fake emails to build reputation): never needed for personal email from verified domains at low volume.

## Open Questions

1. **Resend List Received Emails sort order and consistency**
   - What we know: API returns emails newest-first (based on Context7 response example). Cursor-based pagination via `after`/`before` IDs.
   - What's unclear: Whether sort order is guaranteed, or if new emails can appear "between" pages during pagination.
   - Recommendation: Not a concern at current volume. `limit=100` returns all recent emails in one call. Pagination will only be needed if daily inbound volume exceeds 100 (extremely unlikely for personal email).
   - Confidence: MEDIUM (API docs don't explicitly state sort guarantee)

2. **delivery_status = 'unknown' for old emails without webhook events**
   - What we know: `delivery_status` defaults to 'unknown' in the schema. Webhook events update it to 'delivered', 'bounced', etc. But if the webhook was down when the delivery event fired, the status stays 'unknown'.
   - What's unclear: Whether Resend provides a `GET /emails/{id}` endpoint that returns delivery status for sent emails (to backfill 'unknown' records).
   - Recommendation: At current volume, manually check the few 'unknown' records. Not a priority for automation. Include a note in EMAIL_HEALTH.md that 'unknown' status means "delivery event not received" (not necessarily failed).
   - Confidence: MEDIUM (gap in current delivery tracking pipeline)

3. **Both sent and received emails count toward Resend free tier quotas**
   - What we know: Resend docs state "Both sent and received emails count towards these quotas."
   - What's unclear: At what rate inbound emails consume quota. If Bob receives 20 inbound emails/day, that's 20 against the 100/day and 3000/month limits.
   - Recommendation: Factor inbound volume into quota alerts. Current threshold of 80/day warning assumes mostly outbound. If inbound grows, may need to lower warning threshold. Monitor via `x-resend-monthly-quota` header.
   - Confidence: HIGH (Resend docs explicit: "Both sent and received emails count towards these quotas")

## Sources

### Primary (HIGH confidence)
- [Resend List Received Emails API](https://resend.com/docs/api-reference/emails/list-received-emails) -- Endpoint, parameters (limit, after, before), response format (Context7 verified)
- [Resend Usage Limits / Rate Limits](https://resend.com/docs/api-reference/rate-limit) -- `x-resend-daily-quota`, `x-resend-monthly-quota` response headers, 429 error codes, 2 req/s rate limit (Context7 verified)
- [Resend Account Quotas and Limits](https://resend.com/docs/knowledge-base/account-quotas-and-limits) -- Bounce rate <4%, spam rate <0.08%, free tier 100/day 3000/month. "Both sent and received count" (Context7 verified)
- [Resend DMARC for Subdomains](https://resend.com/blog/how-dmarc-applies-to-subdomains) -- Subdomain DMARC inheritance, sp= tag behavior (WebSearch verified)
- [Resend DMARC Policy Modes](https://resend.com/blog/dmarc-policy-modes) -- none/quarantine/reject progression, pct= tag usage (WebSearch verified)
- [Resend Domain Warmup Guide](https://resend.com/docs/knowledge-base/warming-up) -- Shared IP warmup already handled, dedicated IP warmup managed by Resend (WebSearch verified)
- [Resend Managing Domains](https://resend.com/docs/dashboard/domains/introduction) -- SPF/DKIM DNS record verification process (Context7 verified)
- [Resend DMARC Setup](https://resend.com/docs/dashboard/domains/dmarc) -- Prerequisites (SPF+DKIM verified domain), implementation steps (Context7 verified)
- [Svix Retry Schedule](https://docs.svix.com/retries) -- Retry schedule: immediately, 5s, 5m, 30m, 2h, 5h, 10h, 10h. Total ~34 hours before endpoint disabled (WebSearch verified)
- [Resend Pagination](https://resend.com/docs/api-reference/pagination) -- Cursor-based pagination, limit/after/before parameters (Context7 verified)

### Secondary (MEDIUM confidence)
- [Resend Avoiding Gmail Spam](https://resend.com/docs/knowledge-base/how-do-i-avoid-gmails-spam-folder) -- SPF/DKIM baseline, DMARC/BIMI additional trust
- [Valimail DMARC Policy Configuration](https://www.valimail.com/resources/guides/email-security-best-practices/how-to-configure-dmarc-policy-to-reject-or-quarantine/) -- none -> quarantine -> reject progression, pct= rollout
- [Resend Do You Need a Warmup Service](https://resend.com/blog/do-you-need-a-warmup-service) -- Low-volume senders on shared IPs don't need warmup services

### Tertiary (LOW confidence)
- Resend `x-resend-daily-quota` header exact format -- confirmed to exist in docs, but exact numeric format (remaining count vs used count) needs runtime verification with a real API call

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All components are existing infrastructure (Resend API, email.db, email-config.json, cron, SKILL.md). No new tools or services.
- Architecture: HIGH -- All four workstreams follow proven project patterns (reference doc, cron job, SQL queries, JSON config). Research identified the "no date filter" API limitation and provided the client-side workaround.
- Pitfalls: HIGH -- Key risks identified: no API date filter (verified via Context7), monthly counter reset gap, low-volume rate misleading metrics, DMARC escalation risk. All have documented mitigations.

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable domain -- Resend API v1, DNS/DMARC standards, SQLite patterns all mature/stable)
