# Domain Pitfalls

**Domain:** Resend email integration with OpenClaw AI agent system
**Researched:** 2026-02-16

## Critical Pitfalls

Mistakes that cause rewrites, lost emails, or security incidents.

### Pitfall 1: MX Record on Root Domain Nukes Existing Email

**What goes wrong:** Adding Resend's MX record to the root domain instead of a subdomain causes Resend to intercept ALL inbound email for the domain. Existing email (Gmail, Google Workspace, etc.) stops working because mail servers deliver to the lowest-priority MX record.
**Why it happens:** Resend docs show "add this MX record" without emphasizing that it MUST be on a subdomain if you have existing email. Easy to add to root domain by mistake.
**Consequences:** All incoming email to the main domain goes to Resend instead of your real mailbox. You don't notice until someone says "I emailed you 3 days ago."
**Prevention:**
- ALWAYS use a subdomain for Resend receiving (e.g., `mail.yourdomain.com` or `bot.yourdomain.com`)
- Verify existing MX records with `dig MX yourdomain.com` BEFORE adding anything
- The sending domain and receiving domain can be different subdomains if needed
- Test with `dig MX subdomain.yourdomain.com` after adding to confirm only Resend's MX appears there
**Detection:** Send a test email to the root domain address. If it doesn't arrive in your normal inbox, the MX is wrong.
**Confidence:** HIGH (Resend official docs confirm this behavior)

### Pitfall 2: DMARC Subdomain Policy Inheritance Blocks Sending

**What goes wrong:** The parent domain has a strict DMARC policy (`p=reject` or `p=quarantine`) that the subdomain inherits, causing all Resend-sent emails to be rejected or quarantined by receiving mail servers.
**Why it happens:** DMARC inheritance rules are counterintuitive. If the parent domain has `p=reject` and no `sp=` tag, subdomains inherit `p=reject`. If the parent has `sp=quarantine`, ALL subdomains without their own DMARC record get quarantined. Most people don't check their parent domain's DMARC before setting up the subdomain.
**Consequences:** Emails sent from `bob@mail.yourdomain.com` silently land in spam or get rejected. You think the integration works because the API returns 200, but recipients never see the emails.
**Prevention:**
- Check parent domain DMARC: `dig TXT _dmarc.yourdomain.com`
- Look for `sp=` tag -- this is what your subdomain inherits
- If parent has strict policy, publish a separate DMARC record on the subdomain: `_dmarc.mail.yourdomain.com` with `p=none` during testing
- Verify DKIM alignment: Resend signs with DKIM on your sending domain, which should pass DKIM alignment even with strict DMARC -- but verify
- SPF alignment may fail because Resend's return-path uses their own subdomain, not yours -- rely on DKIM alignment instead
**Detection:** Send test emails to Gmail, check "Show original" in Gmail to see DMARC pass/fail. Check Resend dashboard for bounce/complaint events.
**Confidence:** HIGH (Resend blog post "How DMARC Applies to Subdomains" confirms inheritance behavior)

### Pitfall 3: Agent Email Loop -- Bob Replies to Auto-Replies Forever

**What goes wrong:** Bob receives an out-of-office auto-reply, treats it as a real email requiring response, sends a reply, which triggers another auto-reply, creating an infinite loop that burns through the entire 100/day free tier quota in minutes.
**Why it happens:** The agent has no built-in awareness of auto-reply headers. LLMs see text that looks like it needs a response ("Thanks for your email, I'm out of the office...") and generate a reply. Without explicit header checking, every auto-reply looks like a real email.
**Consequences:** 100 daily email quota exhausted within minutes. Recipient's mailbox flooded. Possible Resend account suspension. Reputation damage to sending domain.
**Prevention:**
- **Before processing ANY inbound email**, check these headers via the Received Emails API:
  - `Auto-Submitted: auto-replied` or `auto-generated` (RFC 3834)
  - `X-Auto-Response-Suppress: All` or `OOF` (Microsoft/Exchange)
  - `Precedence: bulk` or `auto_reply` or `junk`
  - `X-Autoreply: yes`
  - `X-Autorespond` (any value)
- Build a suppression list: if Bob has already replied to address X in the last hour, don't reply again
- Rate limit outbound replies: max 1 reply per unique sender per hour
- Hard cap: if Bob has sent more than 10 emails in 5 minutes, halt all sending and alert
- Add `Auto-Submitted: auto-generated` header to ALL emails Bob sends, so OTHER bots don't reply to Bob
- Build the header-check into the n8n webhook processing workflow, NOT just the agent skill -- defense in depth
**Detection:** Monitor daily send count. If it spikes above 20 in an hour, something is looping.
**Confidence:** HIGH (RFC 3834 is the standard; auto-reply loops are the #1 documented email bot failure mode)

### Pitfall 4: Webhook Body is Metadata-Only -- Agent Gets No Email Content

**What goes wrong:** The n8n webhook receives the Resend inbound email notification, forwards it to the agent, and the agent tries to process the email -- but the webhook payload contains NO email body, NO headers, and NO attachments. Only metadata (from, to, subject, email ID).
**Why it happens:** Resend intentionally excludes email body from webhooks "to support large attachments in serverless environments." This is documented but easy to miss because every other email service (SendGrid, Postmark) includes the body in the webhook.
**Consequences:** Agent receives emails it cannot read. It either crashes, hallucinates content based on the subject line, or silently drops every inbound email.
**Prevention:**
- The n8n workflow MUST make a second API call to `GET /emails/{id}` (Received Emails API) to fetch the actual email body
- For attachments, a third call to the Attachments API is needed to get download URLs
- Design the n8n workflow as: webhook trigger --> HTTP Request node (fetch body) --> forward complete email to agent
- The Resend API key used by n8n needs `full_access` scope (not just `sending_access`) to call the Received Emails API
- Cache the email body in the n8n payload before forwarding -- don't make the agent call Resend's API from the sandbox
**Detection:** If agent responses reference email subjects but not email content, this is the cause.
**Confidence:** HIGH (Resend docs explicitly state: "Webhooks do not include the email body, headers, or attachments, only their metadata")

### Pitfall 5: OpenClaw Ignores mcpServers Config -- resend-mcp Won't Load

**What goes wrong:** You add `resend-mcp` to the `mcpServers` section of `openclaw.json`, restart the gateway, and the logs show "ignoring X MCP servers." The agent has no email tools.
**Why it happens:** OpenClaw's ACP (Agent Client Protocol) layer explicitly disables MCP capabilities. The `mcpServers` config key exists but is silently ignored. This is a known limitation tracked in multiple GitHub issues (#4834, #8188, #13248).
**Consequences:** Wasted time debugging a config that will never work. If not caught, the entire MCP integration approach is dead.
**Prevention:**
- **Option A: openclaw-mcp-adapter plugin** -- Install the community plugin that bridges MCP servers to native OpenClaw tools. Configure MCP servers in the plugin's `config.servers` array. Tools appear as first-class agent tools. Downside: community-maintained, may lag OpenClaw updates.
- **Option B: mcporter skill** -- OpenClaw ships with mcporter built-in, which shells out to the mcporter CLI to call MCP tools as a subprocess. Downside: ~2.4 second cold-start per invocation (confirmed).
- **Option C: Custom OpenClaw skill** -- Write a SKILL.md that directly calls the Resend API via `fetch()` from the sandbox. No MCP overhead. Most reliable for a small set of operations (send, reply, list). This is the pattern already used for Oura, Govee, etc.
- **Recommended: Option C** -- Match existing project patterns (Oura, Govee, receipt-scanner are all custom skills). MCP adds unnecessary indirection for 3-4 API calls.
**Detection:** Check gateway logs after restart. Search for "ignoring" or "MCP" in logs.
**Confidence:** HIGH (Multiple GitHub issues confirm; project already uses custom skills for other integrations)

## Moderate Pitfalls

### Pitfall 6: Webhook Signature Verification Skipped in n8n

**What goes wrong:** The n8n webhook accepts any POST request without verifying Resend's Svix signature. An attacker discovers the webhook URL and sends forged "inbound email" payloads, making Bob process fake emails.
**Why it happens:** n8n's generic Webhook node doesn't natively verify Svix signatures. You have to add a Code node to verify manually. Most tutorials skip this step because "it's behind a VPS" -- but the webhook URL is public by definition.
**Prevention:**
- Add a Code node immediately after the Webhook node that verifies the Svix signature:
  - Extract `svix-id`, `svix-timestamp`, `svix-signature` from headers
  - Use the webhook signing secret from Resend dashboard
  - HMAC-SHA256 verify with the raw request body (not parsed JSON -- signature is sensitive to whitespace)
  - Reject with 401 if verification fails
- Store the webhook signing secret as an n8n credential, not hardcoded
- Use a non-guessable webhook path (UUID, not `/webhook/resend`)
- Consider IP allowlisting if Resend publishes their webhook source IPs
**Detection:** Monitor for webhook events that don't correspond to real emails in the Resend dashboard.
**Confidence:** MEDIUM (Resend docs show Svix verification; n8n limitation is well-documented in community)

### Pitfall 7: n8n Webhook URL Misconfiguration Behind Reverse Proxy

**What goes wrong:** n8n generates webhook URLs with `http://localhost:5678` or the wrong hostname because `WEBHOOK_URL` environment variable isn't set. Resend's webhook delivery fails because the URL is unreachable.
**Why it happens:** Self-hosted n8n behind a reverse proxy (Nginx/Caddy) generates URLs based on its internal address, not the public-facing URL. The `WEBHOOK_URL` environment variable is required but not set by default.
**Consequences:** Webhook registration succeeds in Resend (they don't validate the URL upfront), but every inbound email webhook delivery fails. Resend retries on its schedule (5s, 5m, 30m, 2h, 5h, 10h) but all fail.
**Prevention:**
- Set `WEBHOOK_URL=https://your-vps-domain.com/` in n8n environment
- Set `N8N_PROXY_HOPS=1` if behind one reverse proxy
- Set proper `X-Forwarded-Proto`, `X-Forwarded-For` headers in reverse proxy config
- Test the webhook URL is publicly reachable with `curl -X POST https://your-vps-domain.com/webhook/...` from a different machine
- Register the webhook in Resend dashboard and send a test email immediately to verify end-to-end
**Detection:** Check Resend dashboard --> Webhooks --> look for failed delivery attempts with 5xx or timeout errors.
**Confidence:** HIGH (n8n docs explicitly document this as the #1 self-hosted webhook problem)

### Pitfall 8: API Key Scope Mismatch -- Sending Key Can't Read Inbound

**What goes wrong:** You create a `sending_access` API key for security (least privilege), then discover the agent can't fetch inbound email content because the Received Emails API requires `full_access`.
**Why it happens:** Resend offers two permission levels: `full_access` and `sending_access`. The naming implies sending is all you need for outbound, but the Received Emails API, Attachments API, and domain management all require `full_access`.
**Consequences:** Outbound emails work fine. Inbound email webhook arrives at n8n, n8n tries to fetch email body, gets 403 Forbidden. Silent failure if error handling is weak.
**Prevention:**
- Use TWO API keys with different scopes:
  - `full_access` key: stored in n8n credentials, used only by the webhook processing workflow to fetch inbound email content
  - `sending_access` key: passed to the agent sandbox via `openclaw.json` Docker env, used only for sending
- This limits blast radius: if the sandbox key leaks, attacker can only send (not read inbound emails)
- Document which key is which -- they look identical in the dashboard after creation
**Detection:** n8n workflow fails at the "fetch email body" step with 403. Check Resend dashboard API logs.
**Confidence:** MEDIUM (Resend docs confirm permission levels; specific failure mode is inferred from the two-scope design)

### Pitfall 9: No Domain Warmup -- First Emails Land in Spam

**What goes wrong:** Bob starts sending daily briefings, alerts, and notifications from a brand-new subdomain on day 1. Gmail, Outlook, and Yahoo flag everything as spam because the domain has zero sending reputation.
**Why it happens:** New domains are treated as suspicious by default. Email providers build trust based on sending history, volume patterns, and engagement metrics. A new domain sending 20+ emails on day 1 with no history is a red flag.
**Consequences:** Recipients never see Bob's emails. Briefings disappear into spam. Worse, early spam flags make it harder to build reputation later (the domain gets "burned").
**Prevention:**
- Week 1: Send only to your own addresses (Gmail, work email). Max 5-10/day.
- Week 2: Increase to 20-30/day, still known recipients.
- Week 3-4: Reach target volume (likely under 50/day for this use case).
- DKIM + SPF + DMARC must be verified BEFORE sending the first email.
- Start with engaged recipients (yourself) who will open and click -- this trains spam filters that your domain is legitimate.
- Use Resend's test email addresses for development (no reputation impact).
- Monitor Resend dashboard for bounce and complaint rates. Above 2% bounce or 0.1% complaint = stop and investigate.
**Detection:** Check spam folders on recipient addresses. Resend dashboard shows delivery events. Gmail "Show Original" reveals spam score.
**Confidence:** HIGH (Resend's own blog post recommends 30-60 day warmup period)

### Pitfall 10: Resend API Key Exposed to Agent Sandbox

**What goes wrong:** The Resend API key is passed to the Docker sandbox via `openclaw.json` `agents.defaults.sandbox.docker.env`. The agent can see it. If the agent is tricked via prompt injection in an inbound email, it could exfiltrate the key.
**Why it happens:** The agent needs the key to send email. The sandbox architecture requires explicit env var passing. There's no way to give the agent "send-only" access without the key.
**Consequences:** API key leak via prompt injection. Attacker sends emails from your domain. Reputation damage. Possible Resend account abuse.
**Prevention:**
- Use a `sending_access` key (not `full_access`) in the sandbox -- limits damage to sending only
- Keep the `full_access` key ONLY in n8n for inbound email fetching
- Consider routing ALL email sending through n8n too (agent sends a webhook to n8n, n8n sends the actual email) -- removes API key from sandbox entirely
- If key must be in sandbox: rotate it monthly, monitor Resend dashboard for unexpected sends
- Resend shows the key only once at creation -- store it in a password manager, not a file on disk
**Detection:** Resend dashboard shows all sent emails. If emails appear that Bob didn't send, the key is compromised.
**Confidence:** MEDIUM (Sandbox env var exposure is confirmed by project architecture; prompt injection is the theoretical attack vector)

## Minor Pitfalls

### Pitfall 11: Free Tier Daily Limit is 100, Not 3,000

**What goes wrong:** You plan around the 3,000 emails/month headline number but hit the 100 emails/day daily cap unexpectedly. A spike day (weekly review + briefing + alerts + replies) exhausts the daily quota by noon.
**Why it happens:** The daily limit is less prominently documented than the monthly limit. 3,000/month sounds like ~100/day, but the actual daily cap IS 100 -- and with email loops or bursts, it's easy to hit.
**Prevention:**
- Track daily send count in the agent or n8n workflow
- Implement a daily quota check before every send: if count >= 90, switch to "critical only" mode
- Design the system assuming 50 emails/day max usable (leave 50% buffer for retries and edge cases)
- If consistently hitting limits: upgrade to Pro ($20/month, no daily limit, 50K/month)
- Rate limit: Resend free tier is 2 requests/second -- batch operations need throttling
**Detection:** Resend returns error objects (not exceptions) when rate limited. Check for HTTP 429 responses in n8n or agent logs.
**Confidence:** HIGH (Resend pricing page and quotas doc confirm: 100 emails/day on free tier)

### Pitfall 12: Svix Retry Window is Only ~24 Hours Total

**What goes wrong:** n8n goes down for maintenance or crashes. Resend retries webhooks on a schedule (immediately, 5s, 5m, 30m, 2h, 5h, 10h, 10h) but the total retry window is approximately 27.5 hours. If n8n is down longer, inbound emails are permanently lost (webhook delivery fails, no further retries).
**Why it happens:** The Svix retry schedule is aggressive early but stops after about a day. If n8n has extended downtime, retries exhaust before it comes back.
**Prevention:**
- Ensure n8n has proper process management (systemd, Docker restart policy)
- Set up uptime monitoring on the n8n webhook endpoint
- Resend stores emails even if webhooks fail -- build a "catch-up" cron that polls the Received Emails API for any emails missed during downtime
- Manual replay: Resend dashboard lets you manually replay failed webhook events
**Detection:** Compare Resend dashboard "received emails" count against n8n workflow execution count. Mismatch = missed webhooks.
**Confidence:** HIGH (Svix docs confirm retry schedule; Resend uses Svix for webhooks)

### Pitfall 13: HTML Email Content Overwhelms Agent Context

**What goes wrong:** Inbound emails contain verbose HTML (marketing emails, newsletters, forwarded threads with deep nesting). The raw HTML is passed to the agent, consuming most of the context window with `<div style="...">`  noise.
**Why it happens:** The Received Emails API returns both `text` and `html` fields. If you pass `html` to the agent, it gets the full HTML source. Even `text` can be bloated with forwarded thread chains.
**Prevention:**
- In the n8n workflow, prefer the `text` field over `html` -- it's pre-stripped
- If `text` is empty, use a Code node to strip HTML tags and extract meaningful content
- Truncate email body to a reasonable length (e.g., 2000 characters) before forwarding to agent
- For forwarded threads, extract only the most recent message (split on common reply markers like "On [date], [name] wrote:")
- Store full email content in a file on the workspace (write to `/workspace/emails/`) and give agent just a summary + file path
**Detection:** Agent responses become vague or reference "the email" without specifics -- context window may be overwhelmed.
**Confidence:** MEDIUM (General email integration pattern; Resend's API structure confirmed)

### Pitfall 14: Testing Sends Real Emails During Development

**What goes wrong:** During development, test emails go to real addresses (personal Gmail, coworker addresses). You burn through daily quota, pollute your domain reputation with test noise, and annoy recipients.
**Why it happens:** Resend doesn't have a full "sandbox mode" like Postmark. There's no "test environment" toggle -- all sends via the API are real.
**Prevention:**
- Use Resend's built-in test email addresses that simulate different events (bounce, complaint, etc.) without actually sending
- During development, send ONLY to your own verified email address using the sandbox domain (before custom domain verification)
- Use the Resend dashboard "Send Test Email" feature for quick verification
- In agent skills, add a `DRY_RUN` env variable that logs the email instead of sending it
- Only switch to the real domain after the full integration chain is verified end-to-end
**Detection:** Check Resend dashboard for unexpected sends to real addresses during development.
**Confidence:** HIGH (Resend docs confirm test email feature and sandbox domain for pre-verification testing)

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| DNS/Domain Setup | MX record on root domain (Pitfall 1) | Use subdomain, verify existing MX first |
| DNS/Domain Setup | DMARC inheritance blocking sends (Pitfall 2) | Check parent DMARC before any sending |
| MCP/Skill Integration | mcpServers config silently ignored (Pitfall 5) | Use custom SKILL.md, not MCP server |
| n8n Webhook Chain | Webhook URL wrong behind reverse proxy (Pitfall 7) | Set WEBHOOK_URL env var, test end-to-end |
| n8n Webhook Chain | Webhook body has no email content (Pitfall 4) | Add Received Emails API call in n8n flow |
| n8n Webhook Chain | Missing signature verification (Pitfall 6) | Add Svix HMAC check in Code node |
| Agent Email Skills | Email loop from auto-replies (Pitfall 3) | Header checking + rate limiting + Auto-Submitted header on outbound |
| Agent Email Skills | API key exposure in sandbox (Pitfall 10) | Use sending_access scope, keep full_access in n8n only |
| Testing | Real emails sent during dev (Pitfall 14) | Use Resend test addresses and sandbox domain |
| Go-Live | Domain not warmed up (Pitfall 9) | 2-4 week gradual warmup before relying on delivery |
| Ongoing Operations | Free tier daily limit hit (Pitfall 11) | Track daily count, implement quota check |
| Ongoing Operations | n8n downtime loses webhooks (Pitfall 12) | Catch-up cron polling Received Emails API |

## Integration Chain Risk Map

The Resend + n8n + OpenClaw chain has multiple failure points. Here's where each can break:

```
Sender --> Resend (MX) --> Webhook --> n8n (VPS) --> Tailscale --> OpenClaw (EC2) --> Agent
  |           |              |           |              |             |             |
  |           |              |           |              |             |             +-- Loop risk (Pitfall 3)
  |           |              |           |              |             +-- mcpServers ignored (Pitfall 5)
  |           |              |           |              +-- Tailscale-only, no public webhook
  |           |              |           +-- WEBHOOK_URL wrong (Pitfall 7)
  |           |              |           +-- No body in payload (Pitfall 4)
  |           |              |           +-- No signature check (Pitfall 6)
  |           |              +-- Retry window ~24h (Pitfall 12)
  |           +-- MX on wrong domain (Pitfall 1)
  |           +-- DMARC blocks delivery (Pitfall 2)
  +-- Spam folder (Pitfall 9)
```

## Sources

- [Resend - Managing Domains (SPF/DKIM)](https://resend.com/docs/dashboard/domains/introduction)
- [Resend - Custom Receiving Domains (MX)](https://resend.com/docs/dashboard/receiving/custom-domains)
- [Resend - How DMARC Applies to Subdomains](https://resend.com/blog/how-dmarc-applies-to-subdomains)
- [Resend - Webhook Signature Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests)
- [Resend - Inbound Emails Blog Post](https://resend.com/blog/inbound-emails)
- [Resend - Account Quotas and Limits](https://resend.com/docs/knowledge-base/account-quotas-and-limits)
- [Resend - How to Warm Up a New Domain](https://resend.com/blog/how-to-warm-up-a-new-domain)
- [Resend - Send Test Emails](https://resend.com/docs/dashboard/emails/send-test-emails)
- [Resend - How to Handle API Keys](https://resend.com/docs/knowledge-base/how-to-handle-api-keys)
- [Resend - Receiving Emails Documentation](https://resend.com/docs/dashboard/receiving/introduction)
- [Resend MCP Server (npm)](https://www.npmjs.com/package/resend-mcp)
- [Resend MCP Server Docs](https://resend.com/docs/knowledge-base/mcp-server)
- [Svix Retry Schedule](https://docs.svix.com/retries)
- [n8n - Configure Webhook URLs with Reverse Proxy](https://docs.n8n.io/hosting/configuration/configuration-examples/webhook-url/)
- [n8n - Webhook Node Common Issues](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/common-issues/)
- [RFC 3834 - Automatic Responses to Electronic Mail](https://datatracker.ietf.org/doc/html/rfc3834)
- [Detecting Auto-Reply Emails (arp242.net)](https://www.arp242.net/autoreply.html)
- [OpenClaw MCP Feature Request #13248](https://github.com/openclaw/openclaw/issues/13248)
- [OpenClaw MCP Adapter Plugin](https://github.com/androidStern-personal/openclaw-mcp-adapter)
- [DmarcDkim.com - Resend SPF/DKIM/DMARC Setup](https://dmarcdkim.com/setup/how-to-setup-resend-spf-dkim-and-dmarc-records)
