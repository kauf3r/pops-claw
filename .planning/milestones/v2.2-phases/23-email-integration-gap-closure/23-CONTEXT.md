# Phase 23: Email Integration Gap Closure - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Close 3 specific gaps identified in the v2.2 milestone audit. All are surgical fixes to existing infrastructure — no new capabilities. The catch-up cron API endpoint, counter double-increment, and n8n hardcoded token.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User deferred all implementation decisions to Claude. Recommended approaches below:

**1. Catch-up cron API endpoint**
- Verify the current `GET /emails/receiving` endpoint against Resend API docs
- If endpoint is wrong or deprecated: replace with correct Resend received-emails endpoint in jobs.json cron definition
- If endpoint is correct but returning unexpected results: fix the parsing/processing logic
- Keep the cron pattern (every 30 min at :15/:45) unchanged — only fix the API call itself
- Preserve dedup-via-email.db behavior

**2. Counter double-increment**
- Section 6 (the actual send step) should own the `daily_send_count` increment — it fires after a successful send
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

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. All 3 fixes are well-defined from the milestone audit.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 23-email-integration-gap-closure*
*Context gathered: 2026-02-17*
