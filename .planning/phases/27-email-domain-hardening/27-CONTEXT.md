# Phase 27: Email Domain Hardening - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Escalate email domain (mail.andykaufman.net) from DMARC p=none to production-grade deliverability. Execute warmup checklist, verify inbox placement, establish health monitoring. Prerequisite gate for Phase 29 subscriber sends.

</domain>

<decisions>
## Implementation Decisions

### DMARC escalation strategy
- Staged: p=none (current) → p=quarantine (this phase) → p=reject (deferred)
- Skip percentage ramp — go straight to p=quarantine pct=100 (low volume, auth already configured via Resend SPF+DKIM)
- Monitor DMARC aggregate reports (rua) for 48 hours post-escalation before declaring success
- p=reject deferred until after Phase 29 proves digest sends are clean

### Warmup execution
- Execute WARMUP.md 5 steps sequentially, verify each before moving on
- Inbox placement: send test emails to personal Gmail + AirSpace account, confirm inbox delivery (not spam)
- DNS verification: automated dig checks for SPF, DKIM, DMARC records
- "Verified" = all 5 steps green + at least one successful inbox placement test

### Health monitoring & thresholds
- Pull metrics from Resend API (bounce rate, complaint rate)
- Surface in morning briefing for ongoing visibility
- Red thresholds: bounce ≥5% or complaint ≥0.1% (matching phase success criteria)
- If metrics go red: pause and investigate before Phase 29 proceeds — no auto-escalation, morning briefing flags for manual decision

### Timing & readiness gate
- Minimum 7 days of clean sending data at p=quarantine before Phase 29 is unblocked
- "Clean" = bounce <5%, complaint <0.1%, no DMARC failures in aggregate reports
- If insufficient send volume for meaningful stats, send test emails during warmup to seed baseline data

### Claude's Discretion
- Exact dig command formatting and verification scripts
- How to parse Resend API metrics (polling frequency, storage)
- Morning briefing section placement for email health
- Test email content and cadence during warmup

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- DMARC p=reject escalation — after Phase 29 digest sends prove clean
- Automated DMARC report parsing (currently manual rua review)

</deferred>

---

*Phase: 27-email-domain-hardening*
*Context gathered: 2026-02-19*
