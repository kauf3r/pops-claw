---
phase: 20-inbound-email-infrastructure
verified: 2026-02-17T00:00:00Z
status: human_needed
score: 12/13 must-haves verified
human_verification:
  - test: "Send email to test@mail.andykaufman.net from an external account"
    expected: "Bob posts notification to #popsclaw within ~60 seconds containing sender, subject, body preview, and timestamp"
    why_human: "E2E pipeline spans 3 remote systems (Resend, VPS n8n, EC2 OpenClaw) — automated checks cannot fire a real Resend webhook or observe Slack channel output"
---

# Phase 20: Inbound Email Infrastructure Verification Report

**Phase Goal:** Gateway bind change + hooks config + VPS Caddy route + n8n webhook workflow + Resend webhook + MX record + E2E test
**Verified:** 2026-02-17
**Status:** human_needed (all automated checks pass; E2E behavior requires human confirmation)
**Re-verification:** No — initial verification

---

## Verification Approach

This is a pure infrastructure phase. All changes were made to remote servers (EC2 and VPS). There are no local code artifacts to inspect with file checks or grep. Verification is based on:

1. SUMMARY documentation of observed command output and test results
2. Cross-referencing claimed test results against known failure modes
3. Identifying gaps or contradictions between plan intent and documented outcomes
4. Flagging items that require human confirmation of live system state

---

## Goal Achievement

### Observable Truths — Plan 20-01

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Gateway listens on Tailscale IP (100.72.143.9:18789) instead of localhost | VERIFIED | 20-01-SUMMARY: "Gateway now listens on 100.72.143.9:18789 (Tailscale IP) instead of 127.0.0.1"; STATE.md: "Gateway bind: tailnet (100.72.143.9:18789, changed from loopback in Phase 20-01)" |
| 2 | POST to /hooks/agent with hooks token returns 202 | VERIFIED | 20-01-SUMMARY: "Hooks endpoint accepts authenticated POSTs returning 202 from EC2, VPS, and Mac" |
| 3 | UFW allows 18789 from 100.64.0.0/10 | VERIFIED | 20-01-SUMMARY: "UFW rule for 18789 from 100.64.0.0/10 confirmed pre-existing" |
| 4 | VPS can reach EC2 gateway over Tailscale | VERIFIED | 20-01-SUMMARY: "VPS (100.105.251.99) confirmed on same Tailscale network, can reach EC2 hooks endpoint"; test result 202 from VPS documented |
| 5 | Caddy on VPS routes /webhook/resend to n8n with IP restriction | VERIFIED (with correction) | 20-01-SUMMARY: route added as /webhooks/resend initially. 20-02-SUMMARY corrects: "Caddy path corrected from /webhooks/resend to /webhook/resend (singular)" to match n8n webhook path. Final state: /webhook/resend with IP restriction active. |
| 6 | SSH tunnel uses Tailscale IP for dashboard access | VERIFIED | 20-01-SUMMARY: "SSH tunnel must now target Tailscale IP: ssh -L 3000:100.72.143.9:18789"; documented in both SUMMARY and STATE.md |

**Score 20-01:** 6/6 truths verified

### Observable Truths — Plan 20-02

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Resend webhook POST to VPS triggers n8n workflow | VERIFIED | 20-02-SUMMARY: "n8n workflow 'Resend Inbound Email Relay' (ID: 1XwpGnGro0NYtOjE) active on VPS"; E2E test documented as passing |
| 2 | n8n verifies Svix signature and rejects invalid payloads with 401 | VERIFIED | 20-02-SUMMARY: "Svix signature verification with HMAC-SHA256 (rejects unsigned/invalid webhooks with 401)"; deviation doc confirms crypto access blocker was fixed via NODE_FUNCTION_ALLOW_BUILTIN=crypto |
| 3 | n8n fetches first ~200 chars of email body via Resend API | VERIFIED | 20-02-SUMMARY: "Body preview fetched via Resend Received Emails API (GET /emails/receiving/{id})"; deviation doc confirms full_access key scope blocker was resolved |
| 4 | n8n forwards email metadata + body preview to OpenClaw /hooks/agent | VERIFIED | 20-02-SUMMARY: "Metadata + preview forwarded to OpenClaw /hooks/agent → Bob posts to #popsclaw"; node 6 (POST to OpenClaw) documented in workflow nodes list |
| 5 | Bob posts inbound email summary to #popsclaw | HUMAN NEEDED | 20-02-SUMMARY states "E2E verified: email from Gmail → Bob notification in #popsclaw with body preview" — but this is a live Slack channel output claim that cannot be confirmed from planning docs alone |
| 6 | MX record routes emails to Resend inbound SMTP | VERIFIED | 20-02-SUMMARY: "MX record verified: mail.andykaufman.net → 10 inbound-smtp.us-east-1.amazonaws.com"; matches expected Resend inbound SMTP pattern |
| 7 | Full email body available on demand via Resend API | VERIFIED | 20-02-SUMMARY confirms full_access Resend API key deployed to n8n, OpenClaw config, and OpenClaw .env; the hooks message payload includes the email_id and curl command for Bob to fetch full body |

**Score 20-02:** 6/7 truths verified (1 human_needed)

**Overall Score:** 12/13 truths verified (one requires human confirmation)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| Gateway bind=tailnet in openclaw.json (EC2) | Tailscale IP bind change | VERIFIED | 20-01-SUMMARY documents `gateway.bind` changed from loopback to tailnet; STATE.md confirms |
| Hooks endpoint in openclaw.json (EC2) | /hooks endpoint with dedicated token (982cbc4b...) | VERIFIED | 20-01-SUMMARY: existing hooks config kept; hooks token documented in KEY INFORMATION section |
| UFW rule on EC2 | 18789 allowed from 100.64.0.0/10 | VERIFIED | Pre-existing rule confirmed by SUMMARY |
| Caddyfile on VPS | /webhook/resend route with IP restriction to n8n:5678 | VERIFIED | 20-01 added route, 20-02 corrected path from /webhooks/ to /webhook/ (singular); final state documented |
| n8n workflow on VPS | "Resend Inbound Email Relay" — 8 nodes, Svix verification, active | VERIFIED | 20-02-SUMMARY documents all 8 nodes, workflow ID (1XwpGnGro0NYtOjE), active status |
| n8n .env on VPS | NODE_FUNCTION_ALLOW_BUILTIN=crypto, RESEND_FULL_API_KEY, RESEND_WEBHOOK_SECRET, OPENCLAW_HOOKS_TOKEN | VERIFIED | 20-02-SUMMARY documents all env vars added; crypto env var required for Svix HMAC |
| MX record for mail.andykaufman.net | MX 10 inbound-smtp.us-east-1.amazonaws.com | VERIFIED | 20-02-SUMMARY documents MX record confirmed |
| OpenClaw .env (EC2) | RESEND_API_KEY updated to full_access key | VERIFIED | 20-02-SUMMARY: "RESEND_API_KEY updated to full_access key in n8n .env + OpenClaw config + OpenClaw .env" |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Resend webhook | VPS Caddy /webhook/resend | HTTPS POST with Svix headers | VERIFIED | Resend webhook endpoint configured; Caddy route active with Resend IP restriction (4 IPs); path corrected to /webhook/resend (singular) |
| VPS Caddy | n8n:5678 | Docker reverse_proxy | VERIFIED | 20-01-SUMMARY: "Used Docker service name n8n:5678" — deviation from plan's localhost:5678, correctly adapted for Docker network topology |
| n8n Code node | Resend Received Emails API | GET /emails/receiving/{id} with full_access key | VERIFIED | 20-02-SUMMARY confirms full_access key configured, fetch body preview node operational |
| n8n HTTP Request node | EC2 /hooks/agent | POST over Tailscale with hooks token | VERIFIED | VPS-to-EC2 connectivity verified (202 response in Task 2 of 20-01), n8n workflow node 6 documented as POSTing to http://100.72.143.9:18789/hooks/agent |
| OpenClaw hooks | #popsclaw | Bob agent turn with deliver: true | HUMAN NEEDED | The hooks payload includes deliver:true and channel:#popsclaw — mechanism is documented but actual Slack delivery requires live system observation |

---

## Requirements Coverage

No separate REQUIREMENTS.md exists for v2.2 milestone. Requirements were tracked informally in plan frontmatter.

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|---------|
| gateway-bind-tailnet | 20-01 | SATISFIED | Gateway bind changed to tailnet, ss output showed 100.72.143.9:18789 |
| hooks-endpoint-dedicated-token | 20-01 | SATISFIED | Existing dedicated hooks token (982cbc4b...) retained and verified |
| ufw-sg-defense-in-depth | 20-01 | SATISFIED | UFW rule confirmed pre-existing; SG restricted to Tailscale CGNAT |
| caddy-webhook-route | 20-01 | SATISFIED | Caddy route added with IP restriction; path corrected to /webhook/resend in 20-02 |
| vps-tailscale-connectivity | 20-01 | SATISFIED | VPS Tailscale IP 100.105.251.99 confirmed; 202 response from VPS to EC2 hooks |
| svix-signature-verification | 20-02 | SATISFIED | HMAC-SHA256 verification with crypto builtin; rejects unsigned payloads with 401 |
| n8n-webhook-workflow | 20-02 | SATISFIED | 8-node workflow active (ID: 1XwpGnGro0NYtOjE) |
| two-step-email-read | 20-02 | SATISFIED | Metadata in webhook + full body via Resend API on demand |
| email-to-slack-bridging | 20-02 | SATISFIED (documented) | Hooks deliver:true to #popsclaw; E2E summary claims success |
| mx-record-inbound | 20-02 | SATISFIED | MX 10 inbound-smtp.us-east-1.amazonaws.com confirmed |
| resend-webhook-secret | 20-02 | SATISFIED | whsec_ signing secret from Resend dashboard injected into n8n as RESEND_WEBHOOK_SECRET |

---

## Anti-Patterns Found

No local code files were created or modified in this phase. All changes were remote server configuration. No anti-pattern scan applicable to local repository.

Remote-side anti-patterns documented in SUMMARY deviations:

| Location | Issue | Severity | Resolution |
|----------|-------|----------|------------|
| n8n Code node (initial) | Workflow connections incorrect — Verify Svix routing to Respond 200, bypassing pipeline | Blocker | Fixed by correcting workflow connections |
| n8n .env (initial) | crypto builtin not allowed in Code node sandbox | Blocker | Fixed by NODE_FUNCTION_ALLOW_BUILTIN=crypto + container recreate |
| n8n Code node (initial) | Raw body read from wrong path (json.body vs binary.data.data) | Blocker | Fixed: Buffer.from(item.binary.data.data, 'base64').toString('utf-8') |
| Resend API key (initial) | Sending-only key used — /emails/receiving returned empty | Blocker | Fixed: new full_access key created and deployed |
| Caddyfile (20-01) | Path /webhooks/resend (plural) didn't match n8n /webhook/resend (singular) | Minor | Fixed in 20-02: Caddyfile updated and Caddy reloaded |

All 5 blocking issues were identified and resolved before E2E test. No unresolved blockers remain.

---

## Notable Decisions and Deviations

1. **Hooks token retained, not regenerated.** Pre-existing 982cbc4b... token kept to avoid breaking gmail hooks integration. This is correct behavior — the token was already separate from gateway auth.

2. **Caddy Docker service name.** Plan said `reverse_proxy localhost:5678`; actual setup used `reverse_proxy n8n:5678` (Docker network service name). Correct adaptation — Caddy runs inside Docker.

3. **Caddy path correction.** Plan specified `/webhooks/resend` (plural); n8n webhook path is `/webhook/resend` (singular). Corrected in 20-02. Final state is consistent.

4. **Container recreate requirement.** `docker compose restart` does not propagate new env vars into running containers. `docker compose up -d --force-recreate` required. Documented in STATE.md and MEMORY.md for future reference.

5. **Postgres direct workflow modification.** n8n API required authentication that wasn't configured. Complex Code node modifications were applied via Python script → SCP → Postgres direct update. Unusual but effective.

6. **Full_access Resend key scope.** Initial API key lacked receiving access. New full_access key replaces it across n8n, OpenClaw config, and OpenClaw .env — consolidates send + receive into single key.

---

## Human Verification Required

### 1. Live Pipeline E2E Confirmation

**Test:** Send an email from any external account to any address @mail.andykaufman.net (e.g., test@mail.andykaufman.net). Wait up to 60 seconds.

**Expected:** Bob posts a notification to #popsclaw containing:
- Sender email address
- Subject line
- First ~200 characters of body
- Timestamp

**Why human:** The E2E path spans 3 systems that cannot be tested programmatically from this repo: (1) Resend receiving + webhook firing, (2) VPS n8n workflow execution, (3) EC2 OpenClaw hooks + Bob's Slack delivery. SUMMARY claims E2E passed, but live confirmation validates nothing has drifted since the test.

### 2. Svix Rejection Still Active

**Test:** From VPS terminal, POST to the webhook endpoint without Svix headers:
```
curl -s -o /dev/null -w "%{http_code}" -X POST https://n8n.andykaufman.net/webhook/resend -H "Content-Type: application/json" -d '{"type":"email.received"}'
```

**Expected:** 401 response (Svix verification rejects unsigned payload)

**Why human:** Confirms Svix Code node is still the active code path (not bypassed) and crypto builtin is still enabled in n8n container after any subsequent restarts.

### 3. Full Body Retrieval on Demand

**Test:** After receiving a test email in step 1, ask Bob in #popsclaw: "Can you fetch the full body of the last inbound email?"

**Expected:** Bob uses the RESEND_API_KEY (full_access) to call `GET /emails/receiving/{email_id}` and returns the complete email body.

**Why human:** Validates the email_id is correctly passed through the pipeline and Bob's sandbox has the full_access API key available.

---

## Gaps Summary

No gaps identified. All 13 observable truths have either been verified against SUMMARY documentation (12) or flagged for human confirmation (1 — live Slack delivery). All 5 blocking deviations identified during execution were resolved. All 11 requirements are satisfied.

The one `human_needed` item (Bob's #popsclaw delivery) is verified by the SUMMARY ("E2E verified: email from Gmail → Bob notification in #popsclaw with body preview") but cannot be confirmed programmatically from this repository context.

---

_Verified: 2026-02-17_
_Verifier: Claude (gsd-verifier)_
