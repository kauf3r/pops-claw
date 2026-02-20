---
phase: 28-platform-cleanup
plan: 02
subsystem: auth, docs
tags: [oauth, gog, gmail, calendar, gateway-remote-url]

# Dependency graph
requires:
  - phase: 28-platform-cleanup
    plan: 01
    provides: "Clean doctor output, config migration verified"
provides:
  - "Both Gmail OAuth accounts re-authed with fresh tokens"
  - "AirSpace account now has calendar service (was gmail-only)"
  - "gateway.remote.url documented in PROJECT.md"
affects: [28-platform-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns: ["curl token exchange + gog tokens import (bypasses gog auth add --manual timeout bug)"]

key-files:
  created: []
  modified:
    - ".planning/PROJECT.md (gateway.remote.url docs + OAuth decision update)"
    - "EC2: ~/.config/gogcli/keyring/ (both account tokens refreshed)"

key-decisions:
  - "Gmail OAuth excess scopes (gmail.settings.basic, gmail.settings.sharing) accepted as gog CLI limitation -- hardcoded into --services gmail, cannot be removed without switching tools"
  - "Bypassed gog auth add --manual (context deadline exceeded on token exchange) with curl + gog auth tokens import"
  - "AirSpace account re-authed with gmail+calendar services (previously gmail-only since 2026-02-19)"
  - "gateway.remote.url documented in PROJECT.md Infrastructure section"

patterns-established:
  - "gog auth add --manual has a context deadline bug -- use curl token exchange + gog auth tokens import as workaround"
  - "Construct OAuth URL manually (same client_id/redirect_uri as gog), exchange code with curl, import token JSON"

requirements-completed: [CLN-01, CLN-05]

# Metrics
duration: 15min
completed: 2026-02-21
---

# Phase 28 Plan 02: OAuth Re-Auth & Gateway Documentation Summary

**Both accounts re-authed (calendar added to AirSpace), gateway.remote.url documented in PROJECT.md**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-21
- **Completed:** 2026-02-21
- **Tasks:** 3
- **Files modified:** 1 local (PROJECT.md) + 2 EC2 (keyring tokens)

## Accomplishments

- Re-authed theandykaufman@gmail.com with gmail+calendar services (fresh token)
- Re-authed kaufman@airspaceintegration.com with gmail+calendar services (calendar was missing -- previously gmail-only)
- Documented `gateway.remote.url` in PROJECT.md Infrastructure section with explanation of why it's needed (tailnet bind)
- Updated Key Decisions table: Gmail scope limitation documented, gateway remote URL added
- Gateway verified reachable from Mac via Tailscale (HTTP 200)
- Gateway restarted and running after re-auth

## Task Commits

1. **Task 1: Re-auth Gmail OAuth** -- EC2-only (keyring token changes). Used curl token exchange + `gog auth tokens import` to bypass gog's `auth add --manual` context deadline bug.
2. **Task 2: Human verification** -- User selected Option B (re-auth both accounts). Scope limitation (gog hardcodes excess scopes) accepted.
3. **Task 3: Document gateway.remote.url** -- PROJECT.md updated locally.

## Files Created/Modified

- `.planning/PROJECT.md` -- Added gateway.remote.url to Infrastructure section; updated Gmail scope decision from "deferred" to "accepted as gog limitation"; added gateway remote URL decision
- `EC2: ~/.config/gogcli/keyring/token:pops-claw:theandykaufman@gmail.com` -- Fresh token with gmail+calendar
- `EC2: ~/.config/gogcli/keyring/token:pops-claw:kaufman@airspaceintegration.com` -- Fresh token with gmail+calendar (calendar added)

## Decisions Made

1. **Accepted excess Gmail OAuth scopes as gog limitation:** `gmail.settings.basic` and `gmail.settings.sharing` are hardcoded into `--services gmail`. Cannot be removed without switching OAuth tools. No security risk behind Tailscale.

2. **Bypassed gog auth add --manual:** The `--manual` flow has a "context deadline exceeded" bug on token exchange POST. Workaround: construct OAuth URL manually, user authorizes in browser, exchange code via `curl -X POST https://oauth2.googleapis.com/token`, then `gog auth tokens import` with the refresh token.

3. **Added calendar to AirSpace account:** Was gmail-only since 2026-02-19. Now has both services, enabling AirSpace calendar queries.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] gog auth add --manual context deadline exceeded**
- **Found during:** Task 1 (OAuth re-auth)
- **Issue:** `gog auth add --manual` consistently fails with "exchange code: Post https://oauth2.googleapis.com/token: context deadline exceeded" despite EC2 having working connectivity to Google (curl completes in 0.14s). Likely an internal timeout in gog v0.9.0.
- **Fix:** Manual token exchange via curl + `gog auth tokens import`. Exported existing token to discover JSON format, then created import files with refresh tokens from curl exchange.
- **Files modified:** EC2 keyring tokens
- **Verification:** `gog auth list` shows both accounts, `gog gmail search` and `gog calendar events` work for both
- **Impact:** Same outcome achieved through alternative path. Documented as pattern for future re-auths.

---
**Total deviations:** 1 auto-fixed (1 blocking -- gog CLI bug)
**Impact on plan:** Moderate. Required novel workaround but achieved same result.

## Issues Encountered

- `gog auth add --manual` has a context deadline bug in v0.9.0. The token exchange POST times out despite network connectivity being fine. This affects all re-auth flows and requires the curl+import workaround.

## User Setup Required

None -- user completed interactive OAuth authorization in browser during session.

## Next Phase Readiness

- Phase 28 fully complete (CLN-01 through CLN-05 all resolved)
- Phase 29 (Content Distribution) is next -- depends on Phase 27 (DMARC at p=quarantine, completed 2026-02-19)
- All accounts authenticated and functional
- Gateway running and healthy

## Self-Check: PASSED

- SUMMARY.md: FOUND at .planning/phases/28-platform-cleanup/28-02-SUMMARY.md
- `gog auth list`: both accounts with gmail+calendar
- `gog gmail search`: works for both accounts
- `gog calendar events`: works for both accounts
- `gateway.remote.url` in PROJECT.md: documented
- Gateway: active (running), reachable (HTTP 200)

---
*Phase: 28-platform-cleanup*
*Completed: 2026-02-21*
