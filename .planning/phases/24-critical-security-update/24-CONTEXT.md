# Phase 24: Critical Security Update - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Update OpenClaw from v2026.2.6-3 to v2026.2.17 on EC2 and install SecureClaw security plugin. Configure 15 runtime behavioral rules and pass 51-check security audit with zero critical failures. Gateway must be running and Bob responsive after update.

Full cron/skill/agent verification is Phase 25. Email domain hardening is Phase 27. Doctor warning cleanup is Phase 28.

</domain>

<decisions>
## Implementation Decisions

### SecureClaw Strictness
- Start strict + whitelist: enable all 15 rules at max strictness, carve exceptions for Bob's known workflows
- Pre-approve known exceptions: audit Bob's workflows (browser, email, file writes, external APIs, crons) against the 15 rules BEFORE enabling, so nothing breaks on day one
- Gate cron jobs too: cron-triggered actions go through SecureClaw gates, no exemptions
- External content sandboxing: full sandbox for web-fetched content; known-source APIs (Gmail, Resend, Oura, Govee, Wyze, WordPress, gog) treated as semi-trusted since already behind Tailscale + SG + Docker

### Downtime & Timing
- No scheduling constraints: execute whenever ready, missing a cron run or two is fine
- Target under 30 minutes total downtime
- No downtime announcement needed (single user, running the update ourselves)
- Verify delivery immediately after restart: DM Bob to re-establish session, trigger a test cron to confirm delivery works

### Audit Failure Threshold
- SecureClaw 51-check audit: zero critical findings required, warnings OK and logged
- `openclaw doctor`: no NEW critical findings from the update; pre-existing warnings (deprecated auth profile, legacy session key) are Phase 28's problem
- Fix critical findings in Phase 24: if SecureClaw audit reveals a critical that requires config changes, fix it now rather than deferring to Phase 25
- Capture security baseline BEFORE update: run ClawdStrike + doctor pre-update for before/after comparison

### Rollback Plan
- Copy binary + config before update: backup current openclaw binary and openclaw.json to a backup dir for instant swap-back
- Backup gog keyring tokens before update: known corruption risk during major version migration; if corrupt, remove and re-auth with `--manual`
- Escape hatch: if SecureClaw causes unresolvable issues, disable the plugin but keep the patched binary; update and SecureClaw are separable
- Smoke test only in Phase 24: verify gateway is up, Bob responds to Slack, one cron fires; full 20-cron verification is Phase 25's scope

### Claude's Discretion
- Specific SecureClaw rule-to-workflow mapping (which rules need which exceptions)
- Backup directory location and naming
- Order of operations during the update procedure
- Which cron to use for smoke test

</decisions>

<specifics>
## Specific Ideas

- Known update procedure from MEMORY.md: `npm install -g openclaw@latest` -> `openclaw doctor --fix` -> restart service
- Known gotchas: service entrypoint mismatches after update (doctor flags), gog keyring corruption, gateway restart clears DM sessions
- ClawdStrike baseline currently: 16/25 OK, 3 warn
- Gateway binds tailnet (100.72.143.9:18789) — must verify this survives the update
- `gateway.remote.url` in openclaw.json is critical for CLI commands — verify preserved

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 24-critical-security-update*
*Context gathered: 2026-02-17*
