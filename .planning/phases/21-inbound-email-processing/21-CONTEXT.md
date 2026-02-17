# Phase 21: Inbound Email Processing - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Bob intelligently processes inbound email: filters auto-replies, replies with threading, tracks conversations in SQLite. Builds on Phase 20's inbound infrastructure (webhook -> n8n -> OpenClaw hook). Does NOT add new email capabilities (scheduling campaigns, forwarding, etc.).

</domain>

<decisions>
## Implementation Decisions

### Sender handling
- Closed allowlist stored in `email-config.json` (reuse existing config file)
- Allowlisted senders → Bob processes normally (reads, can reply)
- Unknown senders → Bob notifies Andy in Slack with summary, does NOT reply
- Andy can add senders via Slack command ("add jane@example.com to email allowlist")
- Auto-replies / noreply / mailer-daemon → silently dropped (no notification)
- RFC 3834 `Auto-Submitted` header detection + vendor X-headers (X-Auto-Response-Suppress, X-Autoreply, etc.)

### Reply autonomy
- Bob does NOT auto-reply to any inbound email unprompted
- Inbound from allowlisted sender → Bob posts summary in Slack, waits for instruction
- Andy tells Bob "reply to that email and say X" → Bob composes and sends threaded reply
- No auto-response rules — that's future phase territory if ever needed
- All outbound replies include `Auto-Submitted: auto-replied` header per RFC 3834

### Conversation tracking
- `email_conversations` SQLite table: message_id, in_reply_to, references, from, to, subject, summary (Bob-generated), timestamp, direction (inbound/outbound), resend_email_id
- Full email bodies NOT stored in SQLite — live in Resend API, fetchable on demand
- Bob can query history: "show me my email thread with jane@example.com"
- Retention: indefinite (personal email volume, negligible storage)

### Notification & triage
- Every inbound from allowlisted sender → immediate Slack message: sender, subject, 2-3 line summary
- Unknown senders → same notification prefixed with "[Unknown sender]"
- Auto-replies / spam → silently dropped
- No priority levels (volume too low to warrant triage complexity)
- Notifications go to same channel as existing email hooks

### Rate limiting
- Max 1 reply per sender per hour
- Hard cap: 10 outbound in any 5-minute window halts all sending
- Both enforced in skill logic before curl call

### Claude's Discretion
- Exact SQLite schema (column types, indexes)
- Auto-reply header detection list (comprehensive RFC 3834 + vendor headers)
- Slack notification formatting
- Rate limiter implementation approach (in-memory vs SQLite counter)

</decisions>

<specifics>
## Specific Ideas

- Reuse `email-config.json` for allowlist (don't create a separate config file)
- Conversation table lives in same DB pattern as health.db / coordination.db
- Reply threading must work in Gmail and Outlook (In-Reply-To + References headers)
- Delivery status webhook events already flowing through n8n from Phase 20 — hook into those

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-inbound-email-processing*
*Context gathered: 2026-02-17*
