# Phase 19: Outbound Email Foundation - Research

**Researched:** 2026-02-16
**Domain:** Resend REST API integration for outbound email from OpenClaw Docker sandbox
**Confidence:** HIGH

## Summary

This phase adds outbound email to Bob via a custom SKILL.md that wraps `curl` calls to the Resend REST API. The pattern is identical to Oura, Govee, and receipt-scanner integrations already deployed in this project: SKILL.md teaches Bob the API endpoints, env var provides auth, `exec` tool runs `curl` from the Docker sandbox. No npm packages, no MCP servers, no new binaries.

The main work is: (1) Resend account creation + domain DNS verification, (2) API key injection into sandbox env, (3) SKILL.md with send-email instructions + HTML template, (4) modifying the morning briefing cron to also send email, and (5) alert email logic in the skill instructions. The domain `mail.andykaufman.net` requires SPF (TXT), DKIM (3x CNAME), and optionally DMARC (TXT) DNS records. Resend generates the exact values after you add the domain in their dashboard.

**Primary recommendation:** Build a `resend-email` skill at `~/.openclaw/skills/resend-email/` with a SKILL.md that documents the `POST /emails` curl pattern, stores an HTML email template at `/workspace/email-template.html`, and adds a JSON config at `/workspace/email-config.json` for recipient list. Modify the morning briefing cron's systemEvent text to include an email-send step after the Slack message. Use `sending_access` API key scope in sandbox (least privilege).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Domain: `mail.andykaufman.net` (subdomain on personal domain, protects business MX)
- From address: `bob@mail.andykaufman.net`
- Display name: `Bob` (matches Slack agent name)
- Resend account under Andy's personal domain, not AirSpace
- Minimal HTML with Practical Typography principles (not branded, not plain text)
- Static HTML template stored in Bob's workspace (`/workspace/email-template.html`)
- Inline CSS for email client compatibility (Gmail strips `<style>` tags)
- Typography rules adapted for email: line-height 1.5, subtle heading hierarchy (h1: 1.5rem, h2: 1.35rem, h3: 1.15rem), heading spacing binds to content
- Unicode smart quotes, en/em dashes, proper ellipsis (not CSS -- actual characters)
- Properties that don't work in email (text-wrap, hanging-punctuation, font-kerning) are skipped
- Minimal footer: "Sent by Bob" or similar -- one line, subtle
- Briefing supplements Slack (both channels, same content)
- Same content as Slack, reformatted into HTML email template
- Piggybacks on existing morning briefing cron (generate content once, send to Slack then email)
- Configurable recipient list stored in workspace config file (start with theandykaufman@gmail.com)
- Alert triggers on important + critical events (failed crons, health anomalies, pipeline stalls, system-down, security)
- Bob's judgment decides when to escalate to email (skill instructions define what's email-worthy)
- No separate alert crons -- Bob sends email alerts from any session when warranted
- Soft cap: 5 alert emails per day (6th+ stays Slack-only, protects quota)
- Same recipient list as briefings (one config for all email)

### Claude's Discretion
- Email template HTML/CSS implementation details
- Exact alert threshold descriptions in skill instructions
- Config file format for recipient list (JSON, YAML, or plain text)
- Subject line conventions for briefings vs alerts

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| Resend REST API | v1 | Send email via HTTPS | Direct HTTP calls via `curl`, no SDK needed, works in read-only Docker sandbox |
| `curl` | (in sandbox) | HTTP client | Already available in sandbox image, zero setup |
| Custom SKILL.md | n/a | Teach Bob Resend API patterns | Proven pattern: Oura, Govee, receipt-scanner, ClawdStrike all use this |

### Supporting

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| `jq` | (in sandbox) | Parse JSON responses | Extract email ID from send response for logging |
| Resend Dashboard | n/a | Domain setup, DNS record generation, API key creation | One-time manual setup |
| DNS provider (andykaufman.net) | n/a | Add SPF/DKIM/DMARC records | One-time manual setup |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| curl + SKILL.md | resend-mcp (MCP server) | OpenClaw silently ignores `mcpServers` config. mcporter workaround adds ~2.4s cold-start. Direct curl is faster and proven |
| curl + SKILL.md | Resend Node.js SDK | Sandbox FS is read-only, `npm install` fails. npx adds cold-start overhead. REST API is trivial for send-only |
| JSON config file | SQLite table for recipients | Overkill for a 1-3 person recipient list. JSON is simpler, editable, and readable |
| JSON config file | Plain text (one email per line) | JSON allows future expansion (per-recipient preferences, name field) without format change |

**Installation:** No packages to install. `curl` is already in the sandbox. Only needs:
1. Resend account + API key (manual, web dashboard)
2. DNS records on `mail.andykaufman.net` (manual, DNS provider)
3. `RESEND_API_KEY` in `.env` + `openclaw.json` sandbox env
4. SKILL.md + template + config deployed to EC2

## Architecture Patterns

### Recommended File Structure

```
~/.openclaw/skills/resend-email/
  SKILL.md                          # Skill instructions (send email, briefing, alerts)

~/clawd/agents/main/                # Bob's workspace (= /workspace/ in sandbox)
  email-template.html               # Static HTML email template
  email-config.json                 # Recipient list + preferences
```

### Pattern 1: Send Email via curl

**What:** Bob constructs a curl command to POST to Resend's `/emails` endpoint with JSON body.
**When to use:** Every outbound email.
**Example:**

```bash
# Source: https://resend.com/docs/api-reference/emails/send-email (Context7 verified)
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer '"$RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["theandykaufman@gmail.com"],
    "subject": "Morning Briefing - Feb 16",
    "html": "<html>...</html>",
    "text": "Plain text fallback...",
    "headers": {
      "Auto-Submitted": "auto-generated"
    }
  }'
```

**Response (200):**
```json
{
  "id": "email_id_12345"
}
```

**Key fields in request body:**
- `from` (string, required): `"Bob <bob@mail.andykaufman.net>"`
- `to` (string[], required): recipient array, max 50
- `subject` (string, required): email subject line
- `html` (string, optional): HTML body
- `text` (string, optional): plain text body (auto-generated from HTML if omitted)
- `headers` (object, optional): custom email headers -- use for `Auto-Submitted`
- `reply_to` (string, optional): reply-to address
- `tags` (array, optional): `[{"name": "type", "value": "briefing"}]`
- `scheduled_at` (string, optional): ISO 8601 for future delivery (up to 72h)

### Pattern 2: HTML Email Template with Inline CSS

**What:** Static HTML file in workspace that Bob reads, injects content into, and sends.
**When to use:** All formatted emails (briefings, alerts).
**Rationale:** Gmail strips `<style>` tags. Inline CSS is the only reliable approach. Template stored in workspace so Bob can read it with file tools.

**Template design principles (from Practical Typography + email compatibility):**
- Body font: system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`)
- Body font-size: 16px (Practical Typography recommends 15-25px for screen)
- Line-height: 1.5 (Practical Typography: 120-145% of point size)
- Line length: constrained by `max-width: 600px` on container (standard email width, ~45-90 chars)
- Headings: subtle hierarchy -- h1: 1.5rem, h2: 1.35rem, h3: 1.15rem (user-specified)
- Heading spacing: more top margin, less bottom (binds heading to its content)
- Blockquotes: 0.95em font-size, 1.5rem left padding (user-specified)
- Smart typography: use actual Unicode characters -- curly quotes (\u201C \u201D \u2018 \u2019), en dash (\u2013), em dash (\u2014), ellipsis (\u2026)
- Layout: single-column, no tables needed for simple content flow
- Footer: "Sent by Bob" -- one line, subtle, smaller font, muted color
- No images, no tracking pixels, no marketing elements

**Email client compatibility notes:**
- Gmail: strips `<style>` tags, supports inline styles. Clips emails over 102KB.
- Outlook (new web-based): improving CSS support as Microsoft transitions from Word rendering engine (2025-2026)
- Apple Mail: best CSS support, most permissive
- Mobile: responsive via `max-width` on container (not media queries in `<style>`)

### Pattern 3: Config File for Recipients

**What:** JSON file in workspace with recipient list and email preferences.
**When to use:** Every email send -- Bob reads this file to determine recipients.

**Recommended format (JSON):**
```json
{
  "recipients": [
    {
      "email": "theandykaufman@gmail.com",
      "name": "Andy"
    }
  ],
  "daily_send_count": 0,
  "daily_send_date": "2026-02-16",
  "alert_count_today": 0
}
```

**Why JSON over plain text:** Supports the daily send counter for the soft cap (5 alerts/day), extensible for future per-recipient preferences, and Bob can read/write JSON natively with `jq` or `python3`.

**Why JSON over YAML:** JSON is universally parseable with `jq` (already in sandbox), no YAML parser needed.

### Pattern 4: Briefing Email Cron Integration

**What:** Modify existing morning-briefing systemEvent to add email send step after Slack delivery.
**When to use:** The morning-briefing cron (ID: `863587f3-bb4e-409b-aee2-11fe2373e6e0`, 7 AM PT daily).

**Approach:** Add a new section to the systemEvent text:

```
## 6. Email Briefing (BR-07)
After composing the briefing for Slack, also send it via email:
1. Read /workspace/email-config.json for recipient list
2. Read /workspace/email-template.html for the HTML template
3. Reformat the briefing content into the HTML template (replace placeholder)
4. Send via Resend API using the resend-email skill
5. Subject line format: "Morning Briefing - Mon Feb 16"
6. Include Auto-Submitted: auto-generated header
7. If email send fails, note the error but don't block the Slack briefing
```

**Key constraint:** The morning briefing cron uses `sessionTarget: "main"` with `payload.kind: "systemEvent"`. The email send happens within the same session -- no separate cron needed.

**Alternative considered:** Separate email-briefing cron 5 min after Slack briefing. Rejected because: (1) duplicates content generation work, (2) adds cron management complexity, (3) user explicitly chose "piggyback on existing cron."

### Pattern 5: Alert Email from Any Session

**What:** Bob decides in-session whether an event warrants email escalation, using skill instructions as guidance.
**When to use:** Any session where Bob encounters a critical event (heartbeat health check, cron failure notification, security alert).

**Flow:**
1. Bob encounters critical event in any session
2. Bob consults resend-email skill instructions for "email-worthy" criteria
3. Bob reads `/workspace/email-config.json` -- checks `alert_count_today` against soft cap (5)
4. If under cap: send alert email with descriptive subject, increment counter
5. If at/over cap: stay Slack-only, mention "email cap reached" in Slack message
6. Reset `alert_count_today` to 0 at start of morning briefing (daily reset)

### Anti-Patterns to Avoid

- **Using MCP server for Resend:** OpenClaw ignores `mcpServers` config. Wastes debugging time.
- **Sending test emails to real recipients during development:** Use Resend's built-in test addresses or send only to yourself.
- **Storing HTML in SKILL.md:** Template belongs in workspace (readable/editable by Bob), not in the skill instructions.
- **Building a complex email queue:** Overkill for 5-10 emails/day. Direct send is fine.
- **Omitting `Auto-Submitted: auto-generated` header:** Other bots may reply to Bob's emails, creating loops. This header prevents that (RFC 3834).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email sending | SMTP client, nodemailer | Resend REST API + curl | Deliverability (SPF/DKIM), free tier, 1 API call |
| Email authentication | Manual DKIM signing | Resend's automatic SPF/DKIM | Resend handles signing; you just add DNS records |
| HTML email rendering | Custom template engine | Static HTML file with placeholder | Bob can string-replace content into template; no engine needed |
| Daily send tracking | SQLite table | JSON counter in config file | 1-3 recipients, <10 emails/day. File counter is sufficient |
| CSS inlining | juice/premailer | Write inline CSS directly | Template is small, static, hand-authored once. No build step |

**Key insight:** This is a 5-10 email/day personal assistant, not a marketing platform. Every piece of infrastructure beyond "curl a REST API" is over-engineering.

## Common Pitfalls

### Pitfall 1: DMARC Inheritance from Parent Domain

**What goes wrong:** Parent domain `andykaufman.net` may have a strict DMARC policy (`p=reject` or `p=quarantine`) that `mail.andykaufman.net` inherits. Emails from Bob silently go to spam or get rejected.
**Why it happens:** DMARC `sp=` tag (subdomain policy) or inherited `p=` tag applies to all subdomains without their own DMARC record.
**How to avoid:**
1. Before adding Resend domain, check: `dig TXT _dmarc.andykaufman.net`
2. Look for `p=` and `sp=` values
3. If strict, publish subdomain DMARC: `_dmarc.mail.andykaufman.net` with `v=DMARC1; p=none;` during initial testing
4. After confirmed delivery, optionally tighten to `p=quarantine`
**Warning signs:** Resend dashboard shows "sent" but recipient never sees email. Check Gmail "Show original" for DMARC pass/fail.
**Confidence:** HIGH (Resend blog post confirms inheritance behavior)

### Pitfall 2: Domain Not Warmed Up

**What goes wrong:** Bob starts sending 10+ emails/day from a brand-new subdomain. Gmail and Outlook flag everything as spam.
**Why it happens:** New domains have zero sending reputation. Email providers treat unknown senders as suspicious.
**How to avoid:**
- Week 1: Send only to your own Gmail (theandykaufman@gmail.com). Max 2-3/day.
- Week 2: Increase to 5-10/day. Still own addresses only.
- Week 3+: Reach target volume.
- Verify SPF/DKIM/DMARC pass before first send.
- Check spam folder after first few sends.
**Warning signs:** Emails arriving in spam folder. Resend dashboard showing delivered but no opens.
**Confidence:** HIGH (Resend blog: "How to Warm Up a New Domain")

### Pitfall 3: Free Tier Daily Limit is 100

**What goes wrong:** Alert email storm (5 rapid alerts) + briefings + test sends eat into the 100/day cap unexpectedly.
**Why it happens:** The daily limit is 100 emails/day on free tier, and each recipient counts separately (CC/BCC each count as 1).
**How to avoid:**
- Track daily send count in `email-config.json`
- Soft cap of 5 alert emails/day (user decision)
- Design around ~20 emails/day max realistic usage (huge buffer)
- Rate limit: 2 requests/second for all Resend accounts
**Warning signs:** Resend returns error when limit hit. Monitor for non-200 responses.
**Confidence:** HIGH (Resend pricing page + quotas documentation)

### Pitfall 4: Gmail Clips Emails Over 102KB

**What goes wrong:** Morning briefing HTML is too large. Gmail shows "View entire message" link, cutting off content.
**Why it happens:** Gmail clips emails that exceed 102KB in rendered size (HTML + inline CSS).
**How to avoid:**
- Keep template minimal (no heavy CSS frameworks)
- Briefing content is text-heavy, not image-heavy -- naturally compact
- If concerned, measure: the briefing Slack message is typically <5KB of text. Wrapped in minimal HTML template, unlikely to approach 102KB.
**Warning signs:** Gmail shows "[Message clipped]" at bottom of email.
**Confidence:** HIGH (Well-documented Gmail behavior)

### Pitfall 5: Env Var Not Reaching Sandbox

**What goes wrong:** `RESEND_API_KEY` is in `.env` but Bob's curl commands fail with 401 Unauthorized.
**Why it happens:** `.env` is loaded by the gateway service only. To pass env vars INTO the sandbox, they must also be in `agents.defaults.sandbox.docker.env` in `openclaw.json`.
**How to avoid:** Add to BOTH locations:
1. `~/.openclaw/.env` (for gateway-level access)
2. `openclaw.json` `agents.defaults.sandbox.docker.env.RESEND_API_KEY` (for sandbox access)
3. Restart gateway after changes
4. Verify: Bob can run `echo $RESEND_API_KEY` and see the value
**Warning signs:** 401 or "missing API key" errors from Resend API.
**Confidence:** HIGH (Confirmed in project's own Phase 2/4 learnings)

### Pitfall 6: SKILL.md Missing YAML Frontmatter

**What goes wrong:** Skill created but `openclaw skills list` doesn't show it.
**Why it happens:** OpenClaw requires YAML frontmatter with `name` and `description` fields. Without it, the skill is not detected.
**How to avoid:** Always include frontmatter:
```yaml
---
name: Resend Email
description: Send emails via Resend REST API
---
```
**Warning signs:** Skill directory exists but not in `openclaw skills list`.
**Confidence:** HIGH (Confirmed in Oura skill deployment -- Phase 2)

## Code Examples

### Example 1: Send a Briefing Email (curl)

```bash
# Source: https://resend.com/docs/api-reference/emails/send-email (Context7)
# Bob runs this via exec tool from sandbox

curl -s -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["theandykaufman@gmail.com"],
    "subject": "Morning Briefing \u2014 Mon Feb 16",
    "html": "<html><body style=\"font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.5; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;\"><h1 style=\"font-size: 1.5rem; margin-top: 1.5rem; margin-bottom: 0.5rem;\">Morning Briefing</h1><p>Content here...</p><p style=\"font-size: 0.85rem; color: #999; margin-top: 2rem;\">Sent by Bob</p></body></html>",
    "text": "Morning Briefing\n\nContent here...\n\n---\nSent by Bob",
    "headers": {
      "Auto-Submitted": "auto-generated"
    },
    "tags": [
      {"name": "type", "value": "briefing"}
    ]
  }'
```

### Example 2: Send an Alert Email (curl)

```bash
curl -s -X POST 'https://api.resend.com/emails' \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "Bob <bob@mail.andykaufman.net>",
    "to": ["theandykaufman@gmail.com"],
    "subject": "[Alert] Gateway Health Check Failed",
    "html": "<html><body style=\"font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.5; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;\"><h1 style=\"font-size: 1.5rem; color: #c0392b; margin-bottom: 0.5rem;\">Alert: Gateway Health Check Failed</h1><p>Details here...</p><p style=\"font-size: 0.85rem; color: #999; margin-top: 2rem;\">Sent by Bob</p></body></html>",
    "text": "ALERT: Gateway Health Check Failed\n\nDetails here...\n\n---\nSent by Bob",
    "headers": {
      "Auto-Submitted": "auto-generated"
    },
    "tags": [
      {"name": "type", "value": "alert"}
    ]
  }'
```

### Example 3: HTML Email Template Structure

```html
<!-- /workspace/email-template.html -->
<!-- Bob reads this, replaces {{SUBJECT}}, {{CONTENT}}, {{DATE}} -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.5; color: #333333; max-width: 600px; margin: 0 auto; padding: 24px 16px;">

  <h1 style="font-size: 1.5rem; font-weight: 600; color: #111111; margin-top: 0; margin-bottom: 1rem;">{{SUBJECT}}</h1>

  {{CONTENT}}

  <p style="font-size: 0.8rem; color: #999999; margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #eeeeee;">Sent by Bob</p>

</body>
</html>
```

**Content section HTML patterns for inside the template:**

```html
<!-- Section heading (h2) -->
<h2 style="font-size: 1.35rem; font-weight: 600; color: #222222; margin-top: 1.75rem; margin-bottom: 0.4rem;">Calendar</h2>

<!-- Sub-heading (h3) -->
<h3 style="font-size: 1.15rem; font-weight: 600; color: #333333; margin-top: 1.25rem; margin-bottom: 0.3rem;">9:00 AM \u2014 Team Standup</h3>

<!-- Paragraph -->
<p style="margin-top: 0; margin-bottom: 0.75rem;">Normal paragraph text goes here.</p>

<!-- Blockquote -->
<blockquote style="font-size: 0.95em; padding-left: 1.5rem; margin-left: 0; margin-right: 0; border-left: 3px solid #dddddd; color: #555555;">Quoted or emphasized text</blockquote>

<!-- Unordered list -->
<ul style="padding-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.75rem;">
  <li style="margin-bottom: 0.3rem;">List item one</li>
  <li style="margin-bottom: 0.3rem;">List item two</li>
</ul>

<!-- Bold/emphasis inline -->
<strong>Bold text</strong>
<em>Italic text</em>

<!-- Horizontal rule (section divider) -->
<hr style="border: none; border-top: 1px solid #eeeeee; margin: 1.5rem 0;">
```

### Example 4: Email Config JSON

```json
{
  "recipients": [
    {
      "email": "theandykaufman@gmail.com",
      "name": "Andy"
    }
  ],
  "daily_send_count": 0,
  "daily_send_date": "2026-02-16",
  "alert_count_today": 0
}
```

### Example 5: DNS Records to Add (Illustrative)

After adding `mail.andykaufman.net` in Resend dashboard, Resend generates:

| Record | Type | Name | Value (Resend-generated) |
|--------|------|------|--------------------------|
| SPF | TXT | `send.mail.andykaufman.net` | `v=spf1 include:amazonses.com ~all` |
| DKIM 1 | CNAME | `<hash1>._domainkey.mail.andykaufman.net` | `<hash1>.dkim.amazonses.com.` |
| DKIM 2 | CNAME | `<hash2>._domainkey.mail.andykaufman.net` | `<hash2>.dkim.amazonses.com.` |
| DKIM 3 | CNAME | `<hash3>._domainkey.mail.andykaufman.net` | `<hash3>.dkim.amazonses.com.` |
| DMARC | TXT | `_dmarc.mail.andykaufman.net` | `v=DMARC1; p=none;` |

**Notes:**
- SPF name includes `send.` prefix (Resend's default return-path subdomain)
- DKIM hashes are unique per domain -- copy exact values from Resend dashboard
- DMARC is optional but recommended. Start with `p=none` for monitoring, tighten later
- Exact values come from Resend dashboard after domain creation. The above are structural patterns only

## Discretion Recommendations

### Email Template HTML/CSS

**Recommendation:** Use the template structure shown in Code Example 3 above. Key decisions:

- **Font stack:** System fonts (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`). No custom fonts -- Gmail has the worst custom font support of any major email client.
- **Container:** `max-width: 600px; margin: 0 auto; padding: 24px 16px`. Standard email width, auto-centers, comfortable padding.
- **Colors:** `#333333` body text, `#111111` for h1, `#222222` for h2, `#333333` for h3, `#999999` for footer. Subtle hierarchy without heavy contrast jumps.
- **No dark mode support:** Would require `<style>` block with `prefers-color-scheme` media query, which Gmail strips. Accept light mode only.

### Alert Threshold Descriptions

**Recommendation:** Define these categories in the SKILL.md:

| Category | Email-Worthy | Examples |
|----------|-------------|----------|
| Critical | Always email | Gateway down, Tailscale disconnected, OOM, security breach detected |
| Important | Email if business hours (7 AM - 10 PM PT) | Cron job failed 2+ times consecutively, health anomaly (sleep <50, HRV spike), disk >85% |
| Informational | Slack only, never email | Single cron failure (transient), weather alert, routine status updates |

The skill instructions should explicitly list these categories so Bob has clear criteria. Bob's judgment fills edge cases, but the categories prevent both under-alerting and alert fatigue.

### Config File Format

**Recommendation:** JSON. See Example 4 above. Rationale:
- `jq` is available in sandbox for parsing
- `python3` can read/write it natively
- Extensible (add per-recipient preferences later without format change)
- Human-readable and hand-editable via SSH if needed

### Subject Line Conventions

**Recommendation:**

| Type | Format | Example |
|------|--------|---------|
| Morning briefing | `Morning Briefing \u2014 {Day Mon DD}` | `Morning Briefing \u2014 Mon Feb 16` |
| Evening recap | `Evening Recap \u2014 {Day Mon DD}` | `Evening Recap \u2014 Mon Feb 16` |
| Weekly review | `Weekly Review \u2014 Week of {Mon DD}` | `Weekly Review \u2014 Week of Feb 10` |
| Alert (critical) | `[Alert] {Brief description}` | `[Alert] Gateway Health Check Failed` |
| Alert (important) | `[Notice] {Brief description}` | `[Notice] 3 Cron Jobs Failed Today` |
| General | `{Descriptive subject}` | `Your Meeting Prep for 2:00 PM` |

Em dash (\u2014) used in briefing subjects for visual separation (Practical Typography). Square brackets for alerts for at-a-glance scanning in inbox.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `<style>` blocks in email | Inline CSS | Always (for Gmail) | Gmail strips `<style>` tags. Inline only |
| Table-based email layout | Div-based for simple content | 2024-2025 | Simple single-column emails work fine with divs. Tables still needed for multi-column |
| Custom fonts in email | System font stacks | Always | Gmail breaks custom fonts, even Google Fonts |
| SMTP with nodemailer | REST API (Resend, Postmark, etc.) | 2023+ | Managed deliverability, no SMTP config, built-in SPF/DKIM |
| Full MCP server integration | Custom SKILL.md + curl | Current (OpenClaw limitation) | OpenClaw ignores mcpServers config. Direct REST is the proven pattern |

**Deprecated/outdated:**
- `resend-mcp` via `mcpServers` config: OpenClaw ignores this. Use custom skill instead.
- `text-wrap: balance`: CSS property not supported in any email client. Skip entirely.
- `font-kerning`, `hanging-punctuation`: Not supported in email clients. Skip.

## Open Questions

1. **Existing DMARC on andykaufman.net?**
   - What we know: Need to check before adding subdomain
   - What's unclear: Whether parent domain has strict DMARC that would block subdomain sends
   - Recommendation: Run `dig TXT _dmarc.andykaufman.net` during Plan 1 execution. If strict, add subdomain DMARC override

2. **Existing SPF on andykaufman.net?**
   - What we know: Parent domain likely has SPF for existing email (Gmail/Workspace)
   - What's unclear: Whether `mail.` subdomain inherits parent SPF or needs its own
   - Recommendation: Resend's SPF record goes on `send.mail.andykaufman.net` (not root), so no conflict expected. Verify during setup

3. **Morning briefing cron timeout**
   - What we know: Currently 120s timeout for 5-section briefing
   - What's unclear: Whether adding email send (API call + template formatting) will exceed timeout
   - Recommendation: Email send is a single curl call (~1-2s). Template formatting is string replacement (~instant). 120s should be sufficient. Monitor first few runs

4. **`jq` availability in sandbox**
   - What we know: `curl` is confirmed in sandbox. `jq` status unconfirmed
   - What's unclear: Whether `jq` is installed in the Docker sandbox image
   - Recommendation: Test during implementation. If not available, use `python3 -c "import json..."` as fallback for JSON parsing

## Sources

### Primary (HIGH confidence)
- [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email) -- Full parameter reference, curl examples (Context7 verified)
- [Resend Custom Headers](https://resend.com/docs/dashboard/emails/custom-headers) -- `headers` field in JSON body, curl example with custom headers (Context7 verified)
- [Resend Managing Domains](https://resend.com/docs/dashboard/domains/introduction) -- SPF, DKIM setup, subdomain recommendation (Context7 verified)
- [Resend Domain API - Create Domain](https://resend.com/docs/api-reference/domains/create-domain) -- DNS record structure: SPF TXT, DKIM CNAME format (Context7 verified)
- [Resend Account Quotas](https://resend.com/docs/knowledge-base/account-quotas-and-limits) -- Free tier: 100/day, 3000/month, 2 req/s
- [Resend API Key Permissions](https://resend.com/docs/api-reference/api-keys/create-api-key) -- `full_access` vs `sending_access` scopes
- [Resend DMARC for Subdomains](https://resend.com/blog/how-dmarc-applies-to-subdomains) -- Inheritance rules, `sp=` tag behavior
- [Resend Domain Warmup](https://resend.com/blog/how-to-warm-up-a-new-domain) -- 30-60 day warmup schedule
- [Resend curl Example](https://github.com/resend/resend-curl-example) -- Official curl example repo
- [Practical Typography - Line Spacing](https://practicaltypography.com/line-spacing.html) -- 120-145% line spacing
- [Practical Typography - Point Size](https://practicaltypography.com/point-size.html) -- 15-25px for web body text
- [Practical Typography - Headings](https://practicaltypography.com/headings.html) -- Subtle hierarchy, bind to content
- [Gmail CSS Support](https://developers.google.com/workspace/gmail/design/css) -- Official Gmail CSS compatibility

### Secondary (MEDIUM confidence)
- [HTML and CSS in Emails 2026](https://designmodo.com/html-css-emails/) -- Current email client CSS compatibility landscape
- [RFC 3834](https://datatracker.ietf.org/doc/html/rfc3834) -- Auto-Submitted header standard for preventing bot loops

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Resend REST API is official, well-documented. Custom skill pattern proven in 4+ existing integrations in this project.
- Architecture: HIGH -- All patterns (curl from sandbox, env var injection, SKILL.md, cron modification) are established and documented in project history. No new architectural concepts.
- Pitfalls: HIGH -- DMARC inheritance, warmup, and daily limit confirmed by Resend official sources. Env var and frontmatter pitfalls confirmed by project's own Phase 2/4 experience.

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable domain -- Resend API v1, email standards don't change fast)
