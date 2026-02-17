# Phase 23: Email Integration Gap Closure - Research

**Researched:** 2026-02-17
**Domain:** Resend email integration (API, SKILL.md instructions, n8n workflow)
**Confidence:** HIGH

## Summary

Three gaps were identified in the v2.2 milestone audit. Research confirms that two of the three are genuine issues requiring fixes, while one (the n8n hardcoded token) appears to have already been resolved in the live workflow.

**Gap 1 (Catch-up cron API endpoint):** The `GET /emails/receiving?limit=100` endpoint is CONFIRMED WORKING. Live test against Resend API returned valid `{object, has_more, data}` response with expected email metadata. The audit flagged this as "unconfirmed" but the endpoint exists and functions correctly per Resend's official API documentation. **No code change needed -- only verification and documentation update.**

**Gap 2 (Counter double-increment):** CONFIRMED. Section 6 Step 8 of SKILL.md explicitly instructs "Increment `daily_send_count` in the config" after sending the morning briefing. Section 9 "After successful send" block also increments `daily_send_count` (and `monthly_send_count`). Since Section 9 runs before every outbound send (including briefings), the morning briefing triggers both increments. `monthly_send_count` is NOT double-incremented (only Section 9 handles it). Fix: remove Section 6 Step 8.

**Gap 3 (n8n hardcoded token):** The live n8n workflow in Postgres (11 nodes) already uses `$env.OPENCLAW_HOOKS_TOKEN` in both the "POST to OpenClaw" and "POST Delivery Status" node headers. The hardcoded token `982cbc4b...` does NOT appear anywhere in the live workflow data. However, the on-disk backup file (`resend-inbound-relay.json`) is stale (only 8 nodes, missing the delivery status routing entirely). **The live fix appears done, but the on-disk backup needs updating.**

**Primary recommendation:** Fix the SKILL.md counter double-increment (Gap 2), update the stale on-disk n8n workflow backup (Gap 3), and document the catch-up cron API as verified (Gap 1).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
(none -- all implementation decisions deferred to Claude's discretion)

### Claude's Discretion

User deferred all implementation decisions to Claude. Recommended approaches below:

**1. Catch-up cron API endpoint**
- Verify the current `GET /emails/receiving` endpoint against Resend API docs
- If endpoint is wrong or deprecated: replace with correct Resend received-emails endpoint in jobs.json cron definition
- If endpoint is correct but returning unexpected results: fix the parsing/processing logic
- Keep the cron pattern (every 30 min at :15/:45) unchanged -- only fix the API call itself
- Preserve dedup-via-email.db behavior

**2. Counter double-increment**
- Section 6 (the actual send step) should own the `daily_send_count` increment -- it fires after a successful send
- Section 9 (quota enforcement) should only READ the count to check thresholds, never increment
- Remove the duplicate increment from whichever section is the redundant one
- Same logic applies to `monthly_send_count` if similarly duplicated
- Single source of truth: increment happens once, at send time

**3. n8n delivery status hardcoded token**
- Replace inline token value in the n8n delivery status POST node with `{{$env.OPENCLAW_HOOKS_TOKEN}}`
- Add `OPENCLAW_HOOKS_TOKEN` to the n8n Docker `.env` file on VPS (165.22.139.214)
- Recreate n8n container (`docker compose up -d --force-recreate n8n`) for env var pickup
- Value: the existing hooks token (982cbc4b...)

**Verification approach**
- Each fix verified independently via live E2E test after deployment
- Catch-up cron: trigger manually, confirm API response and email.db dedup
- Counter: send test email, confirm daily_send_count increments by exactly 1
- n8n token: trigger a delivery status webhook, confirm it reaches Bob via hooks

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

## Standard Stack

### Core
| Component | Location | Purpose | Current State |
|-----------|----------|---------|---------------|
| SKILL.md | `~/.openclaw/skills/resend-email/SKILL.md` | 13-section agent instruction set for email operations | Active, has counter bug |
| jobs.json | `~/.openclaw/cron/jobs.json` | Cron job definitions including `email-catchup` | Active, endpoint is valid |
| n8n workflow | Postgres on VPS (`1XwpGnGro0NYtOjE`) | 11-node Resend inbound relay + delivery status routing | Active, token already env-referenced |
| email-config.json | `~/clawd/agents/main/email-config.json` (host) / `/workspace/email-config.json` (sandbox) | Counter state, recipients, allowlist | Active |
| email.db | `~/clawd/agents/main/email.db` (host) / `/workspace/email.db` (sandbox) | SQLite conversation tracker with dedup | Active |

### Supporting
| Component | Location | Purpose |
|-----------|----------|---------|
| n8n .env | `/home/officernd/n8n-production/.env` on VPS | Environment variables including `OPENCLAW_HOOKS_TOKEN`, `RESEND_API_KEY` |
| n8n backup | `/home/officernd/n8n-production/workflows/resend-inbound-relay.json` on VPS | Stale on-disk workflow backup (8 nodes vs 11 live) |
| docker-compose.yml | `/home/officernd/n8n-production/docker-compose.yml` on VPS | n8n container orchestration |

## Architecture Patterns

### Resend API: List Received Emails Endpoint

**Confirmed working.** Live-tested on EC2.

```
GET https://api.resend.com/emails/receiving
Authorization: Bearer $RESEND_API_KEY

Query Parameters:
  limit  (number, optional) - 1 to 100, default 20
  after  (string, optional) - pagination cursor (email ID), cannot use with before
  before (string, optional) - pagination cursor (email ID), cannot use with after

Response:
{
  "object": "list",
  "has_more": true|false,
  "data": [
    {
      "id": "uuid",
      "to": ["recipient@example.com"],
      "from": "sender@example.com",
      "created_at": "2026-02-17 17:21:04.252224+00",
      "subject": "Subject line",
      "bcc": [],
      "cc": [],
      "reply_to": [],
      "message_id": "<rfc2822-message-id@example.com>",
      "attachments": [{"filename": "...", "content_type": "...", "content_id": null}]
    }
  ]
}
```

Source: Resend official API docs (https://resend.com/docs/api-reference/emails/list-received-emails), confirmed via Context7 (/websites/resend), and live API test returning valid data.

### SKILL.md Counter Flow (Current - Buggy)

When the morning briefing email is sent:

1. Section 9 Check 0 runs BEFORE sending (resets daily/monthly if new day/month)
2. Section 6 Steps 1-6 compose and send the email via Section 2 curl pattern
3. Section 6 Step 7 resets `daily_send_date` and `alert_count_today`
4. **Section 6 Step 8 increments `daily_send_count`** <-- FIRST INCREMENT
5. Section 9 "After successful send" increments `daily_send_count` AND `monthly_send_count` <-- SECOND INCREMENT

Result: `daily_send_count` = +2 per briefing email (should be +1). `monthly_send_count` = +1 (correct, only incremented in Section 9).

### SKILL.md Counter Flow (Fixed)

Remove Section 6 Step 8 entirely. Section 9's "After successful send" block handles ALL counter increments for ALL outbound emails (briefings, alerts, replies, ad-hoc). This is the correct single-source-of-truth pattern.

**Note on Context Decision divergence:** The CONTEXT.md suggested Section 9 should only READ and Section 6 should own the increment. However, research shows the opposite is better: Section 9 is the universal "after send" handler that runs for ALL email types, while Section 6 is briefing-specific. If Section 6 owned the increment, alerts (Section 5) and replies (Section 10) would need their own increment logic too, creating more duplication. Section 9's centralized increment is the correct design.

### n8n Workflow Architecture (Live)

```
Webhook Trigger
    |
Verify Svix Signature --[error]--> Respond 401
    |
Extract Metadata (routes: inbound | delivery_status)
    |
Route Events (IF route == "inbound")
    |                          |
   [true]                   [false]
    |                          |
Fetch Body Preview      POST Delivery Status --> Respond 200 Delivery
    |                   (uses $env.OPENCLAW_HOOKS_TOKEN) <-- ALREADY CORRECT
Extract Body Preview
    |
POST to OpenClaw --> Respond 200 OK
(uses $env.OPENCLAW_HOOKS_TOKEN) <-- ALREADY CORRECT
```

The workflow correctly branches: inbound emails go through body fetch + preview extraction before posting to OpenClaw; delivery status events go directly to POST Delivery Status. Both POST nodes use `$env.OPENCLAW_HOOKS_TOKEN`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron API verification | Custom polling script | Existing `email-catchup` cron job in jobs.json | Already polls correctly; just needs documentation update |
| Counter management | Per-section increment logic | Section 9 centralized "after send" block | Universal handler for all email types prevents duplication |
| Token management | Per-node hardcoded values | n8n `$env` references | Already implemented in live workflow |

## Common Pitfalls

### Pitfall 1: Moving Increment to Wrong Section
**What goes wrong:** If Section 6 owns the increment (as CONTEXT.md suggested) instead of Section 9, then alerts (Section 5) and replies (Section 10) would each need their own increment logic.
**Why it happens:** Section 6 "fires after a successful send" but so do Sections 5, 10, and any ad-hoc send. Section 9 is the only section that runs before ALL outbound sends.
**How to avoid:** Keep the increment in Section 9 (centralized). Remove Section 6 Step 8. Section 9's "After successful send" block already handles both `daily_send_count` and `monthly_send_count`.
**Warning signs:** If after the fix, `monthly_send_count` increments but `daily_send_count` doesn't, the wrong section was modified.

### Pitfall 2: Stale On-Disk Workflow Backup
**What goes wrong:** The file `/home/officernd/n8n-production/workflows/resend-inbound-relay.json` has only 8 nodes (the initial deployment). The live workflow in Postgres has 11 nodes (with delivery status routing added later).
**Why it happens:** n8n stores active workflows in Postgres; the JSON file was the initial import/seed and was never re-exported.
**How to avoid:** After confirming the live workflow is correct, export it to update the on-disk backup: `docker exec n8n n8n export:workflow --id=1XwpGnGro0NYtOjE --output=/tmp/wf.json` then copy to the workflows directory.
**Warning signs:** If someone later tries to re-import from the on-disk file, they'd lose the delivery status routing.

### Pitfall 3: Section 6 Step 7 Date Reset Interaction
**What goes wrong:** Section 6 Step 7 resets `daily_send_date` to today AND `alert_count_today` to 0. Section 9 Check 0 also resets daily counter if new day. Both are fine because the morning briefing runs first each day, establishing the date. But if Step 7 runs AFTER Section 9's Check 0 in the same request, the Check 0 reset and Step 7 reset are redundant but harmless.
**How to avoid:** No action needed. Both resets are idempotent. Just be aware they overlap.

### Pitfall 4: n8n Container Restart Not Needed
**What goes wrong:** Unnecessarily restarting the n8n container when the live workflow already uses env vars correctly.
**Why it happens:** The CONTEXT.md assumed the token was hardcoded and prescribed a container restart.
**How to avoid:** Verify current state before acting. The `OPENCLAW_HOOKS_TOKEN` is already in `.env` AND already referenced by `$env.OPENCLAW_HOOKS_TOKEN` in the live workflow. No container restart needed unless the env var value itself changes.

## Code Examples

### Verified: email-catchup cron job definition (from jobs.json)

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
  "timeout": 120000,
  "payload": {
    "kind": "agentTurn",
    "message": "Email catch-up check: poll Resend Received Emails API...\n1. Fetch recent emails: curl -s -X GET 'https://api.resend.com/emails/receiving?limit=100' -H \"Authorization: Bearer $RESEND_API_KEY\"\n2. For each email, check email.db dedup...",
    "model": "sonnet"
  },
  "delivery": { "mode": "silent" }
}
```

### Verified: SKILL.md Section 6 Steps 7-8 (the buggy section)

```markdown
7. Reset `daily_send_date` to today and `alert_count_today` to 0 (daily counter reset happens with the morning briefing)
8. Increment `daily_send_count` in the config   <-- REMOVE THIS STEP
9. If the email send fails, log the error in Slack but do NOT block or retry the Slack briefing
```

After fix, Steps 7-8 become:
```markdown
7. Reset `daily_send_date` to today and `alert_count_today` to 0 (daily counter reset happens with the morning briefing)
8. If the email send fails, log the error in Slack but do NOT block or retry the Slack briefing
```

### Verified: Section 9 "After successful send" block (the correct single increment)

```python
config['daily_send_count'] = config.get('daily_send_count', 0) + 1
config['monthly_send_count'] = config.get('monthly_send_count', 0) + 1

with open('/workspace/email-config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

This block remains unchanged. It is the single source of truth for counter increments.

### Verified: n8n workflow export command

```bash
# Export live workflow from Postgres to update stale on-disk backup
docker exec n8n sh -c "n8n export:workflow --id=1XwpGnGro0NYtOjE" > /home/officernd/n8n-production/workflows/resend-inbound-relay.json
```

### Verified: Resend list received emails API test

```bash
# Returns valid {object, has_more, data} response
curl -s -X GET 'https://api.resend.com/emails/receiving?limit=2' \
  -H "Authorization: Bearer $RESEND_API_KEY"
# Response includes: id, to, from, created_at, subject, message_id, attachments
```

## State of the Art

| What Audit Said | What Research Found | Impact |
|-----------------|---------------------|--------|
| Catch-up cron API endpoint unconfirmed | Endpoint `GET /emails/receiving` is real, documented, and returns valid data | Gap 1 requires NO code fix, only verification acknowledgment |
| Counter double-increment in Sections 6+9 | Confirmed: Section 6 Step 8 and Section 9 both increment `daily_send_count` | Gap 2 requires removing Section 6 Step 8 from SKILL.md |
| n8n delivery status node has hardcoded token | Live workflow already uses `$env.OPENCLAW_HOOKS_TOKEN`; on-disk backup is stale | Gap 3 requires updating stale backup file, not the live workflow |

**Key insight:** Two of three gaps are simpler than expected. The catch-up cron works correctly. The n8n token was already fixed in the live workflow. Only the counter double-increment requires an actual logic fix.

## Open Questions

1. **When was the n8n delivery status routing added?**
   - What we know: The live workflow has 11 nodes including delivery status routing with correct env var references. The on-disk backup has only 8 nodes (no delivery status routing).
   - What's unclear: Was the hardcoded token ever present in the live workflow, or was `$env` used from the start when delivery status routing was added?
   - Recommendation: Treat as resolved. Update the on-disk backup and mark Gap 3 as verified-already-fixed. The planner should still include a verification step.

2. **Should Section 9 increment logic be restructured?**
   - What we know: The CONTEXT.md suggested Section 6 should own the increment and Section 9 should only read. Research shows the opposite is better (Section 9 is the universal handler).
   - What's unclear: Whether the user has a strong preference for the CONTEXT.md approach.
   - Recommendation: The planner should follow the research finding (keep increment in Section 9, remove from Section 6) since it's the simpler and more maintainable approach. The CONTEXT.md was Claude's Discretion, not a locked decision.

## Sources

### Primary (HIGH confidence)
- Context7 `/websites/resend` - List Received Emails API endpoint specification, parameters, response format
- Context7 `/websites/resend_dashboard_receiving` - Receiving email content retrieval, webhook design
- Live API test on EC2 - `GET /emails/receiving?limit=2` returned valid `{object, has_more, data}` response
- Live n8n workflow export from Postgres via `docker exec n8n sh -c "n8n export:workflow --all"` - 11-node workflow with `$env.OPENCLAW_HOOKS_TOKEN` in both POST nodes
- SKILL.md on EC2 (`~/.openclaw/skills/resend-email/SKILL.md`) - 13 sections, counter logic in Sections 6 and 9
- jobs.json on EC2 (`~/.openclaw/cron/jobs.json`) - email-catchup cron definition
- email-config.json on EC2 (`~/clawd/agents/main/email-config.json`) - current counter state
- n8n .env on VPS (`/home/officernd/n8n-production/.env`) - confirms `OPENCLAW_HOOKS_TOKEN` already present

### Secondary (MEDIUM confidence)
- [Resend List Received Emails docs](https://resend.com/docs/api-reference/emails/list-received-emails) - Official API reference
- [Resend Retrieve Received Email docs](https://resend.com/docs/api-reference/emails/retrieve-received-email) - Single email retrieval endpoint
- [v2.2 Milestone Audit](../../v2.2-MILESTONE-AUDIT.md) - Gap identification source

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Gap 1 (Catch-up cron): HIGH - Live API test confirms endpoint works; official docs confirm specification
- Gap 2 (Counter double-increment): HIGH - Direct reading of SKILL.md Sections 6 and 9 confirms the bug
- Gap 3 (n8n token): HIGH - Live workflow export confirms `$env` already used; on-disk backup confirmed stale

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable infrastructure, no API changes expected)
