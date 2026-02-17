---
phase: 21-inbound-email-processing
plan: 02
subsystem: email-reply-threading
tags: [resend, threading, in-reply-to, references, delivery-status, allowlist, n8n, webhook, skill]

requires:
  - phase: 21-inbound-email-processing
    plan: 01
    provides: "email.db with email_conversations table, SKILL.md sections 1-9 (inbound processing + rate limiting)"
  - phase: 20-inbound-email-infrastructure
    plan: 02
    provides: "n8n Resend Inbound Email Relay workflow with Svix verification, hooks endpoint"
provides:
  - "SKILL.md Sections 10-13: reply threading (In-Reply-To + References), allowlist management (add/remove/show), conversation history queries, delivery status handling"
  - "n8n workflow delivery status routing branch (email.delivered/bounced/delayed/complained -> OpenClaw hooks)"
  - "Resend webhook subscribed to 6 event types (received, sent, delivered, bounced, delivery_delayed, complained)"
affects: [email-reply-threading, email-delivery-tracking, allowlist-management, conversation-history]

tech-stack:
  added: []
  patterns: [email-reply-threading-headers, n8n-event-routing-branch, delivery-status-webhook-pipeline]

key-files:
  created: []
  modified:
    - /home/ubuntu/.openclaw/skills/resend-email/SKILL.md
    - n8n workflow 1XwpGnGro0NYtOjE (VPS Postgres)

key-decisions:
  - "Reply threading uses python3 subprocess for safe JSON construction -- avoids shell escaping issues with email headers"
  - "n8n event routing via IF node (Route Events) after Extract Metadata -- cleanly separates inbound vs delivery_status paths"
  - "Resend webhook updated via PATCH API to subscribe to delivery events -- no new webhook needed"
  - "Outbound replies use message_id='pending' since Resend generates RFC Message-ID server-side"
  - "Delivery status POST includes bounce/complaint notification instruction directly in hook message -- Bob handles Slack notification"

patterns-established:
  - "n8n event type routing: Extract Metadata adds 'route' field, IF node splits pipelines based on route value"
  - "Delivery status webhook pipeline: Resend -> n8n (verify+route) -> OpenClaw hooks -> Bob (DB update + optional notification)"
  - "Reply threading composition: python3 builds In-Reply-To + References + subject dedup in single script, sends via subprocess curl"

requirements-completed: []

duration: 5min
completed: 2026-02-17
---

# Phase 21 Plan 2: Reply Threading + Delivery Status Summary

**Threaded reply composition with In-Reply-To/References headers via python3, n8n delivery status event routing branch, Resend webhook subscription expanded to 6 event types, and SKILL.md sections 10-13 (reply threading, allowlist management, conversation history, delivery status handling)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-17T18:03:55Z
- **Completed:** 2026-02-17T18:09:19Z
- **Tasks:** 2
- **Files modified:** 2 (on remote servers: EC2 SKILL.md + VPS n8n workflow)

## Accomplishments
- SKILL.md expanded from 9 to 13 sections (639 lines total): Section 10 (Reply Threading with full python3 composition), Section 11 (Allowlist Management with add/remove/show), Section 12 (Conversation History with formatted thread output), Section 13 (Delivery Status Handling with bounce/complaint notifications)
- n8n workflow updated with 3 new nodes (Route Events IF node, POST Delivery Status, Respond 200 Delivery) -- total 11 nodes
- Extract Metadata node now routes both email.received and delivery status events with 'route' field
- Resend webhook subscription expanded from 1 event (email.received) to 6 events (+ sent, delivered, bounced, delivery_delayed, complained)
- Existing inbound email pipeline fully preserved -- email.received path unchanged
- Reply threading includes RFC 2822 In-Reply-To + References headers, Re: subject deduplication, Auto-Submitted: auto-replied

## Task Commits

All artifacts deployed to remote servers via SSH (no local file changes per task):

1. **Task 1: Add reply threading, allowlist management, and conversation queries to SKILL.md** - EC2 changes only. Appended Sections 10-13 (265 lines) to SKILL.md. Verified: In-Reply-To (4 mentions), References (5), allowlist (25), delivery_status (5), all 13 sections present, skill detected as "ready".
2. **Task 2: Add delivery status event routing to n8n workflow** - VPS changes. Updated Extract Metadata with routing logic, added Route Events IF node, POST Delivery Status node, Respond 200 Delivery node. Updated Resend webhook subscription via PATCH API. Verified: 11 nodes, workflow active, webhook returns 401 for unsigned requests.

**Plan metadata:** See final commit (docs: SUMMARY.md + STATE.md)

## Files Created/Modified
- `~/.openclaw/skills/resend-email/SKILL.md` - Added Section 10 (Reply Threading: thread data lookup, rate limit check, python3 reply composition with In-Reply-To/References/Auto-Submitted headers, outbound recording, Slack confirmation), Section 11 (Allowlist Management: add/remove/show with case-insensitive matching), Section 12 (Conversation History: sender thread queries with direction icons and delivery status), Section 13 (Delivery Status Handling: DB update and bounce/complaint Slack notifications)
- `n8n workflow 1XwpGnGro0NYtOjE (VPS)` - Updated Extract Metadata with route field (inbound vs delivery_status), added Route Events IF node, POST Delivery Status HTTP node (sends to OpenClaw /hooks/agent with status update instruction), Respond 200 Delivery webhook response node

## Decisions Made
- Reply threading uses python3 subprocess pattern (consistent with existing SKILL.md curl patterns) for safe JSON construction with email headers -- avoids shell escaping problems with angle brackets in Message-IDs
- n8n routing implemented as IF node after Extract Metadata rather than modifying Extract Metadata to have multiple outputs -- cleaner separation and easier to debug
- Resend webhook subscription updated in-place via PATCH API rather than creating a new webhook -- keeps single endpoint, single Svix signing secret
- Outbound reply records use message_id='pending' since Resend generates the RFC Message-ID server-side -- can be fetched later via GET /emails/{id} if needed
- Delivery status POST hook message includes the notification instruction text directly -- Bob reads it and decides whether to notify Andy based on status (bounced/complained = notify, delivered/delayed = silent)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Resend webhook subscription update**
- **Found during:** Task 2
- **Issue:** Resend webhook was only subscribed to `email.received` -- delivery status events would never reach n8n even with the new routing branch
- **Fix:** Used Resend PATCH API to add 5 delivery event types (sent, delivered, bounced, delivery_delayed, complained) to existing webhook
- **Files modified:** Resend webhook configuration (ee17cae3-d59f-4262-94f8-5f44b56dacf9)
- **Verification:** GET /webhooks confirms 6 event types subscribed

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for delivery status pipeline to function. Plan mentioned checking webhook subscription but didn't specify the API call to update it.

## Issues Encountered
- n8n container name was `n8n_postgres` (not `n8n-production-postgres-1` as in Phase 20 docs) -- likely Docker Compose naming changed between recreations. Resolved by checking `docker ps`.
- Resend webhook update required PATCH method (not PUT) -- discovered by testing both methods.

## User Setup Required
None - all configuration completed during execution.

## Verification Results
1. SKILL.md In-Reply-To mentions: 4 (header explanation + code + threading rules + section 9 existing)
2. SKILL.md References mentions: 5
3. SKILL.md allowlist mentions: 25 (comprehensive coverage across sections 8, 11)
4. SKILL.md delivery_status mentions: 5
5. SKILL.md Conversation History: 2 mentions
6. All 13 sections present (## 1 through ## 13)
7. OpenClaw skill detection: "ready"
8. n8n workflow nodes: 11 (3 new: Route Events, POST Delivery Status, Respond 200 Delivery)
9. n8n workflow active: true
10. Webhook endpoint live: 401 for unsigned requests (Svix working)
11. Resend webhook events: 6 (received, sent, delivered, bounced, delivery_delayed, complained)
12. n8n container healthy after restart

## Next Phase Readiness
- Full bidirectional email capability complete: inbound processing, threaded replies, delivery tracking, allowlist management, conversation history
- E2E testing recommended: send email to bob@mail.andykaufman.net, tell Bob to reply, verify threading in Gmail
- Delivery status tracking requires an actual outbound reply to trigger delivery events -- will be verified during first real reply
- Phase 21 fully complete -- both plans executed

## Self-Check: PASSED

- FOUND: 21-02-SUMMARY.md (local)
- FOUND: SKILL.md updated (EC2: ~/.openclaw/skills/resend-email/SKILL.md, 639 lines, 13 sections)
- FOUND: n8n workflow updated (VPS: 11 nodes, active)
- FOUND: Resend webhook updated (6 event types)

---
*Phase: 21-inbound-email-processing*
*Completed: 2026-02-17*
