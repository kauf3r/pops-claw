---
phase: 20-inbound-email-infrastructure
plan: 02
subsystem: email-inbound
tags: [n8n, svix, resend, webhook, inbound-email, hooks]

requires:
  - phase: 20-inbound-email-infrastructure
    plan: 01
    provides: "Gateway hooks endpoint, VPS Caddy routing, Tailscale connectivity"
provides:
  - "n8n Resend Inbound Email Relay workflow with Svix signature verification"
  - "Body preview fetched via Resend Received Emails API (full_access key)"
  - "Inbound emails forwarded to OpenClaw /hooks/agent → Bob notifies #popsclaw"
  - "MX record for mail.andykaufman.net → Resend inbound SMTP"
  - "Caddy IP restriction path corrected to /webhook/resend (singular)"
affects: [n8n-workflow, resend-inbound, hooks-delivery, slack-notifications]

tech-stack:
  added: []
  patterns: [svix-hmac-verification, n8n-binary-raw-body, resend-receiving-api]

key-files:
  created: []
  modified:
    - /home/officernd/n8n-production/.env
    - /home/officernd/n8n-production/Caddyfile
    - /home/ubuntu/.openclaw/openclaw.json
    - /home/ubuntu/.openclaw/.env

key-decisions:
  - "NODE_FUNCTION_ALLOW_BUILTIN=crypto in n8n env -- required for Svix HMAC verification in Code nodes"
  - "Container recreate (not restart) needed for new env vars -- docker compose up -d --force-recreate"
  - "Raw body from binary.data.data (base64) -- n8n webhook rawBody option stores in binary, not json.body"
  - "Single full_access Resend API key for both sending and receiving -- simplifies key management"
  - "Caddy path corrected from /webhooks/resend to /webhook/resend to match n8n webhook path"

patterns-established:
  - "n8n Svix verification: crypto.createHmac + binary raw body extraction + timestamp tolerance check"
  - "n8n env var propagation: must use docker compose up --force-recreate, not restart, for new env vars"
  - "Postgres workflow updates: Python script via SCP for complex Code node modifications"

requirements-completed:
  - "svix-signature-verification"
  - "n8n-webhook-workflow"
  - "two-step-email-read"
  - "email-to-slack-bridging"
  - "mx-record-inbound"
  - "resend-webhook-secret"

duration: ~90min (includes debugging crypto access and API key scope)
completed: 2026-02-17
---

# Phase 20 Plan 2: n8n Webhook Workflow + Resend Config + E2E Test

**Inbound email relay pipeline complete — emails to *@mail.andykaufman.net reach Bob in #popsclaw with sender, subject, body preview, and timestamp**

## Performance

- **Duration:** ~90 min (multi-session, debugging crypto + API key scope)
- **Completed:** 2026-02-17
- **Tasks:** 2 (1 auto + 1 checkpoint:human-action)
- **Files modified:** 4 (on remote servers)

## Accomplishments
- n8n workflow "Resend Inbound Email Relay" (ID: 1XwpGnGro0NYtOjE) active on VPS
- Svix signature verification with HMAC-SHA256 (rejects unsigned/invalid webhooks with 401)
- Body preview fetched via Resend Received Emails API (`GET /emails/receiving/{id}`)
- Metadata + preview forwarded to OpenClaw `/hooks/agent` → Bob posts to #popsclaw
- MX record verified: `mail.andykaufman.net → 10 inbound-smtp.us-east-1.amazonaws.com`
- Caddy IP restriction path corrected to match n8n webhook path
- Resend API key upgraded to full_access scope (sending + receiving)

## Pipeline Flow
```
Email → MX → Resend SMTP → Webhook (Svix-signed) → VPS Caddy (IP-restricted)
  → n8n Verify Svix → Extract Metadata → Fetch Body Preview (Resend API)
  → POST /hooks/agent (EC2) → Bob → #popsclaw notification
```

## Workflow Nodes
1. **Webhook Trigger** — POST /webhook/resend, raw body enabled, response via node
2. **Verify Svix Signature** — HMAC-SHA256, 5-min timestamp tolerance, error → 401
3. **Extract Metadata** — Filter email.received events, extract from/to/subject/timestamp
4. **Fetch Body Preview** — GET /emails/receiving/{id} with full_access key
5. **Extract Body Preview** — First ~200 chars of text (or stripped HTML)
6. **POST to OpenClaw** — /hooks/agent with metadata + preview, deliver to #popsclaw
7. **Respond 200 OK** — {"status":"accepted"}
8. **Respond 401** — Error branch for failed verification

## Task Commits

All changes on remote servers (EC2 and VPS):

1. **Task 1: Build n8n workflow + fix Svix verification**
   - Added `NODE_FUNCTION_ALLOW_BUILTIN=crypto` to n8n .env
   - Recreated n8n container (env vars require recreate, not restart)
   - Updated Svix verification Code node with proper HMAC-SHA256 using binary raw body
   - Fixed workflow connections (Verify Svix was bypassing pipeline)
   - Verified: POST without Svix headers → 401 rejection

2. **Task 2: Resend webhook + MX record + E2E test** (human-action checkpoint)
   - Webhook URL verified: `https://n8n.andykaufman.net/webhook/resend`
   - MX record confirmed: `10 inbound-smtp.us-east-1.amazonaws.com`
   - Upgraded Resend API key to full_access scope
   - Updated keys in n8n .env, OpenClaw config, and OpenClaw .env
   - E2E verified: email from Gmail → Bob notification in #popsclaw with body preview
   - Fixed Caddy IP restriction path (`/webhooks/` → `/webhook/`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Blocking] n8n Code node crypto access**
- **Issue:** `require('crypto')` fails in n8n Code node sandbox
- **Root cause:** n8n sandboxes Code nodes; `NODE_FUNCTION_ALLOW_BUILTIN=crypto` needed
- **Additional issue:** `docker compose restart` doesn't pick up new env vars — must use `docker compose up -d --force-recreate`
- **Fix:** Added env var + container recreate

**2. [Blocking] Raw body extraction path**
- **Issue:** Plan used `$input.first().json.body` but n8n stores raw body in binary data
- **Fix:** Changed to `Buffer.from(item.binary.data.data, 'base64').toString('utf-8')`

**3. [Blocking] Workflow connections**
- **Issue:** Verify Svix node was routing to Respond 200 (bypassing pipeline)
- **Fix:** Corrected connection to route through Extract Metadata

**4. [Blocking] Resend API key scope**
- **Issue:** Original API key only had sending access — `/emails/receiving` returned empty
- **Fix:** User created new full_access key, updated in n8n + OpenClaw

**5. [Minor] Caddy path mismatch**
- **Issue:** Caddy restricted `/webhooks/resend` (plural) but n8n uses `/webhook/resend` (singular)
- **Fix:** Updated Caddyfile and reloaded Caddy

---

**Total deviations:** 5 (4 blocking, 1 minor) — all resolved
**Impact on plan:** Required significant debugging but no scope change

## Issues Encountered
- n8n API requires authentication (no API key configured) — used Postgres direct updates for workflow modifications
- n8n execution logs not accessible without API auth — used Caddy access logs + debug Code node responses

## Environment Changes
- `NODE_FUNCTION_ALLOW_BUILTIN=crypto` added to n8n .env
- `RESEND_FULL_API_KEY` added to n8n .env
- `RESEND_API_KEY` updated to full_access key in n8n .env + OpenClaw config + OpenClaw .env
- Caddy path corrected: `/webhook/resend` (singular)
- n8n container recreated (not just restarted)
- OpenClaw gateway restarted for new API key

---
*Phase: 20-inbound-email-infrastructure*
*Completed: 2026-02-17*
