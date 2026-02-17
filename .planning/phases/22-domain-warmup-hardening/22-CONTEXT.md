# Phase 22: Domain Warmup & Production Hardening - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish mail.andykaufman.net domain reputation, add send quota monitoring with alerts, create a catch-up cron as webhook downtime fallback, and monitor bounce/complaint rates. No new email capabilities — this hardens the existing Resend integration from Phases 19-21.

</domain>

<decisions>
## Implementation Decisions

### Warmup Strategy
- No formal warmup schedule — volume is 5-10 emails/day to 1-2 known recipients on Resend shared IPs
- WARMUP.md reference doc in Bob's workspace: checklist to verify SPF/DKIM pass, confirm Gmail inbox placement, escalate DMARC to p=quarantine after 2 clean weeks
- Not a cron — a one-time checklist Bob works through manually

### Quota & Alerting
- Daily send quota tracking already exists in email-config.json (daily_send_count)
- Add threshold alert at 80/day (warning) and hard-block at 95/day (safety margin below 100 free tier limit)
- Add monthly_send_count to email-config.json, alert at 2700/month (90% of 3000)
- Alert channel: #popsclaw (same as all Bob alerts)
- When limit hit: Bob refuses to send, logs refusal, notifies Andy — no silent failures

### Catch-up Cron
- Poll Resend Received Emails API every 30 minutes (isolated session, sonnet, 120s timeout)
- Dedup: query email.db for existing resend_email_id, skip already-processed
- Lookback window: 2 hours (covers brief outages; Svix retries cover up to 27.5hr)
- Silent when healthy — only notify if catch-up actually recovers missed emails

### Monitoring Scope
- Bounce/complaint rates via SQL queries on email.db (same pattern as stuck-detection)
- Weekly section in ops reporting: bounce rate, complaint rate, total sent week/month, delivery success %
- Threshold alerts: bounce >2% or complaint >0.08% → immediate #popsclaw alert
- No dashboard — SQLite queries + cron alerts sufficient at this volume

### Claude's Discretion
- Exact SQL queries for rate calculations
- Whether to add email health to existing PIPELINE_REPORT.md or create separate EMAIL_HEALTH.md
- Catch-up cron session naming and timeout tuning
- WARMUP.md checklist ordering and wording

</decisions>

<specifics>
## Specific Ideas

- Reuse existing patterns: reference doc + cron + SQL queries (like stuck-detection and pipeline-report)
- email-config.json is the single source for quota state — no new DB tables for quota tracking
- DMARC escalation (p=none → p=quarantine) is manual after Andy confirms inbox placement

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 22-domain-warmup-hardening*
*Context gathered: 2026-02-17*
