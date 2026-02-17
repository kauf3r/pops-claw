# Phase 20: Inbound Email Infrastructure - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Multi-hop relay pipeline: emails to bob@mail.andykaufman.net arrive via Resend webhook → n8n on VPS → OpenClaw hooks → Bob notified in Slack. Pure infrastructure — no filtering, reply intelligence, or conversation tracking (those are Phase 21).

</domain>

<decisions>
## Implementation Decisions

### Inbound Notification
- Notify in #popsclaw (existing personal channel, survives gateway restarts)
- Summary format: sender, subject, first ~200 chars of body, timestamp
- Full body available on request (agent fetches via Resend API)
- All inbound emails get same treatment — no urgency tiers (Phase 21 adds filtering)
- No auto-acknowledgment to senders — replies only when Andy explicitly asks

### Receiving Address
- Same subdomain as outbound: mail.andykaufman.net (add MX record alongside existing SPF/DKIM)
- Catch-all: any address @mail.andykaufman.net goes to Bob (bob@, andy@, info@, etc.)

### Relay Architecture
- n8n on VPS (165.22.139.214) receives Resend webhook
- Svix signature verification: strict — reject all unsigned/invalid payloads (401)
- n8n forwards metadata only: from, to, subject, email_id, timestamp (structured fields)
- Agent fetches full email body + headers via Resend API when needed (two-step read)
- n8n retries to OpenClaw hooks: 3 attempts with exponential backoff, then log failure
- Phase 22 catch-up cron is the fallback for missed webhooks

### Gateway Security
- Change gateway bind from loopback (127.0.0.1) to Tailscale IP (100.72.143.9)
- Dedicated hooks token separate from gateway auth token (limited scope, lower blast radius)
- UFW + SG defense in depth: both allow 18789 from 100.64.0.0/10
- VPS Caddy: /webhooks/resend route with IP restriction (Resend webhook IPs if available) + Svix signature as auth layer

### Claude's Discretion
- Exact n8n workflow node layout and error handling details
- Hooks endpoint configuration format in openclaw.json
- Caddy route specifics (proxy_pass, header manipulation)
- Order of DNS record changes during setup

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Follow existing patterns:
- Bind-mount pattern for any new tools needed in sandbox
- Reference doc pattern if Bob needs instructions for handling inbound emails
- Same Caddy/n8n stack already running on VPS (165.22.139.214)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-inbound-email-infrastructure*
*Context gathered: 2026-02-16*
