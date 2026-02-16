# Architecture: Resend Email Integration with OpenClaw

**Domain:** Email send/receive integration for personal AI assistant
**Researched:** 2026-02-16
**Overall confidence:** MEDIUM-HIGH

## System Context

```
CURRENT STATE:
                                    Internet
                                       |
                      +----------------+----------------+
                      |                                 |
              VPS (165.22.139.214)               Resend API
              [n8n + Caddy]                    (resend.com)
              Public HTTPS                          |
                      |                             |
                 Tailscale                     [not yet connected]
                      |
              EC2 (100.72.143.9)
              [OpenClaw Gateway :18789]
              [Docker Sandbox - Bob]
              Tailscale-only, no public IP


PROPOSED STATE:
                                    Internet
                                       |
              +----------+-------------+-------------+
              |          |                           |
     Sender inbox   Resend API               VPS (165.22.139.214)
              |     (resend.com)             [n8n + Caddy]
              |          |                   Public HTTPS
              |    +-----+-----+                  |
              |    |           |                  |
              | Outbound   Inbound           Tailscale
              |  (API)    (webhook)               |
              |    ^          |              EC2 (100.72.143.9)
              |    |          v              [OpenClaw Gateway :18789]
              |    |     n8n receives        [Docker Sandbox - Bob]
              |    |     POST from Resend         |
              |    |          |               +---+---+
              |    |          |               |       |
              |    |     n8n forwards    resend-mcp  hooks
              |    |     over Tailscale  (outbound)  (inbound)
              |    |          |               ^       ^
              |    |          v               |       |
              |    +---- Bob (agent) ---------+-------+
              |          reads email via
              |          Resend API (MCP tool)
              v
         Recipient inbox
```

## Component Boundaries

| Component | Responsibility | Communicates With | New/Modified |
|-----------|---------------|-------------------|--------------|
| Resend API | Email send/receive, DNS, webhooks | Bob (via MCP), n8n (via webhook) | **NEW** external service |
| resend-mcp | MCP server exposing Resend tools to Bob | Bob (stdio), Resend API (HTTPS) | **NEW** MCP server in openclaw.json |
| n8n webhook workflow | Receives Resend inbound webhook, forwards to OpenClaw | Resend (inbound POST), OpenClaw gateway (outbound POST over Tailscale) | **NEW** n8n workflow |
| Caddy | TLS termination, reverse proxy for n8n webhook path | Internet (inbound HTTPS), n8n (proxy target) | **MODIFIED** - add route for webhook path |
| OpenClaw hooks | Receives forwarded email data from n8n, wakes Bob | n8n (inbound POST over Tailscale), Bob (agent wake) | **MODIFIED** - add hook mapping for email |
| Bob (agent) | Processes email notifications, sends replies via MCP tools | resend-mcp (tool calls), hooks (wake trigger) | **MODIFIED** - new email skills |
| OpenClaw config | API key management, MCP server registration | Gateway process, sandbox env | **MODIFIED** - openclaw.json + .env |

## Outbound Email Path (Agent --> Recipient)

**Confidence: HIGH** - Well-documented MCP server pattern.

```
Bob decides to send email
    |
    v
Bob calls resend-mcp tool: send_email
    |  (tool args: to, subject, html/text, from, reply_to, cc, bcc)
    |
    v
resend-mcp process (npx resend-mcp, stdio transport)
    |  uses RESEND_API_KEY env var
    |
    v
Resend API: POST https://api.resend.com/emails
    |
    v
Resend delivers to recipient's mail server
    |
    v
Recipient inbox
```

### resend-mcp MCP Server Configuration

The official `resend-mcp` npm package (MIT licensed, maintained by Resend) provides these tools:

| Tool | Purpose | Key Inputs |
|------|---------|------------|
| send_email | Send email via Resend API | to, subject, html/text, from, reply_to, cc, bcc, attachments, scheduled_at, tags |
| get_email | Get sent email details | email_id |
| list_emails | List sent emails | (pagination) |
| list_received_emails | List inbound emails | (pagination) |
| get_received_email | Get received email content (body, headers) | email_id |
| get_received_email_attachment | Download attachment | email_id, attachment_id |
| create_contact | Create contact in audience | email, first_name, last_name, audience_id |
| list_contacts | List contacts | audience_id |
| create_webhook | Create webhook endpoint | url, events |
| list_domains | List verified domains | - |
| verify_domain | Verify domain DNS | domain_id |

**Configuration in openclaw.json:**

There are two configuration approaches for OpenClaw MCP servers:

### Option A: Native agents.mcp.servers (Recommended if supported in v2026.2.6)

```json
{
  "agents": {
    "defaults": {
      "mcp": {
        "servers": [
          {
            "name": "resend",
            "command": "npx",
            "args": ["-y", "resend-mcp"],
            "env": {
              "RESEND_API_KEY": "${RESEND_API_KEY}",
              "SENDER_EMAIL_ADDRESS": "bob@yourdomain.com"
            }
          }
        ]
      }
    }
  }
}
```

### Option B: MCP Adapter Plugin (if native MCP not available)

```json
{
  "plugins": {
    "entries": {
      "mcp-adapter": {
        "enabled": true,
        "config": {
          "servers": [
            {
              "name": "resend",
              "transport": "stdio",
              "command": "npx",
              "args": ["-y", "resend-mcp"],
              "env": {
                "RESEND_API_KEY": "${RESEND_API_KEY}",
                "SENDER_EMAIL_ADDRESS": "bob@yourdomain.com"
              }
            }
          ]
        }
      }
    }
  }
}
```

**Confidence note:** The Phase 4 verification (2026-02-08) confirmed that OpenClaw v2026.2.6 "doesn't use @modelcontextprotocol MCP servers" and instead uses native tools. However, the MCP adapter plugin and native agents.mcp.servers config are documented features that may have been added in later versions. **This must be verified against the actual installed version before implementation.** The fallback is to NOT use an MCP server and instead create a SKILL.md that wraps `curl` calls to the Resend API directly.

### Sandbox Considerations for resend-mcp

The resend-mcp server runs via `npx` which requires network access (to download the package) and a writable npm cache. Key constraints:

- **Network:** Sandbox uses `network: bridge` -- npx can download packages. OK.
- **Writable FS:** Sandbox FS is read-only. npx writes to `/home/node/.npm/`. This may fail.
- **Workaround if npx fails:** Pre-install `resend-mcp` globally on the host (`npm install -g resend-mcp`), find the binary path, and bind-mount it into the sandbox (same pattern as gh/sqlite3 from Phase 4).
- **Alternative workaround:** The MCP server runs OUTSIDE the sandbox as a gateway-level process. Need to verify if OpenClaw MCP servers run in-sandbox or at gateway level. If gateway-level, no sandbox FS constraint.

## Inbound Email Path (Sender --> Bob)

**Confidence: MEDIUM** - Multiple integration points, each well-documented individually, but the full chain needs validation.

```
Sender sends email to bob@yourdomain.com (or inbound@sub.yourdomain.com)
    |
    v
DNS MX record points to Resend's mail servers
    |
    v
Resend receives and parses email
    |
    v
Resend fires webhook: POST https://your-vps.com/webhooks/resend
    |  Headers: svix-id, svix-timestamp, svix-signature
    |  Body: { type: "email.received", data: { email_id, from, to, subject, created_at } }
    |  NOTE: Body/attachments NOT included in webhook -- only metadata
    |
    v
Caddy (VPS 165.22.139.214) terminates TLS
    |  Route: /webhooks/resend -> n8n:5678
    |
    v
n8n Webhook Node receives POST
    |
    |  n8n workflow steps:
    |  1. [Webhook Trigger] - receive POST, get raw body + headers
    |  2. [Code Node] - verify Svix signature (HMAC-SHA256)
    |  3. [IF Node] - signature valid? continue : reject
    |  4. [Code Node] - extract email_id, from, subject from payload
    |  5. [HTTP Request Node] - POST to OpenClaw gateway over Tailscale
    |
    v
n8n sends: POST http://100.72.143.9:18789/hooks/agent
    |  Headers: { "Authorization": "Bearer <hooks-token>" }
    |  Body: {
    |    "message": "New email received from sender@example.com\nSubject: Hello\nEmail ID: abc123\nUse the resend MCP tool get_received_email to read the full content.",
    |    "name": "Inbound Email",
    |    "agentId": "main",
    |    "sessionKey": "hook:email:abc123",
    |    "wakeMode": "now",
    |    "deliver": true,
    |    "channel": "slack",
    |    "to": "U0CUJ5CAF"
    |  }
    |
    v
OpenClaw hooks endpoint receives, wakes Bob
    |
    v
Bob processes: reads full email body via resend-mcp get_received_email tool
    |  (Resend API: GET /emails/{email_id} returns full body + headers)
    |
    v
Bob notifies Andy via Slack DM with summary
    |  (optionally drafts reply via send_email tool)
```

### Why n8n in the Middle (Not Direct Webhook to OpenClaw)?

The OpenClaw gateway binds to loopback (127.0.0.1:18789) and has no public IP. Resend webhooks require a publicly-accessible HTTPS endpoint. The VPS already runs Caddy with public HTTPS. Options considered:

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **n8n on VPS as relay** | Public HTTPS already working, n8n can verify signatures + transform payloads, visual workflow debugging, rate limiting built-in | Extra hop, n8n must be running | **RECOMMENDED** |
| Caddy reverse proxy direct to EC2 over Tailscale | Simpler, fewer components | No signature verification, no payload transformation, Caddy can't easily do HMAC-SHA256 verification, raw webhook format may not match OpenClaw hooks format | Not recommended |
| Tailscale Funnel on EC2 | Eliminates VPS dependency | Exposes EC2 to internet, requires Tailscale Funnel setup, OpenClaw gateway would need to bind to Tailscale interface | Not recommended for security |
| Resend webhook -> Slack (skip n8n) | Simplest | No Resend-to-Slack integration exists, would need Zapier/Make, adds paid dependency | Not recommended |

### Caddy Configuration Addition (VPS)

```
# Add to existing Caddyfile on VPS
yourdomain.com {
    # Existing n8n routes...

    handle /webhooks/resend {
        reverse_proxy localhost:5678
    }
}
```

Or if n8n uses a dedicated webhook path like `/webhook/resend-inbound`:

```
handle /webhook/* {
    reverse_proxy localhost:5678
}
```

### n8n Workflow Design

**Workflow name:** "Resend Inbound Email Relay"

```
[Webhook Trigger]
    Method: POST
    Path: /webhook/resend-inbound
    Response Mode: Immediately (200 OK)
        |
        v
[Code Node: Verify Svix Signature]
    // Extract headers
    const svixId = $input.first().headers['svix-id'];
    const svixTimestamp = $input.first().headers['svix-timestamp'];
    const svixSignature = $input.first().headers['svix-signature'];
    const rawBody = JSON.stringify($input.first().json);

    // Verify HMAC-SHA256
    const crypto = require('crypto');
    const secret = 'whsec_...' // from n8n credentials store
    const secretBytes = Buffer.from(secret.split('_')[1], 'base64');
    const signedContent = `${svixId}.${svixTimestamp}.${rawBody}`;
    const expectedSignature = crypto
        .createHmac('sha256', secretBytes)
        .update(signedContent)
        .digest('base64');

    // Check timestamp freshness (5 min tolerance)
    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - parseInt(svixTimestamp)) > 300) {
        throw new Error('Webhook timestamp too old');
    }

    return { valid: svixSignature.includes(expectedSignature), ...data };
        |
        v
[IF Node: Signature Valid?]
    true -> continue
    false -> [Stop and Error]
        |
        v
[IF Node: Event Type == email.received?]
    true -> continue
    false -> [No Op] (ignore delivery status events etc.)
        |
        v
[Code Node: Format OpenClaw Message]
    const data = $input.first().json.data;
    return {
        message: `New inbound email received:\n- From: ${data.from}\n- To: ${data.to.join(', ')}\n- Subject: ${data.subject}\n- Email ID: ${data.email_id}\n- Received: ${data.created_at}\n\nUse the get_received_email tool with email_id "${data.email_id}" to read the full email body and attachments.`,
        name: "Inbound Email",
        agentId: "main",
        sessionKey: `hook:email:${data.email_id}`,
        wakeMode: "now",
        deliver: true,
        channel: "slack",
        to: "U0CUJ5CAF"
    };
        |
        v
[HTTP Request Node: Forward to OpenClaw]
    Method: POST
    URL: http://100.72.143.9:18789/hooks/agent
    Headers: { "Authorization": "Bearer <hooks-token>" }
    Body: {{ $json }}
    Timeout: 10s
```

**Confidence note on n8n webhook path:** n8n's webhook paths are configured per-workflow. The WEBHOOK_URL env var on the VPS determines the public base URL. The actual path will be something like `https://yourdomain.com/webhook/resend-inbound`. This must match what's registered in Resend's webhook config.

### OpenClaw Hooks Configuration Addition

Add to `openclaw.json`:

```json
{
  "hooks": {
    "enabled": true,
    "token": "<generate-new-hook-token>",
    "path": "/hooks",
    "defaultSessionKey": "hook:ingress",
    "allowRequestSessionKey": true,
    "allowedSessionKeyPrefixes": ["hook:"],
    "mappings": [
      {
        "match": { "path": "agent" },
        "action": "agent",
        "agentId": "main",
        "deliver": true
      }
    ]
  }
}
```

**Critical consideration:** The gateway binds to loopback (127.0.0.1). The hooks endpoint is part of the gateway HTTP server. For n8n on the VPS to reach it over Tailscale (100.72.143.9:18789), the gateway must ALSO listen on the Tailscale interface, not just loopback.

**Options to solve this:**

| Approach | How | Risk |
|----------|-----|------|
| Change `bind` to `tailscale` | `"bind": "tailscale"` in openclaw.json | Exposes gateway to full Tailscale network (currently only 2 nodes, low risk) |
| Change `bind` to `0.0.0.0` + rely on UFW/SG | Gateway listens on all interfaces, firewall restricts | Higher exposure, but UFW blocks everything except Tailscale CGNAT range |
| SSH tunnel from VPS to EC2 | `ssh -L 18789:localhost:18789 ubuntu@100.72.143.9` | Fragile, needs keepalive, adds complexity |
| **socat/nginx on EC2** | Proxy Tailscale:18789 to localhost:18789 | Extra process to maintain |
| **Keep loopback + use SSH from n8n** | n8n HTTP Request through SSH tunnel | Complex n8n config |

**Recommendation:** Change `bind` from `"loopback"` to `"tailscale"` in openclaw.json. This is the simplest and most secure option. The Tailscale network only has 2 nodes (EC2 + VPS), both controlled by the same user. The gateway already has token auth. UFW + SG both restrict to Tailscale CGNAT range.

## API Key Management

**Confidence: HIGH** - Follows established patterns from Phase 2 (Gmail) and Phase 4 (GitHub).

### Keys Required

| Key | Source | Where to Store | Purpose |
|-----|--------|----------------|---------|
| `RESEND_API_KEY` | Resend Dashboard > API Keys | `~/.openclaw/.env` + `agents.defaults.sandbox.docker.env` in openclaw.json | Authenticate with Resend API (both MCP server and any direct API calls) |
| `RESEND_WEBHOOK_SECRET` | Resend Dashboard > Webhooks > signing secret (whsec_...) | n8n credentials store on VPS | Verify Svix signatures on inbound webhooks |
| `OPENCLAW_HOOKS_TOKEN` | Generate (e.g., `openssl rand -hex 32`) | `hooks.token` in openclaw.json + n8n workflow HTTP Request node auth header on VPS | Authenticate n8n requests to OpenClaw hooks endpoint |

### Env Injection Pattern (Established)

```
~/.openclaw/.env:
    RESEND_API_KEY=re_xxxxx

~/.openclaw/openclaw.json:
    agents.defaults.sandbox.docker.env.RESEND_API_KEY = "${RESEND_API_KEY}"
    (or literal value if ${} interpolation not supported for MCP env)
```

The MCP server process also needs the key. If MCP servers run at the gateway level (not inside sandbox), they inherit from the gateway's EnvironmentFile (`~/.openclaw/.env`). If they run inside sandbox, the key must be in `sandbox.docker.env`.

## DNS Configuration

**Confidence: HIGH** - Standard DNS records, well-documented by Resend.

### For Sending (Required)

Add to your domain's DNS:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| TXT | yourdomain.com | `v=spf1 include:amazonses.com ~all` | SPF (Resend uses SES) |
| CNAME | resend._domainkey.yourdomain.com | (provided by Resend) | DKIM |
| CNAME | (provided by Resend) | (provided by Resend) | DKIM key 2 |
| TXT | _dmarc.yourdomain.com | `v=DMARC1; p=none;` | DMARC |

### For Receiving (Required for Inbound)

**Critical:** If the domain already has MX records (e.g., Google Workspace, personal email), do NOT add Resend's MX record to the root domain. Use a subdomain instead.

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| MX | inbound.yourdomain.com | (provided by Resend, priority 10) | Route inbound email to Resend |

**Receiving address format:** `bob@inbound.yourdomain.com` or `anything@inbound.yourdomain.com`

This avoids disrupting existing email service on the root domain.

## Patterns to Follow

### Pattern 1: Two-Phase Email Read (Webhook Metadata + API Full Content)

Resend webhooks contain only metadata (from, to, subject, email_id) -- NOT the email body. The agent must make a second API call to retrieve full content.

**Why:** Resend designed this for serverless environments with body size limits. It also means the webhook relay (n8n) never handles email bodies, reducing data exposure.

**Implementation:**
1. n8n receives webhook with metadata only
2. n8n forwards metadata to OpenClaw hooks
3. Bob receives wake with email_id
4. Bob calls `get_received_email(email_id)` via MCP tool to get full body
5. Bob processes content and responds

### Pattern 2: Session Key per Email (Multi-turn Threading)

Use `sessionKey: "hook:email:<email_id>"` for each inbound email. This creates an isolated session per email, preventing cross-contamination between different email threads.

For ongoing threads (replies to the same conversation), use `sessionKey: "hook:email:thread:<thread_id>"` where thread_id is derived from the email's In-Reply-To or References header.

### Pattern 3: Bind-Mount for MCP Server Binary (if npx fails)

If the read-only sandbox filesystem prevents npx from caching resend-mcp:
```bash
# On EC2 host:
npm install -g resend-mcp
which resend-mcp  # e.g., /home/ubuntu/.npm-global/bin/resend-mcp

# In openclaw.json, add to agents.defaults.sandbox.docker.binds:
"/home/ubuntu/.npm-global/bin/resend-mcp:/usr/local/bin/resend-mcp:ro"
"/home/ubuntu/.npm-global/lib/node_modules/resend-mcp:/usr/local/lib/node_modules/resend-mcp:ro"
```

Then change the MCP server command from `npx` to the direct path.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Polling Resend API Instead of Webhooks

**What:** Using a cron job to periodically call `list_received_emails` to check for new email.
**Why bad:** Wastes API calls, introduces latency (up to cron interval), misses emails if API is temporarily unavailable during poll window.
**Instead:** Use webhooks for real-time notification. The cron-poll approach is a valid fallback if webhook infrastructure fails.

### Anti-Pattern 2: Passing Full Email Body Through n8n

**What:** Having n8n call the Resend API to fetch full email content, then forward the entire body to OpenClaw hooks.
**Why bad:** Email bodies can be large (HTML, inline images). n8n becomes a data bottleneck. The hooks endpoint message field isn't designed for large payloads. Also exposes email content to an intermediate system unnecessarily.
**Instead:** Pass only metadata through n8n. Let Bob fetch full content directly via MCP tool.

### Anti-Pattern 3: Using Root Domain MX for Resend Inbound

**What:** Adding Resend's MX record alongside existing MX records on the root domain.
**Why bad:** MX record priority conflicts. Either Resend never receives email (if existing MX has lower priority number = higher priority), or existing email service breaks.
**Instead:** Use a subdomain: `inbound.yourdomain.com` with only Resend's MX record.

### Anti-Pattern 4: Reusing Gateway Auth Token for Hooks

**What:** Using the same token for `auth.token` and `hooks.token`.
**Why bad:** Gateway auth token provides full API access. Hook token should be scoped to webhook ingress only.
**Instead:** Generate a separate, dedicated hook token.

## Build Order (Dependency-Aware)

```
Phase 1: Foundation (no external dependencies)
  1a. Create Resend account + API key
  1b. Add/verify sending domain in Resend dashboard (DNS records)
  1c. Add RESEND_API_KEY to ~/.openclaw/.env
  1d. Add RESEND_API_KEY to agents.defaults.sandbox.docker.env in openclaw.json

Phase 2: Outbound Email (depends on 1)
  2a. Configure resend-mcp in openclaw.json (try agents.mcp.servers first)
  2b. Restart gateway
  2c. Test: Bob sends test email via MCP tool
  2d. If MCP config doesn't work, fall back to SKILL.md wrapping curl

Phase 3: Inbound Setup (depends on 1, partially parallel with 2)
  3a. Add inbound subdomain MX record in DNS
  3b. Enable receiving for domain in Resend dashboard
  3c. Wait for MX verification (can take minutes to hours)

Phase 4: Gateway Hooks (depends on 1)
  4a. Generate dedicated hooks token
  4b. Add hooks config to openclaw.json
  4c. Change gateway bind from "loopback" to "tailscale"
  4d. Restart gateway
  4e. Test: curl POST to hooks endpoint from VPS over Tailscale

Phase 5: n8n Webhook Relay (depends on 3, 4)
  5a. Create Resend webhook pointing to VPS URL
  5b. Get webhook signing secret from Resend
  5c. Store signing secret in n8n credentials
  5d. Build n8n workflow (webhook trigger -> verify -> transform -> forward)
  5e. Add Caddy route for webhook path (if not already covered by wildcard)
  5f. Test: send email to inbound address, verify n8n receives webhook

Phase 6: End-to-End Integration (depends on 2, 5)
  6a. Send test email to bob@inbound.yourdomain.com
  6b. Verify: Resend receives -> webhook fires -> n8n processes -> OpenClaw hook triggered -> Bob wakes -> Bob reads full email via MCP -> Bob notifies Andy via Slack
  6c. Test reply: Ask Bob to reply to the test email via send_email tool

Phase 7: Skills and Polish (depends on 6)
  7a. Create email SKILL.md for Bob with protocols (when to read, when to reply, when to summarize)
  7b. Optional: email-check cron as polling fallback
  7c. Optional: email digest cron (daily summary of received emails)
```

## Scalability Considerations

| Concern | Current (Personal Use) | If Email Volume Grows |
|---------|----------------------|----------------------|
| Resend free tier | 3,000 emails/month send, 100/day | Upgrade to Pro ($20/mo for 50K emails) |
| n8n webhook throughput | Single workflow, sequential processing | n8n handles this fine for personal volume |
| OpenClaw hooks | One email at a time, sequential agent processing | Could queue emails if volume becomes an issue |
| Email body storage | Not stored (fetched on-demand from Resend API) | Consider local caching if re-reading is frequent |

## Integration Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP server config format mismatch with installed OpenClaw version | MEDIUM | Blocks outbound | Fallback to SKILL.md with curl-based Resend API calls |
| Gateway bind change breaks existing Slack connection | LOW | Breaks all Bob comms | Slack uses Socket Mode (outbound), not affected by bind change |
| n8n webhook verification fails | LOW | Blocks inbound | Test thoroughly, n8n has built-in debugging |
| Resend MX propagation slow | LOW | Delays inbound | DNS propagation is typically < 1 hour for MX records |
| Read-only sandbox prevents npx resend-mcp | MEDIUM | Blocks MCP server startup | Bind-mount pre-installed binary (established pattern) |
| Webhook replay/duplicate delivery | LOW | Agent processes same email twice | Session key per email_id provides idempotency |

## Sources

- [Resend MCP Server (Official)](https://github.com/resend/resend-mcp) - MIT licensed, maintained by Resend
- [Resend MCP Documentation](https://resend.com/docs/knowledge-base/mcp-server)
- [resend-mcp on npm](https://www.npmjs.com/package/resend-mcp)
- [Resend Receiving Emails](https://resend.com/docs/dashboard/receiving/introduction)
- [Resend Custom Receiving Domains](https://resend.com/docs/dashboard/receiving/custom-domains)
- [Resend Get Email Content](https://resend.com/docs/dashboard/receiving/get-email-content)
- [Resend Inbound Emails Blog](https://resend.com/blog/inbound-emails)
- [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests)
- [Resend Pricing](https://resend.com/pricing)
- [OpenClaw Webhooks Documentation](https://docs.openclaw.ai/automation/webhook)
- [OpenClaw Configuration](https://docs.openclaw.ai/gateway/configuration)
- [OpenClaw MCP Adapter Plugin](https://github.com/androidStern-personal/openclaw-mcp-adapter)
- [Svix Webhook Verification](https://docs.svix.com/receiving/verifying-payloads/how)
- [n8n Webhook Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- Phase 4 MCP Servers verification (internal, 2026-02-08) - confirmed sandbox constraints and bind-mount pattern

---

*Architecture research: 2026-02-16*
