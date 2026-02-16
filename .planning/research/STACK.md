# Technology Stack: Resend Email Integration

**Project:** pops-claw Resend email integration
**Researched:** 2026-02-16
**Overall Confidence:** HIGH

## Recommended Stack

### Core: Resend REST API (Direct `curl`/`exec` from Sandbox)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Resend REST API | v1 | Send, receive, manage emails | Direct HTTP calls via `curl` from sandbox — no npm install needed, works in read-only Docker filesystem, zero cold-start overhead |
| `curl` | (already in sandbox) | HTTP client for API calls | Already available in Docker sandbox image, no setup needed |

**API Base URL:** `https://api.resend.com`
**Auth:** `Authorization: Bearer re_xxxxxxxxx` header

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/emails` | Send single email |
| POST | `/emails/batch` | Send up to 100 emails |
| GET | `/emails/{id}` | Get email details |
| GET | `/emails` | List sent emails |
| PATCH | `/emails/{id}` | Update scheduled email |
| POST | `/emails/{id}/cancel` | Cancel scheduled email |
| GET | `/received-emails` | List received (inbound) emails |
| GET | `/received-emails/{id}` | Get received email details |
| GET | `/received-emails/{id}/attachments` | List attachments |
| GET | `/received-emails/{id}/attachments/{attachment_id}` | Download attachment |
| POST | `/domains` | Create domain |
| GET | `/domains` | List domains |
| POST | `/domains/{id}/verify` | Verify domain DNS |
| POST | `/contacts` | Create contact |
| POST | `/webhooks` | Create webhook |

**Confidence:** HIGH (official Resend API docs at resend.com/docs/api-reference/introduction)

### Webhook Verification: Svix Library (on n8n VPS)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `svix` npm package | ^1.84.1 | Verify Resend webhook signatures | Resend uses Svix for webhook signing; this is the official verification library |

**Verification Headers:** `svix-id`, `svix-timestamp`, `svix-signature`
**Secret format:** `whsec_` prefix, base64-encoded HMAC-SHA256

**Confidence:** HIGH (Resend docs + Svix docs both confirm this approach)

### Webhook Routing: n8n on DigitalOcean VPS

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| n8n Webhook node | (existing) | Receive Resend webhook POSTs | Already deployed at 165.22.139.214 with Caddy HTTPS — provides public endpoint Resend can reach |
| n8n HTTP Request node | (existing) | Forward processed webhooks to OpenClaw | Can relay inbound email events to OpenClaw gateway |
| n8n-nodes-resend | ^1.1.0 | Community node for Resend API in n8n | Full API coverage: send, contacts, domains, broadcasts, webhooks. Install in n8n Settings > Community Nodes |

**Confidence:** MEDIUM (n8n-nodes-resend is community-maintained, not official n8n built-in. Still in active development per npm page. Webhook node is HIGH confidence — core n8n)

### OpenClaw Integration: Custom Skill

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Custom SKILL.md | n/a | Teach Bob to send/read Resend emails | Skills are OpenClaw's native integration pattern. Works in sandbox via `exec` + `curl`. No MCP server needed |
| `RESEND_API_KEY` env var | n/a | Auth for Resend API | Injected to sandbox via `agents.defaults.sandbox.docker.env` in openclaw.json (proven pattern from Phase 2/4) |

**Confidence:** HIGH (skills + sandbox env injection is the same proven pattern used for Oura, GitHub, gog)

### DNS: Domain Verification Records

| Record Type | Name Pattern | Value | Purpose |
|-------------|-------------|-------|---------|
| TXT | `resend._domainkey.yourdomain.com` | (Resend-generated DKIM public key) | DKIM email authentication |
| TXT | `yourdomain.com` or subdomain | `v=spf1 include:amazonses.com ~all` | SPF authorization (Resend uses AWS SES) |
| MX | `yourdomain.com` or subdomain | `feedback-smtp.us-east-1.amazonses.com` | Bounce/complaint handling |
| MX | Receiving subdomain (e.g. `inbound.yourdomain.com`) | (Resend-provided MX for inbound) | Inbound email reception |
| TXT | `_dmarc.yourdomain.com` | `v=DMARC1; p=none;` | DMARC (optional but recommended) |

**IMPORTANT:** Exact record values are generated per-domain by Resend dashboard. The above patterns are illustrative. Inbound email requires a SEPARATE MX record that must be lowest-priority for that domain/subdomain.

**Confidence:** MEDIUM (patterns confirmed across multiple sources but exact values are per-domain; SPF include domain may vary)

## What NOT to Use

### Resend MCP Server -- DO NOT USE

| Technology | Why Not |
|------------|---------|
| `resend-mcp` (github.com/resend/mcp-send-email) | **OpenClaw silently ignores `mcpServers` config.** The ACP layer explicitly disables MCP, logging "ignoring X MCP servers." The mcporter skill workaround cold-starts the MCP server (~2.4s per call), adding unacceptable latency for email operations. Direct REST API calls via `curl` are faster, simpler, and proven in this sandbox |

**Confidence:** HIGH (multiple sources confirm OpenClaw ignores mcpServers; gist by Rapha-btc documents the issue; GitHub issues #4834 and #13248 track native MCP support as a feature request)

### Resend Node.js SDK -- DO NOT USE

| Technology | Why Not |
|------------|---------|
| `resend` npm v6.9.2 | Sandbox filesystem is **read-only** — `npm install` fails. `npx` is available but adds cold-start overhead. The REST API is trivial (`curl -X POST` with JSON body and Bearer token). No benefit to SDK in this context |

**Confidence:** HIGH (sandbox read-only filesystem confirmed in Phase 4 learnings; curl is already available)

### Published Resend OpenClaw Skills (ClawHub) -- EVALUATE, LIKELY SKIP

| Technology | Why Caution |
|------------|-------------|
| `react-email-skills` (openclaw/skills) | Designed for React Email template development with local dev server. Overkill for sending API emails from sandbox. Bob doesn't need a React project scaffold |
| `clawmail` (heyarviind/clawmail) | Third-party community skill. Unverified quality, may not match our sandbox constraints (read-only FS, bind-mount pattern) |

**Recommendation:** Write a custom skill tailored to this deployment's sandbox constraints. Reference the published skills for API patterns but don't install them directly.

**Confidence:** MEDIUM (published skills exist but haven't verified compatibility with our specific sandbox config)

## Recommended Stack Summary

```
SEND EMAIL:     Bob's sandbox -> curl -> api.resend.com/emails
READ INBOUND:   Bob's sandbox -> curl -> api.resend.com/received-emails/{id}
RECEIVE WEBHOOK: Resend -> HTTPS -> n8n (VPS) -> process -> relay to OpenClaw
VERIFY WEBHOOK:  n8n workflow -> svix library or manual HMAC-SHA256
MANAGE DOMAIN:   Resend dashboard + DNS provider (one-time setup)
```

## Integration Architecture

```
                          Internet
                             |
                    [Resend API Cloud]
                   /         |         \
                  /          |          \
     Send/Read API    Webhook POST    DNS Verification
         |                |               |
    [EC2 Sandbox]   [DO VPS n8n]    [DNS Provider]
    curl + Bearer    Caddy HTTPS     TXT/MX/CNAME
         |                |
    RESEND_API_KEY   RESEND_WEBHOOK_SECRET
    (openclaw.json)  (n8n credentials)
```

## Environment Variables to Add

### On EC2 (openclaw.json sandbox env)

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "docker": {
          "env": {
            "RESEND_API_KEY": "re_xxxxxxxxx"
          }
        }
      }
    }
  }
}
```

### On EC2 (.env for gateway)

```bash
RESEND_API_KEY=re_xxxxxxxxx
```

### On VPS (n8n credentials)

```
RESEND_API_KEY=re_xxxxxxxxx         # For n8n-nodes-resend (if used)
RESEND_WEBHOOK_SECRET=whsec_xxxxx   # For webhook signature verification
```

## Resend Pricing Context

| Plan | Price | Emails/month | Daily limit | Notes |
|------|-------|-------------|-------------|-------|
| Free | $0 | 3,000 | 100/day | 1 sending domain, sufficient for personal use |
| Pro | $20/mo | 50,000 | n/a | Multiple domains, custom return path |

Free tier is sufficient for a personal assistant deployment. 100 emails/day covers all realistic personal use.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Email API | Resend REST API | Resend Node.js SDK | Read-only sandbox, npm install fails, curl is simpler |
| Email API | Resend REST API | Resend MCP Server | OpenClaw ignores mcpServers, mcporter adds 2.4s cold-start |
| Webhook receiver | n8n on VPS | Direct webhook to EC2 | EC2 has no public IP (Tailscale-only), can't receive webhooks |
| Webhook receiver | n8n on VPS | Cloudflare Workers | Extra infrastructure, n8n already deployed and working |
| Agent integration | Custom skill | Published ClawHub skills | Custom skill matches our exact sandbox constraints |
| n8n email | n8n-nodes-resend | n8n HTTP Request node | Community node provides better DX, but HTTP Request is always a fallback |

## Installation Steps

### Phase 1: Resend Account + Domain (manual, one-time)

```bash
# 1. Create Resend account at resend.com
# 2. Add sending domain in Resend dashboard
# 3. Add DNS records (TXT for SPF/DKIM, MX for bounces)
# 4. Verify domain in Resend dashboard
# 5. Generate API key (re_xxxxx)
# 6. (Optional) Enable receiving on domain/subdomain
# 7. Add receiving MX record if inbound needed
```

### Phase 2: EC2 Config (SSH to 100.72.143.9)

```bash
# Add RESEND_API_KEY to openclaw.json sandbox env
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  'jq ".agents.defaults.sandbox.docker.env.RESEND_API_KEY = \"re_xxxxxxxxx\"" \
  ~/.openclaw/openclaw.json > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json'

# Add to .env for gateway
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  'echo "RESEND_API_KEY=re_xxxxxxxxx" >> ~/.openclaw/.env'

# Restart gateway
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  'systemctl --user restart openclaw-gateway.service'
```

### Phase 3: Custom Skill

```bash
# Create skill directory
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  'mkdir -p ~/.openclaw/skills/resend-email'

# Write SKILL.md (content in FEATURES.md)
# Write reference docs with curl examples
```

### Phase 4: n8n Webhook (on VPS 165.22.139.214)

```bash
# Install community node
# In n8n: Settings > Community Nodes > Install > n8n-nodes-resend

# Create webhook workflow:
# Webhook node (POST /resend-webhook) -> verify signature -> process -> relay
```

## Sources

- [Resend API Reference](https://resend.com/docs/api-reference/introduction) -- API endpoints, auth, request format
- [Resend Node.js SDK (GitHub)](https://github.com/resend/resend-node) -- SDK v6.9.2, not used but referenced
- [Resend MCP Server (GitHub)](https://github.com/resend/mcp-send-email) -- MCP tools list, NOT recommended for OpenClaw
- [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests) -- Svix headers, signing secret
- [Resend Webhook Event Types](https://resend.com/docs/dashboard/webhooks/event-types) -- All event types and payload format
- [Resend Receiving Emails](https://resend.com/docs/dashboard/receiving/introduction) -- Inbound email setup, MX records
- [Resend Domain Management](https://resend.com/docs/dashboard/domains/introduction) -- DNS records, SPF/DKIM
- [Resend Pricing](https://resend.com/pricing) -- Free tier: 3,000/mo, 100/day
- [n8n-nodes-resend (GitHub)](https://github.com/jonathanferreyra/n8n-nodes-resend) -- Community node, API coverage
- [n8n Webhook Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) -- Webhook receiver config
- [Svix npm package](https://www.npmjs.com/package/svix) -- v1.84.1, webhook verification
- [OpenClaw MCP Limitations (Gist)](https://gist.github.com/Rapha-btc/527d08acc523d6dcdb2c224fe54f3f39) -- mcpServers silently ignored
- [OpenClaw MCP Feature Request #13248](https://github.com/openclaw/openclaw/issues/13248) -- Native MCP support not yet implemented
- [OpenClaw Skills Docs](https://docs.openclaw.ai/tools/skills) -- Skill format, env vars, metadata
- [react-email-skills (ClawHub)](https://playbooks.com/skills/openclaw/skills/react-email-skills) -- Published skill, not recommended for this deployment
