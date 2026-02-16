# Feature Landscape

**Domain:** Resend email integration for AI agent (OpenClaw/Bob)
**Researched:** 2026-02-16

## Table Stakes

Features users expect from an email-enabled AI agent. Missing = integration feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Send plain text + HTML email | Core capability. Agent must be able to compose and send emails | Low | Resend `emails.send()` with `html` and `text` params. Max 40MB per email after Base64 encoding |
| Domain verification (DNS) | Emails from unverified domains go to spam or get rejected | Low | Resend handles SPF/DKIM automatically. Add TXT + CNAME records. Use subdomain (e.g. `mail.yourdomain.com`) to protect root domain reputation |
| Webhook signature verification | Without it, anyone can POST fake inbound emails to your endpoint | Med | Resend uses Svix under the hood. Verify via `svix-id`, `svix-timestamp`, `svix-signature` headers with HMAC-SHA256. MUST use raw request body (not parsed JSON) |
| Inbound email receiving | Agent needs to receive emails, not just send them. Two-way communication is expected | Med | Requires MX record on receiving subdomain, webhook endpoint, then separate API calls to get body + attachments (webhook only delivers metadata) |
| Email delivery status tracking | Must know if emails bounced, failed, or were delivered | Low | Subscribe to webhook events: `email.sent`, `email.delivered`, `email.bounced`, `email.failed`. Log status to coordination DB |
| Reply threading (In-Reply-To) | Replies must appear in the same thread in recipient's email client, not as separate emails | Med | Set `In-Reply-To` header to original `Message-ID`, accumulate `References` header across conversation. Prefix subject with `Re:`. Resend supports custom headers in send API |
| API key management | Secure credential handling | Low | `RESEND_API_KEY` in `.env`, passed to sandbox via `openclaw.json` docker.env config. Key format: `re_` prefix |

## Differentiators

Features that elevate the agent beyond basic email. Not expected, but create real value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Morning briefing via email | Deliver daily briefing to email in addition to Slack. Reaches user even when not in Slack | Low | Reuse existing briefing content, wrap in HTML template, send via cron. Most impactful quick win |
| Inbound email command processing | Email Bob a question or instruction, get a response. "Forward this to Bob" workflow | High | Webhook receives email -> parse sender (allowlist check) -> extract intent -> agent processes -> reply via email. Needs sender verification, intent parsing, response formatting |
| Alert/notification emails | Critical alerts (security, health, anomalies) sent via email as backup channel to Slack | Low | Simple send on trigger. Tag with alert type. Could wake user up via phone email notifications when Slack is muted |
| Email-to-Slack bridging | Forward important inbound emails to Slack for visibility | Med | Inbound webhook -> parse -> format as Slack message -> post to channel. Useful for non-Slack participants contacting Bob |
| Scheduled email sends | Schedule emails up to 72 hours in advance | Low | Resend supports `scheduled_at` param (ISO 8601). Useful for "send this tomorrow morning" patterns |
| Conversation history tracking | Track full email threads in local DB for context | Med | Store message_id, in_reply_to, references, subject, from, to, body summary. Query for conversation context when composing replies |
| Batch email sends | Send up to 100 emails in single API call | Low | Resend batch endpoint. Note: batch does NOT support attachments or scheduling. Good for bulk notifications |
| Email templates (HTML) | Professional, consistent email formatting | Med | Could use React Email (Resend's companion project) or simple HTML templates. Agent-composed content wrapped in branded layout |
| Attachment sending | Send files (reports, screenshots, documents) via email | Low | Base64-encode content, include in `attachments` array. Max 40MB total. Useful for sending generated reports |
| Attachment receiving + processing | Process attachments from inbound emails | High | Webhook delivers attachment metadata only. Must call Attachments API to get `download_url`, then fetch content. Parse based on content_type. Memory/disk considerations in Docker sandbox |
| Email tagging and analytics | Tag outbound emails for tracking/categorization | Low | Resend tags (name/value, max 256 chars each). Tags included in webhook events. Track which email types get opened/clicked |

## Anti-Features

Features to explicitly NOT build. Restraint is a feature.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Marketing email campaigns | Bob is a personal assistant, not a marketing tool. Free tier is 3,000 emails/month (100/day). Marketing burns quota fast and risks spam complaints (must stay under 0.08%) | Use Resend strictly for transactional/personal communication. If marketing needed later, use separate service/domain |
| Auto-reply to all inbound emails | Responding to every email creates reply loops, spam amplification, and embarrassing auto-responses to newsletters/notifications | Strict allowlist of recognized senders. Ignore or silently log emails from unknown senders. Never auto-reply to noreply@ addresses |
| Open/click tracking on personal emails | Tracking pixels feel surveillance-y for personal assistant emails. Damages trust | Only enable `email.opened`/`email.clicked` webhooks for specific use cases (e.g. confirming a critical alert was seen), not blanket tracking |
| Email as primary communication channel | Email is slower, less interactive than Slack. Agent loses real-time conversation ability | Keep Slack as primary. Email is a supplementary channel for: (1) reaching non-Slack contexts, (2) delivering formatted reports, (3) processing inbound from external parties |
| Complex email routing/rules engine | Building a full email client with filters, folders, rules | Simple allowlist + intent detection. Route to agent or ignore. No need to replicate Gmail |
| Storing full email bodies long-term | Privacy concern, storage bloat, not needed for agent operation | Store metadata + summary only. Fetch full body on-demand from Resend API when needed for context |

## Feature Dependencies

```
Domain Verification -> Send Email (must verify domain before sending from it)
Domain Verification -> Receive Email (MX records on verified domain)
Webhook Endpoint -> Receive Email (need public endpoint for Resend to POST to)
Webhook Endpoint -> Delivery Status Tracking (same endpoint, different event types)
Webhook Signature Verification -> Webhook Endpoint (verify before processing any webhook)
Send Email -> Reply Threading (send is prerequisite, threading adds headers)
Receive Email -> Inbound Command Processing (must receive before processing)
Receive Email -> Email-to-Slack Bridge (must receive before forwarding)
Send Email -> Morning Briefing via Email (send is prerequisite)
Send Email -> Alert Notifications (send is prerequisite)
Reply Threading -> Conversation History (threading generates the data to track)
```

Key dependency chain: **Domain Verification -> Webhook Endpoint -> Send/Receive -> Everything Else**

## Resend-Specific Behavioral Notes

### Free Tier Constraints (CRITICAL)
- **100 emails/day, 3,000 emails/month** for transactional emails
- **Inbound emails count against quota** -- each received email = 1 email against daily/monthly limits
- **Multiple recipients count separately** -- CC/BCC each count as 1 email
- **Rate limit: 2 requests/second** for all accounts (can request increase)
- **1 domain per team** on free tier
- **Spam rate must stay under 0.08%** or sending gets paused
- Marketing emails: unlimited to up to 1,000 contacts/month (separate from transactional)

### Inbound Email Architecture (IMPORTANT)
Resend's inbound email design is intentionally two-step:
1. **Webhook delivers metadata only** -- from, to, subject, attachment metadata (id, filename, content_type). NO body, NO headers, NO attachment content
2. **You call the API for content** -- `Received Emails API` for body, `Attachments API` for files (returns `download_url`)

This is designed for serverless environments with request body size limits. It means your webhook handler must be async-capable (receive notification, then fetch content).

### Domain Setup for Receiving
- Resend provides a free `.resend.app` address automatically
- For custom domains: add MX record on a **subdomain** (NOT root domain) to avoid conflicts with existing email (e.g. Gmail)
- Toggle "Receiving" in Resend dashboard for the domain
- All emails to `*@subdomain.yourdomain.com` get received (catch-all)

### Webhook Events Available (17 total)
**Email events:** email.sent, email.delivered, email.delivery_delayed, email.bounced, email.complained, email.opened, email.clicked, email.failed, email.received, email.scheduled, email.suppressed
**Domain events:** domain.created, domain.updated, domain.deleted
**Contact events:** contact.created, contact.updated, contact.deleted

### Threading Mechanics
- Set `headers: { "In-Reply-To": "<original-message-id>" }` in send API
- Accumulate `References` header: append each message_id in the thread separated by spaces
- Gmail, Outlook, Apple Mail all respect In-Reply-To + References for conversation grouping
- Prefix subject with `Re:` if not already present

## MVP Recommendation

**Phase 1 -- Send capability (table stakes):**
1. Domain verification on a subdomain (e.g. `mail.yourdomain.com`)
2. Send email skill for Bob (plain text + HTML)
3. Morning briefing delivery via email (reuse existing content)
4. Alert/notification emails for critical events

**Phase 2 -- Receive capability (differentiator):**
5. Webhook endpoint (with Svix signature verification)
6. Inbound email processing (metadata -> fetch body -> parse)
7. Sender allowlist + basic intent routing
8. Email-to-Slack bridging for inbound

**Phase 3 -- Conversation capability (differentiator):**
9. Reply threading with In-Reply-To/References headers
10. Conversation history tracking in local DB
11. Inbound command processing (email Bob, get email response)

**Defer:**
- Attachment processing: High complexity, low initial value. Add when specific use case emerges
- Email templates (React Email): Nice-to-have. Start with simple HTML, formalize templates later
- Batch sends: Only relevant at scale. Free tier makes this nearly irrelevant
- Email analytics/tagging: Add organically as patterns emerge

**Rationale:** Sending is dramatically simpler than receiving. Sending delivers immediate value (briefings, alerts) with low risk. Receiving requires a public webhook endpoint (Tailscale-only EC2 complicates this significantly -- likely needs a lightweight proxy or Cloudflare Tunnel). Threading builds on both send and receive being stable.

## Infrastructure Consideration (CRITICAL)

The current EC2 setup is Tailscale-only with no public-facing ports. Resend inbound webhooks require a publicly accessible HTTPS endpoint. Options:
1. **Cloudflare Tunnel** -- expose just the webhook endpoint path publicly
2. **AWS API Gateway + Lambda** -- serverless webhook receiver, forward to EC2 via Tailscale
3. **ngrok/similar** -- quick but not production-grade
4. **Open a port in SG** -- violates the security model

This infrastructure question is the single biggest dependency for Phase 2 (receiving). Phase 1 (sending) works fine without any changes since it's outbound API calls only.

## Sources

- [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email) -- HIGH confidence
- [Resend Receiving Emails](https://resend.com/docs/dashboard/receiving/introduction) -- HIGH confidence
- [Resend Reply to Receiving Emails](https://resend.com/docs/dashboard/receiving/reply-to-emails) -- HIGH confidence
- [Resend Webhook Event Types](https://resend.com/docs/dashboard/webhooks/event-types) -- HIGH confidence
- [email.received webhook payload](https://resend.com/docs/webhooks/emails/received) -- HIGH confidence
- [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests) -- HIGH confidence
- [Resend DMARC Setup](https://resend.com/docs/dashboard/domains/dmarc) -- HIGH confidence
- [Resend Subdomain vs Root Domain](https://resend.com/docs/knowledge-base/is-it-better-to-send-emails-from-a-subdomain-or-the-root-domain) -- HIGH confidence
- [Resend MX Record Conflicts](https://resend.com/docs/knowledge-base/how-do-i-avoid-conflicting-with-my-mx-records) -- HIGH confidence
- [Resend Account Quotas](https://resend.com/docs/knowledge-base/account-quotas-and-limits) -- HIGH confidence
- [Resend Custom Receiving Domains](https://resend.com/docs/dashboard/receiving/custom-domains) -- HIGH confidence
- [Resend Batch Email API](https://resend.com/docs/api-reference/emails/send-batch-emails) -- HIGH confidence
- [Resend Schedule Email API](https://resend.com/blog/introducing-the-schedule-email-api) -- HIGH confidence
- [Resend Node.js SDK](https://github.com/resend/resend-node) -- HIGH confidence
- [Resend Inbound Emails Blog Post](https://resend.com/blog/inbound-emails) -- HIGH confidence
- [Svix Webhook Verification](https://docs.svix.com/receiving/verifying-payloads/how) -- HIGH confidence
- [Resend New Free Tier](https://resend.com/blog/new-free-tier) -- MEDIUM confidence (blog post, check for updates)
