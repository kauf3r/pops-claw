# Phase 27: Email Domain Hardening - Research

**Researched:** 2026-02-19
**Domain:** DMARC policy escalation, domain warmup verification, email health monitoring via Resend API + SQLite
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### DMARC escalation strategy
- Staged: p=none (current) → p=quarantine (this phase) → p=reject (deferred)
- Skip percentage ramp — go straight to p=quarantine pct=100 (low volume, auth already configured via Resend SPF+DKIM)
- Monitor DMARC aggregate reports (rua) for 48 hours post-escalation before declaring success
- p=reject deferred until after Phase 29 proves digest sends are clean

#### Warmup execution
- Execute WARMUP.md 5 steps sequentially, verify each before moving on
- Inbox placement: send test emails to personal Gmail + AirSpace account, confirm inbox delivery (not spam)
- DNS verification: automated dig checks for SPF, DKIM, DMARC records
- "Verified" = all 5 steps green + at least one successful inbox placement test

#### Health monitoring & thresholds
- Pull metrics from Resend API (bounce rate, complaint rate)
- Surface in morning briefing for ongoing visibility
- Red thresholds: bounce ≥5% or complaint ≥0.1% (matching phase success criteria)
- If metrics go red: pause and investigate before Phase 29 proceeds — no auto-escalation, morning briefing flags for manual decision

#### Timing & readiness gate
- Minimum 7 days of clean sending data at p=quarantine before Phase 29 is unblocked
- "Clean" = bounce <5%, complaint <0.1%, no DMARC failures in aggregate reports
- If insufficient send volume for meaningful stats, send test emails during warmup to seed baseline data

### Claude's Discretion
- Exact dig command formatting and verification scripts
- How to parse Resend API metrics (polling frequency, storage)
- Morning briefing section placement for email health
- Test email content and cadence during warmup

### Deferred Ideas (OUT OF SCOPE)
- DMARC p=reject escalation — after Phase 29 digest sends prove clean
- Automated DMARC report parsing (currently manual rua review)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EML-01 | DMARC policy escalated from p=none to p=quarantine after confirming 2 clean weeks | DMARC DNS record update pattern, dig verification commands, rua tag for aggregate report monitoring, 48-hour post-escalation monitoring window |
| EML-02 | WARMUP.md 5-step checklist executed (DNS verified, auth tested, inbox placement confirmed, monitoring active) | WARMUP.md already deployed at `/home/ubuntu/clawd/agents/main/WARMUP.md` from Phase 22 -- needs execution not creation. Resend GET /domains/{id} API for DNS status, dig commands for SPF/DKIM/DMARC, Gmail "Show original" for auth headers |
| EML-03 | Email health metrics (bounce/complaint rates) trending clean in morning briefing | Morning briefing already has Section 9 (Email Health) from Phase 22. Phase 27 updates thresholds from 2%/0.08% to 5%/0.1% per CONTEXT.md decisions and adds readiness gate tracking |
</phase_requirements>

## Summary

Phase 27 is primarily an **execution and verification phase**, not a build phase. The infrastructure already exists from Phase 22 (v2.2): WARMUP.md checklist is deployed, email health is in morning briefing Section 9, bounce/complaint alerting is active, and email-catchup cron runs every 30 minutes. The work is: (1) execute the WARMUP.md steps via SSH (dig checks, test emails, inbox verification), (2) update the DMARC DNS record from p=none to p=quarantine with rua tag, (3) verify the escalation didn't break delivery, and (4) adjust monitoring thresholds to match phase success criteria (5%/0.1% vs Phase 22's 2%/0.08%).

The critical nuance: CONTEXT.md says "monitor DMARC aggregate reports (rua) for 48 hours post-escalation." The current DMARC record at `_dmarc.mail.andykaufman.net` likely has `v=DMARC1; p=none;` without an rua tag. Adding `rua=mailto:dmarc@andykaufman.net` (or similar) is needed to receive aggregate reports. This requires a dedicated mailbox or forwarding setup. STATE.md also notes: "DMARC rua mailbox: verify 14+ days of aggregate reports exist before Phase 27 escalation."

The readiness gate is the gatekeeper for Phase 29: 7 days of clean sending data at p=quarantine (bounce <5%, complaint <0.1%, no DMARC failures). At current volume (5-10 emails/day to 1-2 recipients), this should be straightforward if SPF/DKIM are already passing.

**Primary recommendation:** Single plan with 4 tasks: (1) Execute WARMUP.md Steps 1-3 (DNS verify, auth test, inbox placement), (2) Escalate DMARC to p=quarantine with rua tag, (3) Adjust morning briefing thresholds and add readiness gate tracking, (4) Post-escalation verification (48-hour check + test email). Tasks 1-2 are sequential (verify before escalating). Task 3 is independent. Task 4 depends on Task 2 but has a 48-hour wall-clock delay.

## Standard Stack

### Core

| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| `dig` CLI | built-in (EC2) | DNS record verification (SPF, DKIM, DMARC) | Standard DNS query tool. Already used in WARMUP.md |
| Resend API `GET /domains/{id}` | v1 | Retrieve domain DNS record status from Resend | Returns full record set with verification status per record (Context7 verified) |
| Resend Webhook Events | v1 | `email.bounced`, `email.complained` events for delivery tracking | Already configured (Phase 20-21). Events update delivery_status in email.db |
| SQLite (`email.db`) | 3.x (bind-mounted) | Bounce/complaint rate queries for health monitoring | Already deployed (Phase 21). Contains `email_conversations` with `delivery_status` column |
| Morning briefing cron | Section 9 | Email health check with SQL queries | Already deployed (Phase 22). Runs bounce/complaint SQL with threshold alerts |

### Supporting

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| `curl` (EC2 or sandbox) | built-in | Resend API calls for domain status check | One-time warmup verification + optional ongoing polling |
| DNS provider (andykaufman.net) | n/a | Update DMARC TXT record at `_dmarc.mail.andykaufman.net` | One-time DMARC escalation (Andy updates DNS manually) |
| Gmail "Show original" | n/a | Human verification of SPF/DKIM/DMARC headers | One-time auth test during warmup Step 2 |
| `email-config.json` | n/a | Quota counters + readiness gate status tracking | Add `dmarc_escalated_at` timestamp for 7-day gate calculation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual rua report review | DMARC report parsing service (e.g., PowerDMARC, DMARCLY) | Overkill at 5-10 emails/day. Manual review of XML attachments is sufficient. Deferred per CONTEXT.md |
| Resend API `GET /domains/{id}` for DNS check | `dig` commands only | API returns verification status directly; dig returns raw records. Both are useful -- API for quick status, dig for actual DNS propagation confirmation |
| Dedicated DMARC report mailbox | Forwarding to existing Gmail | Dedicated is cleaner but adds maintenance. Forwarding to personal Gmail is simpler at this volume |

**Installation:** No new packages. All components exist from Phase 22.

## Architecture Patterns

### Phase 27 Execution Flow

```
Task 1: Execute WARMUP.md Steps 1-3
  |-- SSH to EC2, run dig commands (SPF, DKIM, DMARC)
  |-- Bob sends test email to personal Gmail + AirSpace email
  |-- Andy checks "Show original" for SPF/DKIM/DMARC PASS
  |-- Andy confirms inbox placement (not spam) for both accounts
  |-- Mark Steps 1-3 as COMPLETE in WARMUP.md

Task 2: Escalate DMARC (Step 5 of WARMUP.md)
  |-- Andy updates DNS: _dmarc.mail.andykaufman.net
  |-- Old: v=DMARC1; p=none;
  |-- New: v=DMARC1; p=quarantine; pct=100; rua=mailto:<rua-address>;
  |-- Verify via dig: record propagated
  |-- Immediately send test email, verify inbox (not spam)
  |-- Mark Step 5 as COMPLETE in WARMUP.md

Task 3: Adjust monitoring thresholds + readiness gate
  |-- Update morning briefing Section 9 thresholds: 2%→5% bounce, 0.08%→0.1% complaint
  |-- Add readiness gate: "Phase 29 blocked until 7 days clean at p=quarantine"
  |-- Add dmarc_escalated_at to email-config.json (ISO timestamp)
  |-- Morning briefing reports days remaining until Phase 29 gate clears

Task 4: Post-escalation verification (48 hours after Task 2)
  |-- Check DMARC aggregate reports (if any arrive at rua address)
  |-- Verify all emails in 48-hour window delivered to inbox
  |-- Confirm email.db shows no bounces/complaints in window
  |-- Bob reports status in #popsclaw
```

### Pattern 1: DMARC Record Update with RUA Tag

**What:** Update the DMARC TXT record to enforce quarantine and enable aggregate reporting.
**When to use:** After WARMUP.md Steps 1-4 are verified clean.
**Source:** [DMARC RFC 7489](https://tools.ietf.org/html/rfc7489), [Resend DMARC docs](https://resend.com/docs/dashboard/domains/dmarc)

```bash
# Current record (verify first)
dig TXT _dmarc.mail.andykaufman.net +short
# Expected: "v=DMARC1; p=none;"

# New record to set in DNS provider:
# Name: _dmarc.mail.andykaufman.net
# Type: TXT
# Value: "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@andykaufman.net;"
#
# Tags:
#   p=quarantine  — unauthenticated emails get quarantined (spam folder)
#   pct=100       — apply to 100% of messages (no percentage ramp)
#   rua=mailto:   — receive daily aggregate XML reports at this address

# Verify propagation (may take up to 24 hours, often faster)
dig TXT _dmarc.mail.andykaufman.net +short
# Expected: "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@andykaufman.net;"
```

**RUA address options:**
1. `dmarc@andykaufman.net` — dedicated address (recommended). Andy creates a filter/label in Gmail to auto-organize.
2. `theandykaufman@gmail.com` — simpler, but DMARC reports clutter personal inbox.
3. Third-party service (e.g., DMARCLY, PowerDMARC free tier) — automated parsing, but adds external dependency. Deferred per CONTEXT.md.

**Recommendation:** Use `dmarc@andykaufman.net` (or `dmarc-reports@andykaufman.net`) with a Gmail filter to auto-label and archive. Reports arrive as XML attachments once daily from each major email provider that receives mail from this domain. At 5-10 emails/day to 1-2 recipients, expect 1-2 reports/day max (from Gmail).

### Pattern 2: DNS Verification via dig

**What:** Automated dig checks for all DNS authentication records.
**When to use:** WARMUP.md Step 1 execution.
**Source:** Phase 22 WARMUP.md deployed on EC2

```bash
# SPF Check
dig TXT send.mail.andykaufman.net +short
# Expected contains: "v=spf1 include:amazonses.com ~all"

# DKIM Check (3 selectors — standard Resend convention)
dig CNAME resend._domainkey.mail.andykaufman.net +short
dig CNAME resend2._domainkey.mail.andykaufman.net +short
dig CNAME resend3._domainkey.mail.andykaufman.net +short
# Each should resolve to *.dkim.amazonses.com

# DMARC Check
dig TXT _dmarc.mail.andykaufman.net +short
# Currently: "v=DMARC1; p=none;"
# After escalation: "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@andykaufman.net;"

# MX Record (for receiving)
dig MX send.mail.andykaufman.net +short
# Expected: feedback-smtp.us-east-1.amazonses.com (priority 10)
```

**Alternative: Resend API Domain Check**
```bash
# Get domain ID first (from Resend dashboard or list domains API)
curl -s -X GET 'https://api.resend.com/domains' \
  -H "Authorization: Bearer $RESEND_API_KEY" | python3 -m json.tool

# Get specific domain with DNS record status
curl -s -X GET 'https://api.resend.com/domains/{domain_id}' \
  -H "Authorization: Bearer $RESEND_API_KEY" | python3 -m json.tool

# Response includes per-record verification status:
# "records": [
#   {"record": "SPF", "status": "verified", ...},
#   {"record": "DKIM", "status": "verified", ...}
# ]
```

The `GET /domains/{domain_id}` endpoint returns the full DNS record set with per-record status (Context7 verified). This provides a quick programmatic check complementing manual dig verification.

### Pattern 3: Readiness Gate in Morning Briefing

**What:** Track days since DMARC escalation and report readiness for Phase 29.
**When to use:** Daily in morning briefing, starting after DMARC escalation.

```python
import json
from datetime import datetime, timezone

# Read escalation timestamp
with open('/workspace/email-config.json') as f:
    config = json.load(f)

escalated_at = config.get('dmarc_escalated_at')
if escalated_at:
    dt = datetime.fromisoformat(escalated_at)
    days_since = (datetime.now(timezone.utc) - dt).days
    if days_since >= 7:
        gate_status = "READY -- 7+ days clean at p=quarantine"
    else:
        gate_status = f"PENDING -- {days_since}/7 days ({7 - days_since} remaining)"
else:
    gate_status = "NOT STARTED -- DMARC not yet escalated"

print(f"Phase 29 Gate: {gate_status}")
```

**email-config.json addition:**
```json
{
  "dmarc_escalated_at": "2026-02-20T12:00:00Z",
  "dmarc_policy": "quarantine"
}
```

### Pattern 4: Threshold Update for Morning Briefing Section 9

**What:** Adjust existing bounce/complaint thresholds to match Phase 27 success criteria.
**When to use:** During phase execution.

Current thresholds (from Phase 22):
- Bounce alert: >2% (minimum 10 outbound)
- Complaint alert: >0.08% (minimum 20 outbound)

New thresholds (from CONTEXT.md):
- Bounce alert: >=5% (keep minimum volume guard)
- Complaint alert: >=0.1% (keep minimum volume guard)

The Phase 22 thresholds were based on Resend's account limits (4% bounce, 0.08% spam). Phase 27 thresholds are the phase success criteria. **Recommendation:** Keep both: the tighter Phase 22 thresholds as "warning" level and the Phase 27 thresholds as "critical/blocking" level.

```
Bounce:
  >=2% (min 10) → WARNING in #popsclaw (Resend account risk)
  >=5% (min 10) → CRITICAL in #popsclaw + Phase 29 gate blocked

Complaint:
  >=0.08% (min 20) → WARNING in #popsclaw (Resend account risk)
  >=0.1% (min 20) → CRITICAL in #popsclaw + Phase 29 gate blocked
```

This way the morning briefing catches issues at the Resend-level warning point (protecting the account) while the readiness gate uses the broader Phase 27 success criteria.

### Anti-Patterns to Avoid

- **Skipping dig verification before DMARC escalation:** Always confirm SPF/DKIM PASS via both dig and Gmail "Show original" before changing DMARC policy. Escalating with broken authentication = all emails go to spam.
- **Setting rua to a nonexistent mailbox:** If the rua address can't receive mail, aggregate reports silently fail. Verify the mailbox exists and can receive email before adding the rua tag.
- **Changing DMARC without immediately testing:** Always send a test email immediately after DNS propagation and verify inbox placement. Don't wait for the 48-hour monitoring window to discover problems.
- **Creating a new WARMUP.md:** WARMUP.md already exists at `/home/ubuntu/clawd/agents/main/WARMUP.md` from Phase 22. Phase 27 executes it, not creates it.
- **Waiting for sufficient volume before escalating:** At 5-10 emails/day to 1-2 known recipients on shared IPs with SPF+DKIM already verified, volume-based waiting is unnecessary. The 2 clean weeks since Phase 22 (Feb 17 to now) satisfy the monitoring period.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DNS verification | Custom DNS resolution library | `dig` CLI on EC2 | One-time use, standard tool, no dependencies |
| Domain DNS status | Parsing dig output | Resend `GET /domains/{id}` API for status + dig for propagation | API gives authoritative verification status directly |
| DMARC aggregate report parsing | XML parser for DMARC reports | Manual review of XML (or free DMARC viewer) | Deferred per CONTEXT.md. At 1-2 reports/day, manual is fine |
| Readiness gate calculation | Complex tracking database | Timestamp in email-config.json + simple date math | Single field solves the problem |
| Email health monitoring | New monitoring infrastructure | Existing morning briefing Section 9 + SQL queries | Already built in Phase 22 |

**Key insight:** Phase 27 is 90% execution of existing infrastructure and 10% configuration adjustment. Zero new tools, zero new databases, minimal code changes.

## Common Pitfalls

### Pitfall 1: DMARC Escalation Breaks Delivery to Forwarded Addresses

**What goes wrong:** After changing to p=quarantine, emails to recipients who forward email (e.g., AirSpace Google Workspace forwarding to personal Gmail) fail DMARC alignment because the forwarding server modifies headers.
**Why it happens:** SPF checks the sending server IP. When a forwarding server relays the email, SPF sees the forwarder's IP, not Resend's. If DKIM is intact, DMARC passes on DKIM alignment. But if the forwarder modifies the body or certain headers, DKIM breaks too.
**How to avoid:** Test to both Gmail and AirSpace email BEFORE escalation. If both show SPF PASS + DKIM PASS in "Show original," forwarding alignment is likely fine. After escalation, immediately retest both recipients. Resend uses Amazon SES which signs DKIM on the domain — DKIM generally survives forwarding.
**Warning signs:** AirSpace email receives test fine before DMARC change, then goes to spam after.
**Confidence:** HIGH (well-documented DMARC + forwarding interaction)

### Pitfall 2: RUA Address Not Receiving Reports

**What goes wrong:** rua tag is added to DMARC record but no aggregate reports arrive after 48 hours.
**Why it happens:** Three common causes: (1) rua address doesn't exist or can't receive email, (2) the domain in the rua `mailto:` is different from the DMARC record's domain and lacks an authorization DNS record, (3) volume is too low for any receiving server to generate a report.
**How to avoid:**
1. Verify the rua address can receive email before adding the rua tag.
2. If rua address is at a different domain than the DMARC record (e.g., DMARC on `mail.andykaufman.net` but rua at `dmarc@andykaufman.net`), this is a cross-domain rua. Per RFC 7489, the receiving domain must publish a DNS record: `mail.andykaufman.net._report._dmarc.andykaufman.net TXT "v=DMARC1"`. This authorizes `andykaufman.net` to receive DMARC reports for `mail.andykaufman.net`.
3. At 5-10 emails/day to 1-2 Gmail recipients, expect at most 1 report/day from Google. Reports may not arrive for 24-48 hours after record publication.
**Warning signs:** 48+ hours after DMARC change, no reports at rua address. Check DNS for the authorization record if cross-domain.
**Confidence:** HIGH (RFC 7489 section 7.1 requires cross-domain authorization)

### Pitfall 3: Morning Briefing Section Numbers Collide

**What goes wrong:** Phase 27 adds a new section to morning briefing, but the section number conflicts with the recently added Section 10 (Agent Observability from Phase 26).
**Why it happens:** The morning briefing has grown to 10 sections. Adding more requires careful numbering.
**How to avoid:** Phase 27 does NOT add a new section. It modifies the existing Section 9 (Email Health) to add the readiness gate and updated thresholds. Verify section numbering before and after modification.
**Warning signs:** Morning briefing output has duplicate section numbers or missing sections.
**Confidence:** HIGH (known from Phase 22 and 26 section additions)

### Pitfall 4: DMARC Policy Applies to Subdomain, Not Root

**What goes wrong:** The DMARC record is added/updated at `_dmarc.andykaufman.net` (root) instead of `_dmarc.mail.andykaufman.net` (subdomain). Policy doesn't apply to Bob's emails.
**Why it happens:** DMARC records are published at `_dmarc.<domain>`. For the subdomain `mail.andykaufman.net`, the record goes at `_dmarc.mail.andykaufman.net`. The root domain record applies only to root domain emails (and subdomains via the `sp=` tag if no subdomain-specific record exists).
**How to avoid:** Always verify: `dig TXT _dmarc.mail.andykaufman.net` (subdomain-specific). The Phase 19 setup already placed the record at the correct subdomain location.
**Warning signs:** `dig TXT _dmarc.mail.andykaufman.net` returns empty but `dig TXT _dmarc.andykaufman.net` returns a record.
**Confidence:** HIGH (Phase 19 research confirmed no parent DMARC exists)

### Pitfall 5: Two Clean Weeks Requirement vs "Already Clean" Ambiguity

**What goes wrong:** Debate about whether the 2 clean weeks started from Phase 22 completion (Feb 17) or requires fresh verification.
**Why it happens:** WARMUP.md Step 4 says "Monitor for 2 Weeks" and Step 5 says "After 2 Clean Weeks." Phase 22 was Feb 17 — that's only 2 days ago.
**How to avoid:** CONTEXT.md resolves this: "skip percentage ramp -- go straight to p=quarantine pct=100 (low volume, auth already configured via Resend SPF+DKIM)." The decision is to escalate now (since auth is already verified) without waiting for a full 2-week monitoring period. The 7-day readiness gate post-escalation replaces the 2-week pre-escalation wait.
**Warning signs:** Unnecessary delay waiting for a monitoring period that was already decided to be skipped.
**Confidence:** HIGH (CONTEXT.md explicitly overrides WARMUP.md's timeline)

## Code Examples

### Example 1: Complete WARMUP.md Step 1 (DNS Verification Script)

```bash
#!/bin/bash
# Run on EC2 to verify all DNS authentication records
echo "=== SPF Check ==="
dig TXT send.mail.andykaufman.net +short

echo ""
echo "=== DKIM Check (3 selectors) ==="
dig CNAME resend._domainkey.mail.andykaufman.net +short
dig CNAME resend2._domainkey.mail.andykaufman.net +short
dig CNAME resend3._domainkey.mail.andykaufman.net +short

echo ""
echo "=== DMARC Check ==="
dig TXT _dmarc.mail.andykaufman.net +short

echo ""
echo "=== MX Check ==="
dig MX send.mail.andykaufman.net +short

echo ""
echo "=== Domain Status via Resend API ==="
curl -s -X GET 'https://api.resend.com/domains' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data.get('data', []):
    if 'mail.andykaufman.net' in d.get('name', ''):
        print(f\"Domain: {d['name']}\")
        print(f\"Status: {d['status']}\")
        print(f\"Capabilities: sending={d.get('capabilities',{}).get('sending','?')}, receiving={d.get('capabilities',{}).get('receiving','?')}\")
"
```

### Example 2: Test Email for Inbox Placement (WARMUP Step 2-3)

```bash
# Send test email via Resend API from EC2
curl -s -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["theandykaufman@gmail.com"],
    "subject": "WARMUP Test - Inbox Placement Verification",
    "html": "<h2>Domain Warmup Test</h2><p>This is a test email to verify inbox placement for mail.andykaufman.net domain hardening (Phase 27).</p><p>Please check:<br>1. This arrived in INBOX (not spam)<br>2. Click Show Original → verify SPF: PASS, DKIM: PASS, DMARC: PASS<br>3. From name shows as Bob</p>"
  }'

# Repeat for AirSpace account
curl -s -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["kaufman@airspaceintegration.com"],
    "subject": "WARMUP Test - Inbox Placement Verification",
    "html": "<h2>Domain Warmup Test</h2><p>This is a test email to verify inbox placement for mail.andykaufman.net domain hardening (Phase 27).</p><p>Please check:<br>1. This arrived in INBOX (not spam)<br>2. Click Show Original → verify SPF: PASS, DKIM: PASS</p>"
  }'
```

### Example 3: Post-Escalation DMARC Verification

```bash
# After DNS update, verify propagation
dig TXT _dmarc.mail.andykaufman.net +short
# Expected: "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@andykaufman.net;"

# If cross-domain rua, verify authorization record exists
dig TXT mail.andykaufman.net._report._dmarc.andykaufman.net +short
# Expected: "v=DMARC1" (authorizes andykaufman.net to receive reports for mail.andykaufman.net)

# Send immediate test email and verify delivery
curl -s -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["theandykaufman@gmail.com"],
    "subject": "Post-DMARC Escalation Test",
    "html": "<p>Verifying inbox delivery after DMARC escalation to p=quarantine.</p>"
  }'
```

### Example 4: Readiness Gate in email-config.json

```json
{
  "recipients": [
    {"email": "theandykaufman@gmail.com", "name": "Andy"}
  ],
  "daily_send_count": 3,
  "daily_send_date": "2026-02-19",
  "alert_count_today": 0,
  "monthly_send_count": 45,
  "monthly_send_month": "2026-02",
  "sender_allowlist": [
    "theandykaufman@gmail.com",
    "kaufman@airspaceintegration.com"
  ],
  "dmarc_escalated_at": "2026-02-20T12:00:00Z",
  "dmarc_policy": "quarantine",
  "phase29_gate": {
    "requires_days": 7,
    "bounce_threshold_pct": 5,
    "complaint_threshold_pct": 0.1
  }
}
```

## Discretion Recommendations

### Dig Command Formatting and Verification

**Recommendation:** Use `+short` flag for concise output. Run all checks as a single script (Example 1 above) for easy copy-paste execution. Complement with Resend API `GET /domains/{id}` for authoritative verification status. The API check is especially useful because it shows per-record status (verified/not_started/pending) without parsing dig output.

### Resend API Metrics Polling

**Recommendation:** Do NOT add separate metrics polling. The existing infrastructure already captures everything needed:
- **Bounce/complaint rates:** Already tracked via webhook events → email.db → SQL queries in morning briefing Section 9
- **Delivery status:** Already tracked in `email_conversations.delivery_status` column
- **Volume stats:** Already calculated in Section 9 SQL queries

The Resend dashboard metrics page shows the same data visually but there is no documented programmatic API endpoint for fetching aggregated metrics. At current volume, the email.db SQL approach is more reliable (it captures every event via webhooks). No additional polling needed.

### Morning Briefing Section Placement

**Recommendation:** Modify existing Section 9 (Email Health Check) in place. Do NOT add a new section. The morning briefing already has 10 sections (1-8 from v2.0-v2.1, 9 from Phase 22, 10 from Phase 26). Changes to Section 9:
1. Update threshold levels (add CRITICAL tier at 5%/0.1%)
2. Add readiness gate status line after metrics
3. Keep existing WARNING tier at 2%/0.08% (Resend account protection)

### Test Email Content and Cadence

**Recommendation:** Send 2 test emails during warmup execution (one to personal Gmail, one to AirSpace). Send 1 more immediately after DMARC escalation. No ongoing test email cadence needed -- real email traffic (morning briefing, alerts, etc.) provides sufficient organic volume. If volume is truly insufficient for meaningful 7-day stats, add 1 daily test email for the 7-day gate period, but at current volume (5-10/day) this shouldn't be necessary.

### RUA Address Setup

**Recommendation:** Use `dmarc@andykaufman.net` as the rua address. Before adding the rua tag:
1. Verify the address can receive email (send a test from personal Gmail)
2. Set up a Gmail filter: from contains "noreply-dmarc-support" or subject contains "DMARC" → label "DMARC Reports", skip inbox
3. If using cross-domain rua (DMARC on `mail.andykaufman.net`, rua at `andykaufman.net`), add the DNS authorization record: `mail.andykaufman.net._report._dmarc.andykaufman.net TXT "v=DMARC1"`

Alternative: Use Andy's personal Gmail directly as rua (`theandykaufman@gmail.com`). Simpler (no cross-domain auth needed if DMARC record is on `mail.andykaufman.net` and rua points to a different domain), but clutters inbox. Filter recommended either way.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| p=none forever with manual review | Progressive enforcement: none → quarantine → reject | RFC 7489 (2015), widely adopted by 2023 | Industry standard. Google and Yahoo require DMARC for bulk senders since Feb 2024 |
| DMARC without rua (blind enforcement) | Always include rua for aggregate reports | Best practice since RFC 7489 | Can't diagnose failures without reports. rua is essential for enforcement confidence |
| Wait 30+ days before quarantine | Low-volume senders can escalate faster | Common guidance as of 2024 | At 5-10 emails/day to known recipients, shorter ramp is safe if authentication is clean |
| Dedicated IP warmup schedules | Shared IP senders skip formal warmup | Resend guidance (shared IPs pre-warmed) | Resend handles shared IP reputation. Sender just verifies authentication |

**Deprecated/outdated:**
- Waiting 30-60 days at p=none for low-volume senders: Only needed for high-volume senders (1000+/day) or those with complex sending infrastructure. At 5-10/day with verified SPF+DKIM, faster escalation is safe.
- Setting pct=10 → pct=25 → pct=50 → pct=100: Percentage ramp is for high-volume senders who need gradual rollout. At low volume, pct=100 from the start (per CONTEXT.md decision).

## Existing Infrastructure Inventory

Critical for planning: what already exists from Phase 22 and doesn't need to be rebuilt.

| Component | Location | Status | Phase 27 Action |
|-----------|----------|--------|-----------------|
| WARMUP.md | `/home/ubuntu/clawd/agents/main/WARMUP.md` | Deployed, Status: PENDING | Execute steps (not create) |
| SKILL.md Section 9 | `/home/ubuntu/.openclaw/skills/resend-email/SKILL.md` | Deployed, active | Adjust thresholds only |
| email-config.json | `/home/ubuntu/clawd/agents/main/email-config.json` | Has monthly counters | Add dmarc_escalated_at + gate config |
| Morning briefing Section 9 | `~/.openclaw/cron/jobs.json` (job ID: 863587f3-...) | Email Health active | Update thresholds, add gate status |
| email-catchup cron | `~/.openclaw/cron/jobs.json` (job ID: email-catchup) | Running at :15/:45 | No change needed |
| email.db | `/home/ubuntu/clawd/agents/main/email.db` | Active, webhook events flowing | No schema change needed |
| SPF/DKIM DNS records | DNS provider | Verified (Phase 19) | Verify still active (dig check) |
| DMARC DNS record | `_dmarc.mail.andykaufman.net` | `p=none` | Update to `p=quarantine; pct=100; rua=mailto:...` |

## Open Questions

1. **Does a `dmarc@andykaufman.net` mailbox exist?**
   - What we know: Andy uses Gmail for `theandykaufman@gmail.com` and Google Workspace for `kaufman@airspaceintegration.com`. The `andykaufman.net` domain is registered.
   - What's unclear: Whether `dmarc@andykaufman.net` is a valid receiving address, or if Andy needs to create it as a Gmail alias/forwarding address.
   - Recommendation: Verify during execution. If creating a dedicated address is cumbersome, use `theandykaufman@gmail.com` directly for rua (with a filter to organize reports).
   - Confidence: LOW (requires user input)

2. **Cross-domain DMARC RUA authorization record**
   - What we know: DMARC record is on `mail.andykaufman.net`. If rua points to an address at `andykaufman.net` (different domain), RFC 7489 Section 7.1 requires the receiving domain to publish `mail.andykaufman.net._report._dmarc.andykaufman.net TXT "v=DMARC1"`.
   - What's unclear: Whether `andykaufman.net` is considered a "different domain" from `mail.andykaufman.net` for DMARC report purposes (subdomain relationship). Most implementations DO require the authorization record for subdomain-to-parent reporting.
   - Recommendation: Add the authorization DNS record proactively. It's a single TXT record and ensures reports flow regardless of receiver implementation. If rua is at Gmail (external domain entirely), the authorization record goes at `mail.andykaufman.net._report._dmarc.gmail.com` -- which Andy cannot control. In that case, most large providers (Google, Microsoft) accept rua from any address without the authorization record as a practical exception.
   - Confidence: MEDIUM (RFC is clear, but real-world implementations vary)

3. **Has WARMUP.md been partially executed since Phase 22?**
   - What we know: Phase 22 created WARMUP.md on Feb 17. It's been 2 days. The status field was set to "PENDING."
   - What's unclear: Whether Andy or Bob have started working through the steps since then.
   - Recommendation: Check WARMUP.md status via SSH during execution. If steps are already partially complete, skip those and verify results.
   - Confidence: MEDIUM (planner should check status at execution time)

## Sources

### Primary (HIGH confidence)
- [Resend `GET /domains/{domain_id}`](https://resend.com/docs/api-reference/domains/get-domain) -- Domain detail with per-record DNS verification status (Context7 verified)
- [Resend `POST /domains/{domain_id}/verify`](https://resend.com/docs/api-reference/domains/verify-domain) -- Trigger async domain verification (Context7 verified)
- [Resend Webhook Events](https://resend.com/docs/webhooks/event-types) -- email.bounced, email.complained, email.delivered events (Context7 verified)
- [Resend Account Quotas](https://resend.com/docs/knowledge-base/account-quotas-and-limits) -- Bounce <4%, spam <0.08% (Context7 verified)
- [Resend DMARC Implementation](https://resend.com/docs/dashboard/domains/dmarc) -- Prerequisites (SPF+DKIM verified), implementation steps
- [Resend Domain Troubleshooting](https://resend.com/docs/knowledge-base/what-if-my-domain-is-not-verifying) -- DNS verification via nslookup/dig

### Secondary (MEDIUM confidence)
- [MXToolbox DMARC RUA Tag](https://mxtoolbox.com/dmarc/details/dmarc-tags/dmarc-rua) -- RUA format, multiple recipients, report delivery timing
- [Valimail DMARC Tags Guide](https://www.valimail.com/blog/dmarc-the-only-3-tags-you-really-need/) -- Only 3 required tags: v, p, rua
- [DMARCLY RUA Explained](https://dmarcly.com/blog/what-is-rua-in-dmarc-dmarc-rua-tag-explained) -- Aggregate report format (XML), delivery cadence (daily)
- [Resend DMARC Policy Modes](https://resend.com/blog/dmarc-policy-modes) -- none/quarantine/reject progression
- [Resend Domain Warmup Guide](https://resend.com/docs/knowledge-base/warming-up) -- Shared IP warmup handled by provider

### Tertiary (LOW confidence)
- Cross-domain DMARC RUA authorization -- RFC 7489 Section 7.1 is clear, but real-world enforcement varies across providers. Google typically accepts cross-domain rua without authorization records. Needs runtime verification.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All components exist from Phase 22. Zero new tools. Verified via codebase search and Phase 22 verification report.
- Architecture: HIGH -- Execution plan maps directly to existing WARMUP.md steps. DMARC escalation is a single DNS record change. Morning briefing modification follows proven Pattern from Phases 22 and 26.
- Pitfalls: HIGH -- Cross-domain rua authorization (Pitfall 2) is the highest-risk item. DMARC forwarding interaction (Pitfall 1) is standard and testable. All other pitfalls have documented mitigations.

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable domain -- DMARC RFC 7489, DNS standards, Resend API v1 all mature/stable)
