# Project Research Summary

**Project:** Resend email integration for OpenClaw/Bob (pops-claw)
**Domain:** Email API integration for AI agent system
**Researched:** 2026-02-16
**Confidence:** HIGH

## Executive Summary

This project integrates Resend email capabilities into an existing OpenClaw AI agent deployment. The research reveals a straightforward outbound path (agent sends via Resend REST API) but a more complex inbound path requiring webhook relay infrastructure. The recommended approach avoids MCP servers (which OpenClaw silently ignores) in favor of custom skills using direct `curl` API calls from the sandbox. This matches the established pattern used for Oura, GitHub, and other integrations in this deployment.

The critical architectural constraint is that the EC2 instance has no public IP (Tailscale-only access), which blocks direct webhook reception. The solution is to use the existing n8n instance on the VPS (165.22.139.214) as a webhook relay: Resend POSTs to the VPS, n8n verifies the Svix signature and transforms the payload, then forwards to OpenClaw over Tailscale. The key risk is the multi-hop integration chain (7 potential failure points), mitigated by careful attention to webhook signature verification, auto-reply loop prevention, and proper DNS subdomain configuration.

Sending capability delivers immediate value (morning briefings via email, alert backup channel) with minimal risk. Receiving capability requires more infrastructure work but unlocks two-way email conversations and external party integration. The phased approach prioritizes sending first, then receiving, then threading/conversation features.

## Key Findings

### Recommended Stack

**Outbound emails:** Use Resend REST API directly via `curl` from the Docker sandbox. No npm packages needed, avoiding the read-only filesystem constraint. A custom SKILL.md teaches Bob to construct API calls using the `exec` tool with `curl -X POST`. This is the same proven pattern used for Oura, Govee, and receipt-scanner integrations.

**Inbound emails:** Use n8n (existing VPS) as webhook relay. Resend sends webhooks to public HTTPS endpoint on VPS, n8n verifies Svix signatures and fetches full email content (webhooks contain only metadata), then forwards complete payload to OpenClaw hooks endpoint over Tailscale. This solves the "no public IP on EC2" problem without exposing the gateway to the internet.

**Core technologies:**
- Resend REST API v1 (https://api.resend.com) — transactional email with receiving capability, 100/day free tier sufficient for personal use
- `curl` (already in sandbox) — HTTP client for API calls, no installation needed
- n8n webhook node (existing VPS) — public HTTPS endpoint for Resend webhooks, already deployed with Caddy TLS
- `svix` npm package in n8n — verify webhook signatures (Resend uses Svix for signing), prevents forged email injection

**What NOT to use:**
- **Resend MCP Server:** OpenClaw's ACP layer silently ignores `mcpServers` config. The mcporter workaround adds 2.4s cold-start per call. Direct REST API calls are faster and proven.
- **Resend Node.js SDK:** Sandbox filesystem is read-only, `npm install` fails. The REST API is simple enough that SDK overhead isn't justified.
- **Direct webhooks to EC2:** Gateway binds to loopback (127.0.0.1), no public IP. Exposing it would violate the Tailscale-only security model.

### Expected Features

**Must have (table stakes):**
- Send plain text and HTML email — core capability, max 40MB per email
- Domain verification (SPF/DKIM/DMARC) — without it, emails go to spam or get rejected
- Webhook signature verification — prevents anyone from POSTing fake emails to the endpoint
- Inbound email receiving — two-way communication is expected for an email-enabled agent
- Delivery status tracking — must know if emails bounced, failed, or were delivered
- Reply threading with In-Reply-To headers — replies appear in same thread, not separate emails
- API key management — secure credential handling via openclaw.json sandbox env

**Should have (competitive):**
- Morning briefing via email — reuse existing briefing content, deliver via email in addition to Slack (most impactful quick win)
- Alert/notification emails — critical alerts sent via email as backup channel when Slack is muted
- Email-to-Slack bridging — forward important inbound emails to Slack for visibility
- Scheduled email sends — schedule up to 72 hours in advance using Resend's `scheduled_at` param
- Conversation history tracking — store message_id and thread relationships in local DB for context

**Defer (v2+):**
- Inbound email command processing — "email Bob a question, get email response" requires sender verification, intent parsing, high complexity
- Attachment sending/receiving — adds significant complexity, wait for specific use case
- Email templates (React Email) — start with simple HTML, formalize templates later
- Batch sends — only relevant at scale, free tier makes this nearly irrelevant
- Email analytics/tagging — add organically as patterns emerge

### Architecture Approach

The architecture splits into two independent paths: outbound (agent sends emails) and inbound (agent receives and processes emails). Outbound is self-contained within the EC2/sandbox boundary. Inbound requires the VPS as a public-facing relay because the EC2 instance has no public IP. The webhook relay pattern follows defense-in-depth: verify signatures at the edge (n8n), transform payloads to match OpenClaw hooks format, forward over Tailscale with dedicated auth token.

**Major components:**
1. **Resend REST API** — external service providing send/receive/webhooks. Direct HTTP calls via curl from sandbox. Auth: `Authorization: Bearer re_xxxxx` header
2. **Custom skill (resend-email)** — SKILL.md at `~/.openclaw/skills/resend-email/` teaching Bob to construct curl commands for send, get received email, list emails. Uses `RESEND_API_KEY` from sandbox env
3. **n8n webhook workflow** — receives Resend webhooks at public HTTPS endpoint, verifies Svix signature (HMAC-SHA256), calls Received Emails API to fetch full body (webhook only has metadata), forwards complete payload to OpenClaw hooks endpoint over Tailscale
4. **OpenClaw hooks endpoint** — receives formatted email notifications from n8n, wakes Bob in isolated session per email_id, delivers notification to Slack
5. **DNS records** — subdomain MX records for receiving (avoids conflicting with existing email on root domain), SPF/DKIM/DMARC for sending reputation

**Critical architectural constraint:** Gateway currently binds to loopback (127.0.0.1:18789). For n8n on VPS to reach hooks endpoint over Tailscale, gateway must also listen on Tailscale interface. Recommendation: change `bind` from `"loopback"` to `"tailscale"` in openclaw.json. This is secure because Tailscale network only has 2 nodes (EC2 + VPS), both controlled by same user, and gateway already has token auth.

### Critical Pitfalls

1. **MX record on root domain nukes existing email** — Adding Resend's MX to root domain intercepts ALL email for the domain, breaking existing Gmail/Workspace. ALWAYS use a subdomain (e.g., `mail.yourdomain.com` or `bot.yourdomain.com`) for Resend receiving. Verify existing MX with `dig MX yourdomain.com` before adding anything.

2. **Agent email loop from auto-replies** — Bob receives out-of-office auto-reply, treats it as real email, replies, triggers another auto-reply, burns through 100/day quota in minutes. Prevention: check headers (`Auto-Submitted`, `X-Auto-Response-Suppress`, `Precedence`) before processing ANY inbound email. Add rate limiting (max 1 reply per sender per hour). Hard cap: halt all sending if >10 emails in 5 minutes. Add `Auto-Submitted: auto-generated` to all Bob's outbound emails.

3. **Webhook body is metadata-only** — Resend inbound webhook contains NO email body, NO headers, NO attachment content. Only from/to/subject/email_id. The n8n workflow MUST make a second API call to `GET /received-emails/{id}` to fetch actual email content. Cache the full email in n8n payload before forwarding to OpenClaw. The agent cannot operate on webhook metadata alone.

4. **OpenClaw ignores mcpServers config** — The `mcpServers` section in openclaw.json is silently ignored. ACP layer explicitly disables MCP. This means resend-mcp won't load via standard config. Solution: use custom SKILL.md with direct curl calls (matches existing project patterns). Alternative: openclaw-mcp-adapter plugin, but it's community-maintained and adds complexity.

5. **Webhook signature verification skipped in n8n** — n8n's generic Webhook node doesn't natively verify Svix signatures. Must add Code node after webhook trigger to manually verify `svix-id`, `svix-timestamp`, `svix-signature` headers with HMAC-SHA256. Without this, anyone discovering the webhook URL can inject forged emails. Use raw request body for verification (signature is whitespace-sensitive, parsed JSON breaks it).

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Outbound Email Foundation
**Rationale:** Sending is dramatically simpler than receiving (no webhook infrastructure needed) and delivers immediate value. Proven to work: every API integration in this project uses the same pattern (custom skill + curl + sandbox env var). Zero external dependencies beyond Resend account setup.

**Delivers:** Bob can send emails via custom skill. Morning briefings delivered to email. Alert notifications have email backup channel.

**Addresses features:**
- Send plain text and HTML email (table stakes)
- Domain verification for sending (table stakes)
- API key management (table stakes)
- Morning briefing via email (differentiator)
- Alert/notification emails (differentiator)

**Avoids pitfalls:**
- Uses custom skill (not MCP) — avoids Pitfall 4 (mcpServers ignored)
- Adds `Auto-Submitted: auto-generated` to outbound — prevents other bots from creating loops

**Research flag:** No research needed. This is the exact pattern used for Oura, Govee, receipt-scanner. Well-documented REST API, HIGH confidence sources.

### Phase 2: Inbound Email Infrastructure
**Rationale:** Receiving requires multi-component setup (DNS MX records, n8n webhook relay, hooks configuration, gateway bind change). These are prerequisites for any inbound email processing. Must be completed as a unit because partial setup doesn't deliver value. This phase establishes the plumbing; next phase adds the processing logic.

**Delivers:** Email sent to `bob@subdomain.yourdomain.com` triggers webhook → n8n relay → OpenClaw hook → Bob receives notification in Slack with email metadata and full content.

**Addresses features:**
- Inbound email receiving (table stakes)
- Webhook signature verification (table stakes)
- Email-to-Slack bridging (differentiator)

**Avoids pitfalls:**
- Uses subdomain for MX (not root domain) — avoids Pitfall 1 (nuking existing email)
- Two-step email read (metadata in webhook, body via API call) — addresses Pitfall 3 (webhook body is metadata-only)
- Svix signature verification in n8n Code node — avoids Pitfall 5 (forged email injection)
- Gateway binds to Tailscale (not just loopback) — enables webhook forwarding over Tailscale without exposing to internet

**Stack elements:**
- n8n webhook workflow on VPS (relay pattern)
- svix verification in Code node
- Resend Received Emails API for fetching full content
- OpenClaw hooks endpoint (new config in openclaw.json)

**Research flag:** LIGHT research during phase planning. Need to verify:
- Exact n8n Code node syntax for Svix HMAC-SHA256 verification
- OpenClaw hooks config format (documented but untested in this deployment)
- Whether `bind: "tailscale"` is valid in openclaw.json (may need to be IP address like `bind: "100.72.143.9"`)

### Phase 3: Inbound Email Processing
**Rationale:** With receiving infrastructure stable (Phase 2), this phase adds intelligence: header checking for auto-replies, rate limiting, reply logic, conversation threading. These features require the inbound path to be reliable before testing edge cases like loops.

**Delivers:** Bob intelligently processes inbound emails: filters auto-replies, replies to recognized senders, tracks conversation threads, bridges important emails to Slack.

**Addresses features:**
- Delivery status tracking via webhooks (table stakes)
- Reply threading with In-Reply-To (table stakes)
- Conversation history tracking (differentiator)
- Scheduled email sends (differentiator)

**Avoids pitfalls:**
- Header checking for auto-replies — prevents Pitfall 2 (email loops)
- Rate limiting (max 1 reply per sender per hour) — secondary loop prevention
- Hard cap (halt if >10 sends in 5 min) — circuit breaker for loop scenarios
- API key scope split (full_access in n8n, sending_access in sandbox) — limits blast radius if key leaks

**Implements architecture component:** Session key per email pattern (`hook:email:<email_id>`) for isolated processing, thread detection via In-Reply-To/References headers.

**Research flag:** MEDIUM research needed during phase planning:
- Exact header names/values for auto-reply detection (RFC 3834 lists several variants, need comprehensive list)
- Resend API pagination for conversation history lookups
- Testing strategy for loop scenarios (can't test with real email, need simulation approach)

### Phase 4: Domain Warmup and Production Hardening
**Rationale:** New domains have zero sending reputation. Emails from cold domains land in spam regardless of technical correctness (SPF/DKIM/DMARC). This phase executes the 2-4 week warmup schedule and adds operational monitoring. Must come after basic sending works (Phase 1) but before relying on email delivery for critical functions.

**Delivers:** Domain reputation established through gradual volume increase. Monitoring confirms emails reach inboxes (not spam). Daily quota tracking prevents hitting free tier limits.

**Addresses features:**
- None directly (this is operational hardening, not feature work)

**Avoids pitfalls:**
- Gradual warmup (5-10/day week 1, 20-30/day week 2, target volume week 3-4) — prevents Pitfall 9 (first emails land in spam)
- Daily send count tracking — prevents Pitfall 11 (hitting 100/day limit unexpectedly)
- Catch-up cron polling Received Emails API — mitigates Pitfall 12 (n8n downtime loses webhooks beyond 27.5hr retry window)
- Test emails to own addresses only during warmup — avoids polluting domain reputation with dev noise

**Research flag:** No research needed. Resend docs explicitly recommend 30-60 day warmup. Standard operational patterns.

### Phase Ordering Rationale

**Phase 1 → 2 → 3 sequencing:** Outbound is independent and simple (proven pattern). Inbound requires infrastructure setup (Phase 2) before intelligence (Phase 3). Can't test auto-reply loop prevention until basic receiving works. Phase 4 runs parallel with Phase 1-3 (warmup starts after first send, takes weeks).

**Why Phase 2 before Phase 3:** The webhook relay chain (Resend → n8n → OpenClaw hooks) has 7 potential failure points. Must verify end-to-end before adding complexity (reply logic, threading, rate limiting). "Make it work, then make it smart."

**Why Phase 4 is parallel:** Domain warmup is time-based (2-4 weeks), not work-based. Start sending low-volume emails to own addresses immediately after Phase 1, increase gradually while building Phase 2-3. By the time Phase 3 is complete, domain reputation is established.

**Dependency chain confirmed by research:**
- Phase 1 needs: Resend account + API key + DNS for sending
- Phase 2 needs: Phase 1 stable + DNS for receiving + n8n + hooks config
- Phase 3 needs: Phase 2 stable + conversation tracking DB schema
- Phase 4 needs: Phase 1 complete (start warmup)

### Research Flags

Phases needing deeper research during planning:

- **Phase 2 (Inbound Infrastructure):** LIGHT research needed for n8n Code node Svix verification syntax and OpenClaw hooks config format. Both are documented but untested in this specific deployment. Budget 30-60 min for verification.

- **Phase 3 (Inbound Processing):** MEDIUM research needed for comprehensive auto-reply header detection (RFC 3834 lists several variants, plus vendor-specific headers from Microsoft/Google). Also need testing strategy for loop scenarios. Budget 1-2 hours for research-phase.

Phases with standard patterns (skip research-phase):

- **Phase 1 (Outbound Foundation):** Exact same pattern as Oura/Govee/receipt-scanner integrations. Resend REST API is well-documented (official docs, HIGH confidence). No unknowns.

- **Phase 4 (Domain Warmup):** Operational task, not technical implementation. Resend docs provide explicit warmup schedule. No research needed, just execution discipline.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Resend REST API is official, well-documented. Custom skill pattern proven in 4+ existing integrations. n8n webhook relay is established (used for ClawdStrike, other workflows). |
| Features | HIGH | Feature landscape derived from official Resend docs (API reference, receiving docs, webhook docs). Free tier constraints (100/day, 3K/month) confirmed on pricing page. MVP recommendation aligns with dependency chain. |
| Architecture | MEDIUM-HIGH | Outbound path is HIGH confidence (proven pattern). Inbound path is MEDIUM confidence (documented components but untested full integration chain). Hooks endpoint config format is documented but not yet tested in this deployment. Gateway bind change to Tailscale is inferred (need to verify exact config syntax). |
| Pitfalls | HIGH | MX record, DMARC, webhook metadata-only, and mcpServers pitfalls are directly confirmed by official docs. Email loop prevention (RFC 3834, auto-reply headers) is industry-standard practice. Warmup requirement confirmed by Resend blog post. |

**Overall confidence:** HIGH

### Gaps to Address

- **OpenClaw hooks config format:** Documentation shows structure but exact field names (especially for `deliver` and `channel` routing) need verification. Plan: review openclaw.json schema or test with minimal config in Phase 2 planning.

- **Gateway bind syntax:** Need to confirm whether `bind: "tailscale"` is magic string that OpenClaw resolves, or if it requires explicit IP address like `bind: "100.72.143.9"`. Plan: check OpenClaw configuration docs or `openclaw doctor` output during Phase 2 planning.

- **Auto-reply header coverage:** RFC 3834 defines standard headers but vendors (Microsoft, Google, Apple) use additional X-headers. Need comprehensive list to avoid false negatives. Plan: research-phase in Phase 3 to compile full header checklist from RFCs + vendor docs.

- **Resend webhook event payload format for delivery status:** Research confirmed `email.sent`, `email.delivered`, `email.bounced`, `email.failed` events exist but didn't capture exact JSON schema. Plan: reference Resend webhook event types docs during Phase 2-3 implementation.

- **n8n Svix verification implementation:** Concept is clear (HMAC-SHA256 with raw body) but exact JavaScript syntax in n8n Code node needs verification. Svix docs provide examples but n8n's request object format may differ. Plan: test minimal verification Code node during Phase 2 implementation.

## Sources

### Primary (HIGH confidence)
- [Resend API Reference](https://resend.com/docs/api-reference/introduction) — All API endpoints, request/response formats, auth
- [Resend Receiving Emails](https://resend.com/docs/dashboard/receiving/introduction) — Inbound email setup, MX records, two-step fetch pattern
- [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests) — Svix signature verification, headers, HMAC-SHA256
- [Resend Webhook Event Types](https://resend.com/docs/dashboard/webhooks/event-types) — All 17 webhook event types, payload schemas
- [Resend Custom Receiving Domains](https://resend.com/docs/dashboard/receiving/custom-domains) — Subdomain MX setup, catch-all addresses
- [Resend Account Quotas and Limits](https://resend.com/docs/knowledge-base/account-quotas-and-limits) — Free tier: 3K/month, 100/day, 2 req/sec
- [Resend Domain Management](https://resend.com/docs/dashboard/domains/introduction) — SPF, DKIM, DMARC DNS records
- [Resend Pricing](https://resend.com/pricing) — Free tier confirmed: 3K emails/month, 100/day
- [Resend How DMARC Applies to Subdomains](https://resend.com/blog/how-dmarc-applies-to-subdomains) — Inheritance rules, sp= tag
- [Resend How to Warm Up a New Domain](https://resend.com/blog/how-to-warm-up-a-new-domain) — 30-60 day schedule, gradual volume
- [RFC 3834 - Automatic Responses to Electronic Mail](https://datatracker.ietf.org/doc/html/rfc3834) — Auto-reply headers standard
- [Svix Webhook Verification](https://docs.svix.com/receiving/verifying-payloads/how) — HMAC-SHA256 verification algorithm
- [Svix Retry Schedule](https://docs.svix.com/retries) — Retry timing: 5s, 5m, 30m, 2h, 5h, 10h (27.5hr total)
- [OpenClaw Skills Documentation](https://docs.openclaw.ai/tools/skills) — Skill format, env vars, exec tool usage
- [OpenClaw Webhooks Documentation](https://docs.openclaw.ai/automation/webhook) — Hooks endpoint config, sessionKey, mappings
- [n8n Webhook Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) — Webhook trigger config
- [n8n Configure Webhook URLs with Reverse Proxy](https://docs.n8n.io/hosting/configuration/configuration-examples/webhook-url/) — WEBHOOK_URL env var requirement

### Secondary (MEDIUM confidence)
- [n8n-nodes-resend GitHub](https://github.com/jonathanferreyra/n8n-nodes-resend) — Community node, API coverage (alternative to HTTP Request node)
- [OpenClaw MCP Limitations Gist](https://gist.github.com/Rapha-btc/527d08acc523d6dcdb2c224fe54f3f39) — mcpServers silently ignored
- [OpenClaw MCP Feature Request #13248](https://github.com/openclaw/openclaw/issues/13248) — Native MCP support tracked as feature request
- [Detecting Auto-Reply Emails (arp242.net)](https://www.arp242.net/autoreply.html) — Comprehensive header list, vendor-specific X-headers
- [OpenClaw MCP Adapter Plugin](https://github.com/androidStern-personal/openclaw-mcp-adapter) — Community plugin bridging MCP to native tools

### Tertiary (LOW confidence, needs validation)
- [react-email-skills ClawHub](https://playbooks.com/skills/openclaw/skills/react-email-skills) — Published skill for React Email templates (not verified for sandbox compatibility)
- Phase 4 MCP verification (internal, 2026-02-08) — Confirmed sandbox read-only filesystem, bind-mount pattern for gh/sqlite3 (referenced in architecture findings)

---
*Research completed: 2026-02-16*
*Ready for roadmap: yes*
