---
phase: 20-inbound-email-infrastructure
plan: 01
subsystem: infra
tags: [gateway, hooks, tailscale, caddy, ufw, bind-change, webhook-routing]

requires:
  - phase: 19-outbound-email-foundation
    provides: "Resend account with verified mail.andykaufman.net domain and API key"
provides:
  - "Gateway bound to Tailscale IP (100.72.143.9:18789) instead of loopback"
  - "Hooks endpoint accepting authenticated POSTs with dedicated token (202 response)"
  - "UFW rule allowing 18789 from Tailscale CGNAT range (100.64.0.0/10)"
  - "VPS-to-EC2 connectivity verified over Tailscale"
  - "Caddy route on VPS for /webhooks/resend with Resend IP restriction"
  - "VPS Tailscale IP: 100.105.251.99"
  - "Webhook URL: https://n8n.andykaufman.net/webhooks/resend"
affects: [n8n-workflow, resend-inbound, hooks-delivery, ssh-tunnel-dashboard]

tech-stack:
  added: []
  patterns: [gateway-tailnet-bind, hooks-dedicated-token, caddy-ip-restricted-webhook-route]

key-files:
  created: []
  modified:
    - /home/ubuntu/.openclaw/openclaw.json
    - /home/officernd/n8n-production/Caddyfile

key-decisions:
  - "Kept existing hooks token (982cbc4b...) rather than generating new one -- already separate from gateway auth token, changing would break gmail hooks"
  - "Caddy route uses Docker service name (n8n:5678) not localhost:5678 since Caddy runs in Docker network"
  - "Resend webhook route added to n8n.andykaufman.net server block (same domain as n8n dashboard)"
  - "SSH tunnel must now use Tailscale IP: ssh -L 3000:100.72.143.9:18789 (not localhost:18789)"

patterns-established:
  - "Gateway tailnet bind: gateway.bind=tailnet for Tailscale-only access with hooks"
  - "Caddy webhook route: named matcher with path + remote_ip for IP-restricted webhook proxying"

requirements-completed:
  - "gateway-bind-tailnet"
  - "hooks-endpoint-dedicated-token"
  - "ufw-sg-defense-in-depth"
  - "caddy-webhook-route"
  - "vps-tailscale-connectivity"

duration: 3min
completed: 2026-02-16
---

# Phase 20 Plan 1: Endpoint Infrastructure Summary

**Gateway bind changed to Tailscale IP with hooks endpoint verified, VPS Caddy routing /webhooks/resend to n8n with Resend IP restriction**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-16T22:09:50Z
- **Completed:** 2026-02-16T22:13:02Z
- **Tasks:** 2
- **Files modified:** 2 (on remote servers)

## Accomplishments
- Gateway now listens on 100.72.143.9:18789 (Tailscale IP) instead of 127.0.0.1
- Hooks endpoint accepts authenticated POSTs returning 202 from EC2, VPS, and Mac
- VPS (100.105.251.99) confirmed on same Tailscale network, can reach EC2 hooks endpoint
- Caddy on VPS routes /webhooks/resend to n8n:5678 with Resend IP whitelist (4 IPs)
- UFW rule for 18789 from 100.64.0.0/10 confirmed pre-existing

## Task Commits

All changes were on remote servers (EC2 and VPS), not in local repository:

1. **Task 1: Gateway bind change + hooks config + UFW update on EC2** - Remote changes only (no local commit)
   - Changed `gateway.bind` from `loopback` to `tailnet` in openclaw.json
   - Verified hooks endpoint (pre-existing, already enabled with dedicated token)
   - Confirmed UFW rule already existed for 18789
   - Restarted gateway, verified listening on 100.72.143.9:18789

2. **Task 2: VPS Tailscale verification + Caddy route for Resend webhooks** - Remote changes only (no local commit)
   - Verified VPS on same Tailscale network (IP: 100.105.251.99)
   - Tested VPS-to-EC2 connectivity (202 response)
   - Added @resend_webhook route to Caddyfile with Resend IP restriction
   - Validated and reloaded Caddy in Docker container

## Files Created/Modified
- `~/.openclaw/openclaw.json` (EC2) - Changed gateway.bind from loopback to tailnet
- `/home/officernd/n8n-production/Caddyfile` (VPS) - Added @resend_webhook route with IP restriction

## Decisions Made
- **Kept existing hooks token** rather than generating a new one. The existing token (982cbc4b...) is already separate from the gateway auth token, and changing it would break the pre-existing gmail hooks integration.
- **Used Docker service name** `n8n:5678` (not `localhost:5678`) in Caddy reverse_proxy since Caddy runs in the same Docker network as n8n.
- **Added route to n8n.andykaufman.net** server block -- the webhook URL will be `https://n8n.andykaufman.net/webhooks/resend`.
- **SSH tunnel must now target Tailscale IP**: `ssh -L 3000:100.72.143.9:18789` since gateway no longer listens on localhost.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Caddy reverse_proxy target adjusted for Docker network**
- **Found during:** Task 2 (Caddy route configuration)
- **Issue:** Plan specified `reverse_proxy localhost:5678` but Caddy runs in Docker, not on host. n8n is on Docker network as service `n8n`.
- **Fix:** Used `reverse_proxy n8n:5678` (Docker service name) matching the existing Caddyfile pattern.
- **Files modified:** /home/officernd/n8n-production/Caddyfile
- **Verification:** Caddy validated and reloaded successfully, 404 from n8n confirms request was proxied.
- **Committed in:** Remote change only.

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary adaptation for Docker-based Caddy setup. No scope creep.

## Issues Encountered
None -- all verification steps passed on first attempt.

## User Setup Required
None -- all infrastructure changes applied directly to remote servers.

## Key Information for Plan 02
- **Hooks token:** 982cbc4b7e29edd465a8f1c411883122142d9f6dc5adc58a
- **Hooks endpoint:** http://100.72.143.9:18789/hooks/agent
- **VPS Tailscale IP:** 100.105.251.99
- **Webhook URL:** https://n8n.andykaufman.net/webhooks/resend
- **n8n port:** 5678 (Docker service name: n8n)
- **Gateway auth token:** tQnJMkuYLVKuO6NdWDQJ_eaBZhA2S4qz8uJuFJpw5Iw (separate from hooks token)

## Next Phase Readiness
- Gateway accepting hook POSTs from Tailscale network -- ready for n8n workflow (Plan 02)
- Caddy routing /webhooks/resend to n8n -- ready for Resend webhook configuration
- VPS connectivity to EC2 verified -- n8n can POST to hooks endpoint
- n8n webhook workflow (Plan 02) needs to be created at path matching Caddy route

---
*Phase: 20-inbound-email-infrastructure*
*Completed: 2026-02-16*
