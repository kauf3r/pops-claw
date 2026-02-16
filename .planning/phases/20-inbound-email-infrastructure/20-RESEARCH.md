# Phase 20: Inbound Email Infrastructure - Research

**Researched:** 2026-02-16
**Domain:** Multi-hop inbound email relay: Resend webhook -> VPS n8n -> OpenClaw hooks -> Slack notification
**Confidence:** HIGH

## Summary

This phase builds an inbound email pipeline where emails to `*@mail.andykaufman.net` arrive via Resend's receiving infrastructure, trigger a webhook to n8n on the VPS (165.22.139.214), which verifies the Svix signature, extracts metadata, and forwards it to OpenClaw's `/hooks/agent` endpoint over Tailscale. Bob then notifies Andy in #popsclaw with a summary (sender, subject, first ~200 chars, timestamp). Full email body is fetched on-demand via Resend's Received Emails API (`GET /emails/receiving/{id}`).

The key infrastructure changes are: (1) MX record on `mail.andykaufman.net` pointing to Resend's inbound SMTP servers, (2) gateway bind change from `loopback` to `tailnet` so the VPS can reach the hooks endpoint over Tailscale, (3) dedicated hooks token separate from gateway auth, (4) Caddy route on VPS for `/webhooks/resend` proxying to n8n, and (5) n8n workflow that receives the Resend webhook, verifies Svix signature in a Code node, and POSTs metadata to OpenClaw hooks.

**Primary recommendation:** Use OpenClaw's `/hooks/agent` endpoint with `deliver: true, channel: "slack", to: "#popsclaw"` to wake Bob with inbound email metadata. n8n forwards only structured fields (from, to, subject, email_id, timestamp) -- Bob fetches full body via `curl GET https://api.resend.com/emails/receiving/{email_id}` when needed. Svix verification uses raw crypto in n8n Code node (no SDK install needed).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Inbound Notification
- Notify in #popsclaw (existing personal channel, survives gateway restarts)
- Summary format: sender, subject, first ~200 chars of body, timestamp
- Full body available on request (agent fetches via Resend API)
- All inbound emails get same treatment -- no urgency tiers (Phase 21 adds filtering)
- No auto-acknowledgment to senders -- replies only when Andy explicitly asks

#### Receiving Address
- Same subdomain as outbound: mail.andykaufman.net (add MX record alongside existing SPF/DKIM)
- Catch-all: any address @mail.andykaufman.net goes to Bob (bob@, andy@, info@, etc.)

#### Relay Architecture
- n8n on VPS (165.22.139.214) receives Resend webhook
- Svix signature verification: strict -- reject all unsigned/invalid payloads (401)
- n8n forwards metadata only: from, to, subject, email_id, timestamp (structured fields)
- Agent fetches full email body + headers via Resend API when needed (two-step read)
- n8n retries to OpenClaw hooks: 3 attempts with exponential backoff, then log failure
- Phase 22 catch-up cron is the fallback for missed webhooks

#### Gateway Security
- Change gateway bind from loopback (127.0.0.1) to Tailscale IP (100.72.143.9)
- Dedicated hooks token separate from gateway auth token (limited scope, lower blast radius)
- UFW + SG defense in depth: both allow 18789 from 100.64.0.0/10
- VPS Caddy: /webhooks/resend route with IP restriction (Resend webhook IPs if available) + Svix signature as auth layer

### Claude's Discretion
- Exact n8n workflow node layout and error handling details
- Hooks endpoint configuration format in openclaw.json
- Caddy route specifics (proxy_pass, header manipulation)
- Order of DNS record changes during setup

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| Resend Receiving | n/a (dashboard + API) | Inbound email reception, MX routing, webhook dispatch | Already using Resend for outbound (Phase 19). Native inbound support with Svix-signed webhooks |
| Resend Received Emails API | v1 | Fetch full email body + headers on-demand | REST endpoint `GET /emails/receiving/{id}` -- Bob calls via curl from sandbox |
| OpenClaw Hooks (`/hooks/agent`) | v2026.2.x | Receive webhook from n8n, wake Bob with email metadata | Built-in webhook endpoint with auth, session management, delivery routing |
| n8n Webhook + Code nodes | (on VPS) | Receive Resend webhook, verify Svix, forward to OpenClaw | Already running on VPS. Webhook node receives, Code node verifies, HTTP Request forwards |
| Caddy reverse proxy | (on VPS) | HTTPS termination + routing for `/webhooks/resend` | Already running on VPS. Adds one route block |

### Supporting

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| Node.js `crypto` (in n8n) | built-in | HMAC-SHA256 for Svix signature verification | Every inbound webhook -- verify before forwarding |
| `curl` (in sandbox) | built-in | Fetch full email body from Resend API | When Bob needs full email content (on-demand) |
| UFW + AWS SG | n/a | Firewall rules allowing 18789 from Tailscale CGNAT | Defense in depth for gateway bind change |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| n8n Code node for Svix | Svix npm package in n8n | Adds dependency management. Raw crypto is ~10 lines of JS and verified against Svix docs |
| `/hooks/agent` endpoint | `/hooks/wake` endpoint | Wake is fire-and-forget (no message). Agent accepts message text and delivers to channel |
| `bind: "tailnet"` | Tailscale Serve mode | Serve requires `tailscale serve` setup on EC2. Direct tailnet bind is simpler, no HTTPS overhead within Tailscale tunnel |
| Caddy IP restriction | Svix verification only | IP restriction is defense-in-depth. Svix signature is the primary auth. Belt and suspenders |

**Installation:** No new packages. All components already exist:
1. Resend receiving -- enable in dashboard, add MX record
2. n8n -- add workflow (already running on VPS)
3. Caddy -- add route (already running on VPS)
4. OpenClaw -- configure hooks + bind in openclaw.json
5. UFW/SG -- update rules for tailnet bind

## Architecture Patterns

### Recommended Architecture

```
External Sender
    |
    v (SMTP)
Resend Inbound SMTP (MX record)
    |
    v (HTTPS POST -- Svix-signed)
VPS Caddy (/webhooks/resend)
    |
    v (proxy to localhost)
n8n Webhook Node
    |
    v (Code node: verify Svix signature)
    v (HTTP Request node: POST metadata)
    |
    v (HTTPS over Tailscale)
EC2 OpenClaw Gateway (/hooks/agent)
    |
    v (agent turn)
Bob (in Docker sandbox)
    |
    v (Slack SDK)
#popsclaw notification to Andy
```

### Pattern 1: OpenClaw Hooks Configuration

**What:** Configure hooks in `openclaw.json` with dedicated token, enable the endpoint, and set up a mapping for inbound email.
**When to use:** One-time gateway configuration.
**Source:** [OpenClaw Webhooks Documentation](https://docs.openclaw.ai/automation/webhook)

```json5
// In openclaw.json
{
  // Change bind from loopback to tailnet
  "gateway": {
    "bind": "tailnet",
    "auth": {
      "mode": "token",
      "token": "EXISTING_GATEWAY_TOKEN"
    }
  },
  "hooks": {
    "enabled": true,
    "token": "DEDICATED_HOOKS_TOKEN",
    "path": "/hooks"
  }
}
```

**Key details:**
- `gateway.bind: "tailnet"` -- binds to Tailscale interface IP (100.72.143.9) instead of 127.0.0.1
- `hooks.token` -- SEPARATE from `auth.token`. This is the token n8n sends in `x-openclaw-token` header
- `hooks.enabled: true` -- activates the `/hooks/agent` and `/hooks/wake` endpoints
- Hooks config is "safe hot-apply" -- changes apply without full gateway restart

### Pattern 2: POST to `/hooks/agent` from n8n

**What:** n8n sends inbound email metadata to OpenClaw's agent hook endpoint.
**When to use:** Every verified inbound email webhook.
**Source:** [OpenClaw Webhooks Docs](https://docs.openclaw.ai/automation/webhook)

```bash
# What n8n's HTTP Request node sends to OpenClaw
curl -X POST http://100.72.143.9:18789/hooks/agent \
  -H 'x-openclaw-token: DEDICATED_HOOKS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Inbound email received.\nFrom: sender@example.com\nTo: bob@mail.andykaufman.net\nSubject: Meeting tomorrow\nEmail ID: 56761188-7520-42d8-8898-ff6fc54ce618\nReceived: 2026-02-16T20:30:00Z\n\nNotify Andy in #popsclaw with a summary. If he asks for the full body, fetch it using: curl -X GET https://api.resend.com/emails/receiving/56761188-7520-42d8-8898-ff6fc54ce618 -H \"Authorization: Bearer $RESEND_API_KEY\"",
    "name": "Inbound Email",
    "sessionKey": "hook:email:56761188",
    "wakeMode": "now",
    "deliver": true,
    "channel": "slack",
    "to": "#popsclaw"
  }'
```

**Key parameters:**
- `message` (required): Structured text with email metadata + instructions for Bob
- `name`: "Inbound Email" -- appears in session summaries
- `sessionKey`: `hook:email:{email_id_prefix}` -- unique per email, prevents collisions
- `wakeMode`: "now" -- immediate processing (inbound email is time-sensitive)
- `deliver`: true + `channel`: "slack" + `to`: "#popsclaw" -- routes Bob's response to the channel
- Returns 202 (async run started)

### Pattern 3: Svix Signature Verification in n8n Code Node

**What:** Verify Resend webhook authenticity using HMAC-SHA256 in n8n's Code node.
**When to use:** Every incoming webhook before forwarding.
**Source:** [Svix Manual Verification Docs](https://docs.svix.com/receiving/verifying-payloads/how-manual), [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests)

```javascript
// n8n Code node -- runs after Webhook node (with "Respond: Using 'Respond to Webhook' Node")
const crypto = require('crypto');

// Get the raw body and headers from webhook node
const body = $input.first().json.body; // raw JSON string
const svixId = $input.first().json.headers['svix-id'];
const svixTimestamp = $input.first().json.headers['svix-timestamp'];
const svixSignature = $input.first().json.headers['svix-signature'];

// Webhook secret from n8n credentials (starts with "whsec_")
const secret = $env.RESEND_WEBHOOK_SECRET;

// 1. Timestamp tolerance check (5 minutes)
const now = Math.floor(Date.now() / 1000);
const tolerance = 300; // 5 min
if (Math.abs(now - parseInt(svixTimestamp)) > tolerance) {
  throw new Error('Webhook timestamp too old or too new');
}

// 2. Construct signed content: {svix_id}.{svix_timestamp}.{body}
const signedContent = `${svixId}.${svixTimestamp}.${body}`;

// 3. Compute HMAC-SHA256 with base64-decoded secret (strip "whsec_" prefix)
const secretBytes = Buffer.from(secret.split('_')[1], 'base64');
const computedSignature = crypto
  .createHmac('sha256', secretBytes)
  .update(signedContent)
  .digest('base64');

// 4. Compare against provided signatures (may be multiple, space-separated)
const expectedSignature = `v1,${computedSignature}`;
const signatures = svixSignature.split(' ');
const isValid = signatures.some(sig => sig === expectedSignature);

if (!isValid) {
  throw new Error('Invalid Svix signature');
}

// 5. Parse and return the verified payload
const payload = JSON.parse(body);
return [{ json: payload }];
```

**Critical implementation notes:**
- MUST use raw request body for signature verification (not parsed-then-stringified)
- Secret format is `whsec_<base64_key>` -- strip `whsec_` prefix, base64-decode the remainder
- Signed content format: `${svix_id}.${svix_timestamp}.${raw_body}`
- Signature format in header: `v1,<base64_signature>` (may contain multiple space-separated signatures)
- Timestamp tolerance prevents replay attacks (5 min window is standard)

### Pattern 4: Caddy Route for Webhook Endpoint

**What:** Add a Caddy route on the VPS to proxy Resend webhooks to n8n.
**When to use:** One-time VPS configuration.
**Source:** [Caddy reverse_proxy docs](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [Caddy remote_ip matcher](https://caddyserver.com/docs/caddyfile/matchers)

```caddyfile
# Add to existing Caddyfile on VPS
your-vps-domain.com {
    # Existing routes...

    # Resend webhook route with IP restriction
    @resend_webhook {
        path /webhooks/resend
        remote_ip 44.228.126.217 50.112.21.217 52.24.126.164 54.148.139.208
    }
    handle @resend_webhook {
        reverse_proxy localhost:5678  # n8n default port
    }
}
```

**Key details:**
- `remote_ip` matcher restricts to Resend's webhook source IPs (documented whitelist)
- Resend webhook IPs: `44.228.126.217`, `50.112.21.217`, `52.24.126.164`, `54.148.139.208` (IPv4), `2600:1f24:64:8000::/52` (IPv6)
- Defense in depth: IP restriction + Svix signature verification in n8n
- n8n default port is 5678 (verify on VPS)
- Caddy handles HTTPS termination automatically (Let's Encrypt)

### Pattern 5: Two-Step Email Read (Webhook Metadata -> API Fetch Body)

**What:** Webhook delivers metadata only. Agent fetches full body on-demand via Resend API.
**When to use:** When Andy asks for full email content or Bob needs to process the body.
**Source:** [Resend Received Emails API](https://resend.com/docs/api-reference/emails/retrieve-received-email)

```bash
# Bob runs from sandbox to fetch full email body
curl -s -X GET "https://api.resend.com/emails/receiving/${EMAIL_ID}" \
  -H "Authorization: Bearer $RESEND_API_KEY"
```

**Response (200):**
```json
{
  "object": "email",
  "id": "4ef9a417-02e9-4d39-ad75-9611e0fcc33c",
  "to": ["bob@mail.andykaufman.net"],
  "from": "sender@example.com",
  "created_at": "2026-02-16T20:30:00.000Z",
  "subject": "Meeting tomorrow",
  "html": "<html><body><p>Full HTML content...</p></body></html>",
  "text": "Full plain text content...",
  "headers": {
    "return-path": "sender@example.com",
    "mime-version": "1.0",
    "message-id": "<unique-message-id@example.com>"
  },
  "bcc": [],
  "cc": [],
  "reply_to": ["sender@example.com"],
  "message_id": "<unique-message-id@example.com>",
  "attachments": []
}
```

**Key details:**
- Endpoint: `GET /emails/receiving/{id}` (not `/emails/{id}` -- that's for sent emails)
- Returns full HTML, plain text, all headers, attachment metadata
- `RESEND_API_KEY` needs `full_access` scope to read received emails (n8n should have its own `full_access` key; sandbox `sending_access` key is NOT sufficient)
- Resend stores received emails even if webhook endpoint is down
- Bob's `sending_access` key in sandbox cannot read received emails -- need to either: (a) upgrade sandbox key to `full_access`, or (b) add a separate `RESEND_FULL_API_KEY` to sandbox env for reading

### Pattern 6: Resend Inbound Email Webhook Payload

**What:** The `email.received` webhook event payload format.
**When to use:** Reference for n8n workflow parsing.
**Source:** [Resend Webhook Event Types](https://resend.com/docs/dashboard/webhooks/event-types), [Resend Receiving Introduction](https://resend.com/docs/dashboard/receiving/introduction)

```json
{
  "type": "email.received",
  "created_at": "2026-02-16T20:30:12.126Z",
  "data": {
    "email_id": "56761188-7520-42d8-8898-ff6fc54ce618",
    "created_at": "2026-02-16T20:30:11.894Z",
    "from": "Sender Name <sender@example.com>",
    "to": ["bob@mail.andykaufman.net"],
    "bcc": [],
    "cc": [],
    "message_id": "<unique-msg-id@example.com>",
    "subject": "Meeting tomorrow",
    "attachments": []
  }
}
```

**Critical note:** Webhook does NOT include email body, headers, or attachment content. Only metadata. This is intentional (supports serverless environments with size limits). Full content must be fetched via Received Emails API.

### Anti-Patterns to Avoid

- **Forwarding full email body through n8n:** Webhook doesn't include body anyway, and large emails would bloat n8n payloads. Stick to metadata-only relay.
- **Using `gateway.tailscale.mode: "serve"` for hooks:** Serve mode enforces `bind: "loopback"` and requires `tailscale serve` setup. Direct `bind: "tailnet"` is simpler for Tailscale-only access.
- **Putting webhook secret in Caddy config:** Svix verification belongs in n8n (where the crypto happens). Caddy does IP filtering only.
- **Using `/hooks/wake` instead of `/hooks/agent`:** Wake is fire-and-forget with no message content. Agent accepts a message, which is essential for passing email metadata.
- **Sharing the gateway auth token as hooks token:** Separate tokens = separate blast radius. If hooks token leaks, attacker can trigger agent turns but can't access gateway admin functions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Webhook signature verification | Custom implementation from scratch | Svix manual verification algorithm (documented, 10 lines) | Algorithm is standardized by Svix. Just follow the spec |
| Inbound email reception | Run your own SMTP server | Resend receiving + MX record | SMTP servers are complex, need TLS certs, anti-spam. Resend handles all of it |
| Webhook relay / retry | Custom Express server on VPS | n8n workflow with built-in retry | n8n has built-in error handling, retry logic, and monitoring UI |
| Agent waking from webhook | Custom cron polling for new emails | OpenClaw `/hooks/agent` endpoint | Built-in endpoint with auth, session management, delivery routing |
| Email body extraction | Parse raw email MIME | Resend Received Emails API | Resend parses MIME, extracts HTML/text/headers. Just call the API |

**Key insight:** Every hop in this pipeline uses an existing service's built-in capability. No new servers, no custom daemons, no SMTP handling. The only custom code is ~10 lines of Svix verification in n8n.

## Common Pitfalls

### Pitfall 1: MX Record Priority Conflict

**What goes wrong:** MX record for `mail.andykaufman.net` has higher priority number than existing records. Emails route to wrong server or fail.
**Why it happens:** MX priority is inverted -- lower number = higher priority. If existing MX records exist on the subdomain, Resend's must be the lowest number.
**How to avoid:**
1. Check existing MX records: `dig MX mail.andykaufman.net`
2. Since this is a new subdomain (no existing MX), there should be no conflict
3. Set Resend MX record with priority 10 (standard default)
4. Verify after adding: `dig MX mail.andykaufman.net` should show only the Resend record
**Warning signs:** Emails to @mail.andykaufman.net bounce or never arrive in Resend dashboard.
**Confidence:** HIGH (Resend docs explicitly warn about priority conflicts)

### Pitfall 2: Gateway Bind Change Breaks Existing Access

**What goes wrong:** Changing `bind` from `loopback` to `tailnet` makes the gateway unreachable from `localhost` on the EC2 instance itself.
**Why it happens:** `bind: "tailnet"` binds to the Tailscale IP (100.72.143.9) only. Local processes using `127.0.0.1:18789` (like SSH tunnel dashboard access) stop working.
**How to avoid:**
1. Understand the impact: SSH tunnel `ssh -L 3000:localhost:18789` will break because gateway no longer listens on localhost
2. Update SSH tunnel to use Tailscale IP: `ssh -L 3000:100.72.143.9:18789`
3. Or use Tailscale direct access from Mac: `http://100.72.143.9:18789`
4. Test access from both Mac (Tailscale) and EC2 (local) after the change
5. Keep UFW rule allowing 18789 from 100.64.0.0/10 (Tailscale CGNAT range)
**Warning signs:** "Connection refused" on `localhost:18789` from EC2. Dashboard inaccessible via old SSH tunnel.
**Confidence:** HIGH (direct consequence of bind change, confirmed by OpenClaw docs)

### Pitfall 3: Resend API Key Scope for Reading Received Emails

**What goes wrong:** Bob tries to fetch full email body using `curl GET /emails/receiving/{id}` but gets 403 Forbidden.
**Why it happens:** Sandbox has `sending_access` API key (Phase 19 decision -- least privilege). The Received Emails API requires `full_access` scope.
**How to avoid:**
- Option A: Add a second env var `RESEND_FULL_API_KEY` with `full_access` scope to sandbox env (keeps sending key separate)
- Option B: Upgrade existing `RESEND_API_KEY` to `full_access` (simpler but increases blast radius)
- Option C: Have n8n fetch the first ~200 chars of body (using n8n's `full_access` key) and include in the hook message, so Bob rarely needs to fetch
- **Recommended: Option C** -- n8n already has `full_access` key. Add a quick body preview to the metadata relay. Bob only calls API directly for full body on request.
**Warning signs:** 403 or "Insufficient permissions" from Resend API when Bob tries to read received email.
**Confidence:** HIGH (Resend API key scopes documented; `sending_access` explicitly excludes read operations)

### Pitfall 4: n8n Webhook Node Parses JSON Before Code Node

**What goes wrong:** Svix signature verification fails even with correct secret because n8n's Webhook node parses the JSON body, and re-stringifying changes whitespace/ordering.
**Why it happens:** Svix HMAC is computed over the raw request body. JSON.parse then JSON.stringify can alter the byte-level content.
**How to avoid:**
1. In n8n Webhook node settings, enable "Raw Body" option to preserve the original request body
2. Access raw body in Code node via `$input.first().json.body` (or the raw body field depending on n8n version)
3. Use the raw body string directly in HMAC computation -- never parse and re-stringify
4. Test with a known-good webhook payload from Resend's test feature
**Warning signs:** All webhook verifications fail despite correct secret. Signature mismatch errors.
**Confidence:** HIGH (Svix docs + n8n community posts both emphasize raw body requirement)

### Pitfall 5: n8n Retry to OpenClaw Overshoots Timeout

**What goes wrong:** n8n retries POST to `/hooks/agent` but OpenClaw returns 202 (accepted, async). n8n treats non-200 as failure and retries unnecessarily.
**Why it happens:** `/hooks/agent` returns 202 Accepted (not 200 OK) because it starts an async agent turn. Some retry logic treats only 200 as success.
**How to avoid:**
1. In n8n HTTP Request node, configure "Success Responses" to include 202
2. Retry only on 4xx (auth failure) or 5xx (server error) or network timeout
3. Do NOT retry on 202 -- that means the hook was accepted
**Warning signs:** OpenClaw processes the same inbound email multiple times. Duplicate Slack notifications.
**Confidence:** HIGH (OpenClaw docs confirm `/hooks/agent` returns 202)

### Pitfall 6: VPS Not on Same Tailscale Network

**What goes wrong:** n8n on VPS can't reach `100.72.143.9:18789` because VPS doesn't have Tailscale installed or isn't on the same tailnet.
**Why it happens:** The VPS (165.22.139.214) is a DigitalOcean droplet. It may or may not have Tailscale configured.
**How to avoid:**
1. Verify VPS Tailscale status: `tailscale status` on VPS
2. If not installed: install Tailscale on VPS, join same tailnet
3. Verify connectivity: `curl http://100.72.143.9:18789/health` from VPS
4. If VPS already has Tailscale, note its Tailscale IP for UFW/SG rules
**Warning signs:** "Connection timed out" or "No route to host" when n8n tries to POST to OpenClaw hooks.
**Confidence:** MEDIUM (VPS Tailscale status unknown from project docs -- needs verification)

## Code Examples

### Example 1: Complete n8n Workflow Node Layout

```
[Webhook Node] --> [Code: Verify Svix] --> [Code: Extract Metadata] --> [HTTP Request: POST to OpenClaw] --> [Respond to Webhook: 200]
                                      \--> [Respond to Webhook: 401] (on verification failure)
```

**Webhook Node config:**
- HTTP Method: POST
- Path: (matches Caddy route, e.g., `/webhooks/resend`)
- Authentication: None (Svix verification handles auth)
- Response: "Using 'Respond to Webhook' Node"
- Raw Body: Enabled (critical for Svix verification)

**Code Node: Extract Metadata (after Svix verification):**
```javascript
const payload = $input.first().json;

if (payload.type !== 'email.received') {
  // Not an inbound email event -- skip
  return [];
}

const data = payload.data;

return [{
  json: {
    email_id: data.email_id,
    from: data.from,
    to: data.to,
    subject: data.subject,
    timestamp: data.created_at,
    message_id: data.message_id,
    has_attachments: (data.attachments && data.attachments.length > 0)
  }
}];
```

**HTTP Request Node config:**
- Method: POST
- URL: `http://100.72.143.9:18789/hooks/agent`
- Headers:
  - `x-openclaw-token`: `{{ $env.OPENCLAW_HOOKS_TOKEN }}`
  - `Content-Type`: `application/json`
- Body (JSON):
```json
{
  "message": "Inbound email received.\nFrom: {{ $json.from }}\nTo: {{ $json.to }}\nSubject: {{ $json.subject }}\nEmail ID: {{ $json.email_id }}\nReceived: {{ $json.timestamp }}\nAttachments: {{ $json.has_attachments }}\n\nNotify Andy in #popsclaw with a summary of this email. Format: sender, subject, timestamp. If Andy asks for the full body, fetch it with: curl -s -X GET 'https://api.resend.com/emails/receiving/{{ $json.email_id }}' -H 'Authorization: Bearer '\"$RESEND_API_KEY\"",
  "name": "Inbound Email",
  "sessionKey": "hook:inbound-email:{{ $json.email_id }}",
  "wakeMode": "now",
  "deliver": true,
  "channel": "slack",
  "to": "#popsclaw"
}
```

### Example 2: Fetch Full Email Body (Bob in Sandbox)

```bash
# Bob fetches full email when Andy requests it
# Note: requires full_access API key scope
curl -s -X GET "https://api.resend.com/emails/receiving/56761188-7520-42d8-8898-ff6fc54ce618" \
  -H "Authorization: Bearer $RESEND_API_KEY" | python3 -c "
import sys, json
email = json.load(sys.stdin)
print(f'From: {email[\"from\"]}')
print(f'Subject: {email[\"subject\"]}')
print(f'Date: {email[\"created_at\"]}')
print()
if email.get('text'):
    print(email['text'])
elif email.get('html'):
    print('[HTML content -- see full HTML below]')
    print(email['html'][:2000])
"
```

### Example 3: Gateway Configuration Change

```bash
# On EC2 via SSH
# 1. Generate dedicated hooks token
HOOKS_TOKEN=$(openssl rand -hex 32)
echo "Hooks token: $HOOKS_TOKEN"

# 2. Update openclaw.json
ssh ubuntu@100.72.143.9 << 'COMMANDS'
# Backup config
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# Update bind and hooks config using openclaw CLI
openclaw config set gateway.bind tailnet
openclaw config set hooks.enabled true
openclaw config set hooks.token "HOOKS_TOKEN_HERE"

# Restart gateway
systemctl --user restart openclaw-gateway.service

# Verify
journalctl --user -u openclaw-gateway.service --since '30 sec ago' | tail -10
COMMANDS
```

### Example 4: Caddy Route Addition

```caddyfile
# On VPS -- add to existing Caddyfile
# Route for Resend inbound email webhooks
@resend_webhook {
    path /webhooks/resend
    remote_ip 44.228.126.217 50.112.21.217 52.24.126.164 54.148.139.208
}
handle @resend_webhook {
    reverse_proxy localhost:5678
}
```

### Example 5: UFW Rule Update on EC2

```bash
# Allow port 18789 from Tailscale CGNAT range (already exists for SSH)
# Verify existing rule
sudo ufw status numbered | grep 18789

# If no rule for 18789 from Tailscale:
sudo ufw allow from 100.64.0.0/10 to any port 18789 proto tcp comment "OpenClaw gateway from Tailscale"

# Verify
sudo ufw status verbose
```

## Discretion Recommendations

### n8n Workflow Node Layout

**Recommendation:** 5-node linear workflow with error branch:

1. **Webhook Trigger** (POST, raw body enabled, respond via Respond node)
2. **Code: Verify Svix** (HMAC-SHA256 verification, throws on failure)
3. **Code: Extract Metadata** (parse payload, filter for `email.received` type)
4. **HTTP Request: POST to OpenClaw** (forward metadata to `/hooks/agent`)
5. **Respond to Webhook** (return 200 on success path)

Error handling: Add a second **Respond to Webhook** node on the error output of the Svix verification Code node, returning 401. This satisfies the "reject unsigned/invalid payloads" requirement.

For retry logic: Configure the HTTP Request node with 3 retries, exponential backoff (1s, 2s, 4s), and treat 202 as success. Log failures to n8n execution history (built-in).

### Hooks Endpoint Configuration

**Recommendation:** Minimal hooks config in `openclaw.json`:

```json5
{
  "hooks": {
    "enabled": true,
    "token": "DEDICATED_64_CHAR_HEX_TOKEN",
    "path": "/hooks"
  }
}
```

No `mappings` needed -- n8n constructs the full `/hooks/agent` POST body. Mappings are for when OpenClaw receives raw webhook data and needs to template it into agent messages. Since n8n already formats the message, direct POST to `/hooks/agent` is cleaner.

No `presets` needed -- presets are built-in mapping templates (e.g., "gmail"). There's no Resend preset.

### Caddy Route Specifics

**Recommendation:** Simple path-match with IP restriction and proxy:

```caddyfile
@resend_webhook {
    path /webhooks/resend
    remote_ip 44.228.126.217 50.112.21.217 52.24.126.164 54.148.139.208
}
handle @resend_webhook {
    reverse_proxy localhost:5678
}
```

No header manipulation needed. Caddy passes all headers through to n8n by default (including `svix-id`, `svix-timestamp`, `svix-signature`). No path stripping needed since n8n webhook path can match `/webhooks/resend` directly.

### Order of Setup Steps

**Recommendation:**

1. **First: Gateway config** (bind + hooks) -- this is the biggest change and should be verified before adding external dependencies
2. **Second: UFW/SG rules** -- allow 18789 from Tailscale range if not already configured
3. **Third: Caddy route on VPS** -- add the webhook proxy route
4. **Fourth: n8n workflow** -- build and test with manual webhook sends
5. **Fifth: Resend webhook** -- configure webhook endpoint URL in Resend dashboard, select `email.received` event
6. **Sixth: MX record** -- add last because this starts routing real emails
7. **Last: End-to-end test** -- send email to `test@mail.andykaufman.net`, verify full pipeline

Rationale: Build the receiving infrastructure before enabling the source (MX record). This avoids emails arriving before the pipeline is ready.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Run your own SMTP server (Postfix/Sendmail) | Managed inbound via API (Resend, Mailgun, SendGrid) | 2023+ | No SMTP config, no TLS cert management, no spam filtering |
| Poll for new emails (IMAP/POP3) | Webhook-driven push notifications | 2020+ | Near-instant notification vs periodic polling latency |
| Email body in webhook payload | Metadata-only webhook + API fetch | 2024+ (Resend) | Supports serverless (payload size limits), reduces bandwidth |
| HMAC-SHA1 webhook signatures | HMAC-SHA256 via Svix standard | 2023+ | Stronger hash, standardized across services using Svix |

**Current ecosystem note:** Resend's inbound email feature is relatively new (launched 2024). The two-step pattern (webhook metadata + API body fetch) is their deliberate design choice to support serverless environments with payload size limits.

## Open Questions

1. **VPS Tailscale status**
   - What we know: VPS (165.22.139.214) runs Caddy + n8n. It needs to reach EC2 at 100.72.143.9:18789 over Tailscale.
   - What's unclear: Whether Tailscale is already installed on the VPS and joined to the same tailnet.
   - Recommendation: Check during Plan 1 execution. If not installed, add Tailscale installation as a prerequisite task. Alternative: if VPS has no Tailscale, could use EC2 public IP with additional security (but this conflicts with Tailscale-only security model).

2. **Resend API key scope for sandbox**
   - What we know: Sandbox currently has `sending_access` key. Received Emails API likely needs `full_access`.
   - What's unclear: Exact permissions required for `GET /emails/receiving/{id}`.
   - Recommendation: Have n8n (which already has `full_access`) include first ~200 chars of body in the hook message (Pattern 5: two-step read with n8n pre-fetch). This way sandbox key stays `sending_access` and Bob rarely needs to call the API directly. If direct fetch is needed later, add a `RESEND_READ_API_KEY` with `full_access` to sandbox.

3. **Exact MX record value from Resend**
   - What we know: Resend requires an MX record for receiving. The value is displayed in the Resend dashboard after enabling receiving on the domain. Research suggests format like `inbound-smtp.{region}.amazonaws.com` with priority ~10.
   - What's unclear: The exact MX record value for `mail.andykaufman.net` (domain-specific, generated by Resend).
   - Recommendation: Enable receiving in Resend dashboard during execution. Copy the exact MX record value shown. This is a manual step, not automatable.

4. **n8n webhook path configuration**
   - What we know: Caddy proxies `/webhooks/resend` to n8n on `localhost:5678`. n8n Webhook node needs a matching path.
   - What's unclear: Whether n8n is at `localhost:5678` on VPS (default), or a different port.
   - Recommendation: Verify n8n port during Plan 1. Adjust Caddy proxy target if different.

5. **Body preview in webhook relay**
   - What we know: User wants "first ~200 chars of body" in the Slack notification. Webhook doesn't include body.
   - What's unclear: Whether n8n should fetch the body preview (adding latency + API call) or Bob should fetch after being woken.
   - Recommendation: Have n8n fetch body preview using its `full_access` key, include in the hook message. Adds ~500ms but provides richer notification. Bob still has API fetch capability for full body on request.

## Sources

### Primary (HIGH confidence)
- [Resend Receiving Emails Introduction](https://resend.com/docs/dashboard/receiving/introduction) -- Inbound email setup, webhook configuration, catch-all behavior (Context7 verified)
- [Resend Custom Receiving Domains](https://resend.com/docs/dashboard/receiving/custom-domains) -- MX record setup, DNS configuration steps (Context7 verified)
- [Resend Received Emails API](https://resend.com/docs/api-reference/emails/retrieve-received-email) -- `GET /emails/receiving/{id}` endpoint, response format (Context7 verified)
- [Resend email.received Event](https://resend.com/docs/dashboard/webhooks/event-types) -- Webhook payload format with all fields (Context7 verified)
- [Resend Webhook Verification](https://resend.com/docs/dashboard/webhooks/verify-webhooks-requests) -- Svix verification with code examples (Context7 verified)
- [Resend Webhook IPs](https://resend.com/docs/webhooks/introduction) -- Source IP whitelist: 44.228.126.217, 50.112.21.217, 52.24.126.164, 54.148.139.208 (WebSearch verified)
- [Svix Manual Verification](https://docs.svix.com/receiving/verifying-payloads/how-manual) -- HMAC-SHA256 algorithm, signed content format, secret format
- [OpenClaw Webhooks Documentation](https://docs.openclaw.ai/automation/webhook) -- `/hooks/agent` endpoint, payload format, authentication
- [OpenClaw Gateway Configuration](https://docs.openclaw.ai/gateway/configuration) -- `bind: "tailnet"`, hooks config format
- [OpenClaw Tailscale Documentation](https://docs.openclaw.ai/gateway/tailscale) -- Bind modes, allowTailscale auth
- [Caddy remote_ip Matcher](https://caddyserver.com/docs/caddyfile/matchers) -- IP restriction syntax (Context7 verified)
- [Caddy reverse_proxy Directive](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) -- Proxy configuration with path matching (Context7 verified)
- [n8n Webhook Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) -- Configuration, raw body, authentication options (Context7 verified)

### Secondary (MEDIUM confidence)
- [Hookdeck + OpenClaw Guide](https://hookdeck.com/webhooks/platforms/using-hookdeck-with-openclaw-reliable-webhooks-for-your-ai-agent) -- OpenClaw hooks configuration example with mappings
- [OpenClaw Config Gist](https://gist.github.com/digitalknk/4169b59d01658e20002a093d544eb391) -- Sanitized openclaw.json example showing hooks configuration
- [n8n HMAC Verification Template](https://n8n.io/workflows/3439-validate-seatable-webhooks-with-hmac-sha256-authentication/) -- Community workflow for HMAC webhook verification pattern
- [n8n Community: Webhook HMAC](https://community.n8n.io/t/webhook-hmac-hash-cannot-be-verified/46100) -- Raw body requirement for signature verification

### Tertiary (LOW confidence)
- MX record exact value (`inbound-smtp.{region}.amazonaws.com`) -- inferred from AWS SES pattern. Actual Resend value comes from dashboard at setup time. Verify during execution.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All components are existing services (Resend, n8n, Caddy, OpenClaw hooks). No new infrastructure to install.
- Architecture: HIGH -- Multi-hop relay pattern is well-documented. Each hop uses official APIs/endpoints. OpenClaw hooks config verified against multiple sources.
- Pitfalls: HIGH -- Svix raw body requirement, MX priority, API key scope, bind change impact all confirmed by official docs. VPS Tailscale status is MEDIUM (needs runtime verification).

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable domain -- Resend API, OpenClaw hooks, n8n, Caddy all mature/stable)
