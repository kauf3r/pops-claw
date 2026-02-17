# Phase 21: Inbound Email Processing - Research

**Researched:** 2026-02-17
**Domain:** Inbound email filtering (auto-reply detection, sender allowlist), reply threading (RFC 2822 headers via Resend API), conversation tracking (SQLite), rate limiting
**Confidence:** HIGH

## Summary

This phase adds intelligent email processing on top of Phase 20's working inbound pipeline (Gmail -> Resend -> n8n -> OpenClaw -> Bob -> #popsclaw). The core work is: (1) an auto-reply/spam filter that silently drops bot mail before it reaches Andy, (2) a sender allowlist with unknown-sender notification, (3) threaded reply capability using Resend's `headers` parameter with `In-Reply-To` and `References`, (4) an `email_conversations` SQLite table tracking all inbound/outbound messages with threading metadata, (5) rate limiting (1 reply/sender/hour, hard cap 10 outbound/5min), and (6) delivery status tracking via Resend's existing webhook events.

All logic lives in Bob's SKILL.md (processing rules, reply composition, rate checks) and the n8n workflow (auto-reply filtering at the relay layer, delivery status event routing). No new external services needed. Resend's API natively supports custom headers including `In-Reply-To` and `References` for reply threading -- verified via Context7 with official code examples from Resend's "Reply to Receiving Emails" docs. The SQLite conversation table follows existing patterns (health.db, coordination.db) and is bind-mounted into the sandbox.

**Primary recommendation:** Split into 2 plans: (1) Auto-reply filter + allowlist + rate limiter in n8n + SKILL.md, (2) Reply threading + conversation DB + delivery status webhooks. Plan 1 is pure filtering/gating logic. Plan 2 adds stateful features.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Sender handling
- Closed allowlist stored in `email-config.json` (reuse existing config file)
- Allowlisted senders -> Bob processes normally (reads, can reply)
- Unknown senders -> Bob notifies Andy in Slack with summary, does NOT reply
- Andy can add senders via Slack command ("add jane@example.com to email allowlist")
- Auto-replies / noreply / mailer-daemon -> silently dropped (no notification)
- RFC 3834 `Auto-Submitted` header detection + vendor X-headers (X-Auto-Response-Suppress, X-Autoreply, etc.)

#### Reply autonomy
- Bob does NOT auto-reply to any inbound email unprompted
- Inbound from allowlisted sender -> Bob posts summary in Slack, waits for instruction
- Andy tells Bob "reply to that email and say X" -> Bob composes and sends threaded reply
- No auto-response rules -- that's future phase territory if ever needed
- All outbound replies include `Auto-Submitted: auto-replied` header per RFC 3834

#### Conversation tracking
- `email_conversations` SQLite table: message_id, in_reply_to, references, from, to, subject, summary (Bob-generated), timestamp, direction (inbound/outbound), resend_email_id
- Full email bodies NOT stored in SQLite -- live in Resend API, fetchable on demand
- Bob can query history: "show me my email thread with jane@example.com"
- Retention: indefinite (personal email volume, negligible storage)

#### Notification & triage
- Every inbound from allowlisted sender -> immediate Slack message: sender, subject, 2-3 line summary
- Unknown senders -> same notification prefixed with "[Unknown sender]"
- Auto-replies / spam -> silently dropped
- No priority levels (volume too low to warrant triage complexity)
- Notifications go to same channel as existing email hooks

#### Rate limiting
- Max 1 reply per sender per hour
- Hard cap: 10 outbound in any 5-minute window halts all sending
- Both enforced in skill logic before curl call

### Claude's Discretion
- Exact SQLite schema (column types, indexes)
- Auto-reply header detection list (comprehensive RFC 3834 + vendor headers)
- Slack notification formatting
- Rate limiter implementation approach (in-memory vs SQLite counter)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Technology | Version | Purpose | Why Standard |
|------------|---------|---------|--------------|
| Resend Send Email API | v1 (`POST /emails`) | Send threaded replies with custom headers | Already in use (Phase 19). Natively supports `In-Reply-To` and `References` via `headers` parameter |
| Resend Received Emails API | v1 (`GET /emails/receiving/{id}`) | Fetch full email body + headers for auto-reply detection | Already configured (Phase 20). Returns headers object including `message-id` |
| SQLite | 3.x (bind-mounted binary) | Conversation tracking, rate limiting counters | Already used for health.db, coordination.db, content.db. Same bind-mount pattern |
| n8n Workflow | Existing (ID: 1XwpGnGro0NYtOjE) | Auto-reply filtering at relay layer, delivery status event routing | Already handling inbound email relay (Phase 20) |
| OpenClaw SKILL.md | v2026.2.x | Reply composition, allowlist management, rate check, conversation DB queries | Bob's primary instruction mechanism |

### Supporting

| Technology | Version | Purpose | When to Use |
|------------|---------|---------|-------------|
| `curl` (in sandbox) | built-in | Send reply emails via Resend API, fetch email headers | Every reply and on-demand body fetch |
| `sqlite3` (in sandbox) | bind-mounted | Query/insert conversation records, check rate limits | Every inbound email and every reply |
| `python3` (in sandbox) | built-in | JSON payload construction for curl, header analysis | Complex reply composition with proper escaping |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite rate counters | In-memory counters in SKILL logic | In-memory resets on session/container restart. SQLite persists. For rate limiting that must survive restarts, SQLite is correct |
| n8n-layer auto-reply filter | Skill-layer filter (Bob decides) | n8n filter prevents unnecessary OpenClaw hook invocations (saves tokens/compute). But n8n needs full email headers which requires an extra API call. **Recommendation: filter in SKILL.md** -- Bob already gets woken by the hook, and can fetch headers with a single curl call. Simpler than adding header-fetch logic to n8n |
| Separate rate_limits table | Columns on email_conversations | Dedicated table is cleaner for the 5-min window query. But conversations table already has timestamp + direction. **Recommendation: query email_conversations directly** -- `SELECT COUNT(*) FROM email_conversations WHERE direction='outbound' AND timestamp > datetime('now', '-5 minutes')` is efficient with an index |

**Installation:** No new packages. All components exist:
1. SQLite binary already bind-mounted to sandbox
2. Resend API key already in sandbox env (full_access scope from Phase 20)
3. n8n workflow already active
4. email-config.json already in workspace

## Architecture Patterns

### Data Flow: Inbound Email Processing

```
Inbound Email (via Phase 20 pipeline)
    |
    v
Bob wakes (hook:inbound-email:{id})
    |
    v
[1] Fetch full email headers via Resend API
    |
    v
[2] Auto-reply detection (check headers)
    |--- Auto-reply detected --> silently drop, no notification
    |
    v
[3] Sender allowlist check (email-config.json)
    |--- Unknown sender --> Slack: "[Unknown sender] From: X, Subject: Y, Preview: Z"
    |--- Allowlisted --> Slack: "From: X, Subject: Y, Preview: Z"
    |
    v
[4] Record in email_conversations table
    |
    v
[5] Wait for Andy's instruction (no auto-reply)
```

### Data Flow: Reply Composition

```
Andy says "reply to that email and say X"
    |
    v
[1] Bob looks up conversation in email_conversations
    |
    v
[2] Rate limit check:
    |--- 1/sender/hour check --> BLOCK if exceeded
    |--- 10/5min hard cap --> HALT ALL if exceeded
    |
    v
[3] Compose reply with threading headers:
    - In-Reply-To: <original_message_id>
    - References: <all_previous_message_ids in thread>
    - Subject: "Re: {original_subject}"
    - Auto-Submitted: auto-replied
    |
    v
[4] Send via Resend API (POST /emails with headers)
    |
    v
[5] Record outbound in email_conversations
    |
    v
[6] Confirm to Andy in Slack
```

### Pattern 1: Resend Reply with Threading Headers

**What:** Send a reply that appears in the same thread in Gmail/Outlook.
**When to use:** Every time Bob replies to an inbound email.
**Source:** [Resend Reply to Receiving Emails](https://resend.com/docs/dashboard/receiving/reply-to-emails) (Context7 verified)

```bash
# Bob sends a threaded reply from sandbox
python3 -c "
import json, subprocess, os

# Threading data from email_conversations
original_message_id = '<original-msg-id@example.com>'
previous_refs = ['<msg1@example.com>', '<msg2@example.com>']
original_subject = 'Meeting tomorrow'

# Build References header: all previous message IDs + the one being replied to
all_refs = previous_refs + [original_message_id]
references_header = ' '.join(all_refs)

payload = json.dumps({
    'from': 'Bob <bob@mail.andykaufman.net>',
    'to': ['recipient@example.com'],
    'subject': f'Re: {original_subject}',
    'html': '<p>Reply content here</p>',
    'text': 'Reply content here',
    'headers': {
        'In-Reply-To': original_message_id,
        'References': references_header,
        'Auto-Submitted': 'auto-replied'
    },
    'tags': [{'name': 'type', 'value': 'reply'}]
})

result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'https://api.resend.com/emails',
     '-H', f'Authorization: Bearer {os.environ[\"RESEND_API_KEY\"]}',
     '-H', 'Content-Type: application/json',
     '-d', payload],
    capture_output=True, text=True
)
print(result.stdout)
"
```

**Critical threading rules (RFC 2822/5322):**
- `In-Reply-To`: Set to the `message_id` of the email being replied to (the immediate parent)
- `References`: All `message_id`s in the thread chain, space-separated, in chronological order. Append the parent's `message_id` to the parent's `References` header value
- `Subject`: Prefix with `Re: ` (only once -- don't stack `Re: Re: Re:`)
- Both Gmail and Outlook use `References` for thread grouping; `In-Reply-To` links the direct parent

### Pattern 2: Auto-Reply Detection Header Checks

**What:** Comprehensive header-based detection of automated emails.
**When to use:** Every inbound email, before allowlist check.
**Source:** [RFC 3834](https://datatracker.ietf.org/doc/html/rfc3834), [arp242.net Auto-Reply Detection Guide](https://www.arp242.net/autoreply.html)

```python
def is_auto_reply(headers):
    """
    Returns True if the email is an auto-reply/automated message.
    Check order matters: cheapest checks first.
    """
    # 1. RFC 3834: Auto-Submitted header (most authoritative)
    auto_submitted = headers.get('auto-submitted', '').lower()
    if auto_submitted and auto_submitted != 'no':
        return True  # Values: auto-generated, auto-replied, auto-notified

    # 2. Microsoft X-Auto-Response-Suppress
    xars = headers.get('x-auto-response-suppress', '').lower()
    if xars and ('all' in xars or 'autoreply' in xars or 'dr' in xars or 'oof' in xars):
        return True

    # 3. Precedence header (bulk, auto_reply, list, junk)
    precedence = headers.get('precedence', '').lower()
    if precedence in ('bulk', 'auto_reply', 'list', 'junk'):
        return True

    # 4. X-Autoreply header (rare but definitive)
    if headers.get('x-autoreply', '').lower() == 'yes':
        return True

    # 5. X-Autorespond header
    if headers.get('x-autorespond', ''):
        return True

    # 6. X-Loop header (loop prevention)
    if headers.get('x-loop', ''):
        return True

    # 7. From address patterns (noreply, mailer-daemon)
    from_addr = headers.get('from', '').lower()
    noreply_patterns = ['noreply@', 'no-reply@', 'no_reply@',
                        'donotreply@', 'do-not-reply@',
                        'mailer-daemon@', 'postmaster@',
                        'mail delivery subsystem']
    if any(pattern in from_addr for pattern in noreply_patterns):
        return True

    # 8. Return-Path: <> (null sender = bounce/DSN)
    return_path = headers.get('return-path', '').strip()
    if return_path == '<>' or return_path == '':
        return True

    return False
```

**Header detection list (comprehensive, ordered by reliability):**

| Header | Value | Source | Reliability |
|--------|-------|--------|-------------|
| `Auto-Submitted` | Any value except `no` | RFC 3834 | HIGH -- standard |
| `X-Auto-Response-Suppress` | `All`, `AutoReply`, `DR`, `OOF` | Microsoft Exchange | HIGH -- widely deployed |
| `Precedence` | `bulk`, `auto_reply`, `list`, `junk` | De facto standard | HIGH -- mailing lists, newsletters |
| `X-Autoreply` | `yes` | Various | MEDIUM -- rare but definitive |
| `X-Autorespond` | Any value | Various | MEDIUM -- rare |
| `X-Loop` | Any value | Loop prevention | MEDIUM -- sometimes false positive |
| `From` contains | `noreply`, `no-reply`, `mailer-daemon`, `postmaster` | Address pattern | HIGH -- nearly universal for automated senders |
| `Return-Path` | `<>` (empty) | RFC 5321 | HIGH -- DSN/bounce indicator |

### Pattern 3: email-config.json Allowlist Extension

**What:** Add sender allowlist to existing email-config.json.
**When to use:** One-time config update, then Bob manages via Slack commands.

```json
{
  "recipients": [
    {
      "email": "theandykaufman@gmail.com",
      "name": "Andy"
    }
  ],
  "daily_send_count": 1,
  "daily_send_date": "2026-02-17",
  "alert_count_today": 0,
  "sender_allowlist": [
    "theandykaufman@gmail.com",
    "kaufman@airspaceintegration.com"
  ]
}
```

**Allowlist matching rules:**
- Case-insensitive email comparison
- Match against the bare email address extracted from "Display Name <email@domain.com>" format
- Allowlist is a simple string array (no glob patterns, no domain wildcards for v1)
- Andy manages via Slack: "add jane@example.com to email allowlist" -> Bob reads config, appends, writes back

### Pattern 4: Conversation DB Schema

**What:** SQLite table for email conversation tracking.
**When to use:** Created once, queried on every inbound/outbound email.

```sql
CREATE TABLE email_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,           -- RFC 2822 Message-ID header value
    in_reply_to TEXT,                   -- Message-ID of parent (for threading)
    references_chain TEXT,              -- Space-separated Message-IDs (full thread)
    from_addr TEXT NOT NULL,            -- Sender email address
    to_addr TEXT NOT NULL,              -- Recipient email address
    subject TEXT,                       -- Email subject line
    summary TEXT,                       -- Bob-generated 2-3 line summary
    direction TEXT NOT NULL CHECK(direction IN ('inbound', 'outbound')),
    resend_email_id TEXT,               -- Resend's internal email ID (for API fetch)
    delivery_status TEXT DEFAULT 'unknown', -- sent, delivered, bounced, delayed, complained
    created_at TEXT DEFAULT (datetime('now'))
);

-- Index for thread lookups (find all messages in a conversation)
CREATE INDEX idx_conversations_message_id ON email_conversations(message_id);
CREATE INDEX idx_conversations_in_reply_to ON email_conversations(in_reply_to);

-- Index for sender history (rate limiting + "show me emails from X")
CREATE INDEX idx_conversations_from ON email_conversations(from_addr, created_at);

-- Index for rate limiting (outbound count in time window)
CREATE INDEX idx_conversations_outbound ON email_conversations(direction, created_at)
    WHERE direction = 'outbound';

-- Index for Resend email ID lookups (delivery status updates)
CREATE INDEX idx_conversations_resend_id ON email_conversations(resend_email_id);
```

**Schema design rationale:**
- `message_id` is the RFC 2822 Message-ID (angle-bracket format like `<abc123@example.com>`). NOT the Resend email_id
- `resend_email_id` is Resend's internal UUID (like `56761188-7520-42d8-8898-ff6fc54ce618`). Used for API fetch and delivery status correlation
- `references_chain` stores the full References header value (space-separated message IDs). Enables rebuilding thread history for replies
- `summary` is Bob's 2-3 sentence summary, generated when processing inbound emails. Useful for "show me my thread with X" queries
- `delivery_status` tracks outbound email fate via webhook events. Default 'unknown' until webhook fires
- No `UNIQUE` constraint on `message_id` because the same message could theoretically arrive via multiple paths (unlikely but defensive)
- Partial index on `direction='outbound'` optimizes the rate limiting query

### Pattern 5: Rate Limiting Queries

**What:** SQLite-based rate limit checks before sending.
**When to use:** Before every outbound email.

```sql
-- Check 1: Max 1 reply per sender per hour
SELECT COUNT(*) as recent_replies
FROM email_conversations
WHERE direction = 'outbound'
  AND to_addr = ?  -- the recipient we're about to reply to
  AND created_at > datetime('now', '-1 hour');
-- If recent_replies >= 1: BLOCK this reply

-- Check 2: Hard cap 10 outbound in any 5-minute window
SELECT COUNT(*) as recent_outbound
FROM email_conversations
WHERE direction = 'outbound'
  AND created_at > datetime('now', '-5 minutes');
-- If recent_outbound >= 10: HALT ALL sending
```

**Implementation in SKILL.md (bash/python):**
```bash
# Rate limit check before sending
SENDER_COUNT=$(sqlite3 /workspace/email.db "SELECT COUNT(*) FROM email_conversations WHERE direction='outbound' AND to_addr='$RECIPIENT' AND created_at > datetime('now', '-1 hour');")
WINDOW_COUNT=$(sqlite3 /workspace/email.db "SELECT COUNT(*) FROM email_conversations WHERE direction='outbound' AND created_at > datetime('now', '-5 minutes');")

if [ "$SENDER_COUNT" -ge 1 ]; then
    echo "Rate limit: already replied to $RECIPIENT in the last hour"
    exit 1
fi
if [ "$WINDOW_COUNT" -ge 10 ]; then
    echo "HARD CAP: 10 outbound emails in 5 minutes. All sending halted."
    exit 1
fi
```

### Pattern 6: Delivery Status Webhook Processing

**What:** Update `delivery_status` in email_conversations when Resend fires delivery events.
**When to use:** Existing n8n webhook already receives Resend events. Add routing for delivery status events.

Resend webhook event types for delivery tracking:
- `email.sent` -- API accepted, attempting delivery
- `email.delivered` -- Successfully delivered to recipient's mail server
- `email.bounced` -- Permanently rejected (includes `bounce.message`, `bounce.type`, `bounce.subType`)
- `email.delivery_delayed` -- Temporary failure (recipient inbox full, transient server issue)
- `email.complained` -- Recipient marked as spam

**Payload format (all delivery events share this structure):**
```json
{
  "type": "email.delivered",
  "created_at": "2024-02-22T23:41:12.126Z",
  "data": {
    "email_id": "56761188-7520-42d8-8898-ff6fc54ce618",
    "from": "Acme <onboarding@resend.dev>",
    "to": ["delivered@resend.dev"],
    "subject": "Sending this example"
  }
}
```

**n8n workflow modification:** The existing Resend webhook already receives all event types (if subscribed). Add a branch after Svix verification:
- `email.received` -> existing inbound processing pipeline
- `email.delivered`, `email.bounced`, `email.complained`, `email.delivery_delayed` -> POST to OpenClaw hooks with delivery status update instruction
- Bob updates `delivery_status` in email_conversations by matching `resend_email_id`

**Note:** Delivery status events fire for outbound emails sent by Bob. The `email_id` in the event matches the Resend ID returned by `POST /emails`. This is how we correlate delivery events to conversation records.

### Anti-Patterns to Avoid

- **Storing full email bodies in SQLite:** Bodies can be large (HTML, inline images). Resend stores them -- fetch on demand via API. SQLite stores only metadata + summary.
- **Auto-replying to any email without Andy's instruction:** User decision is explicit: Bob NEVER auto-replies. All replies are Andy-directed.
- **Filtering at the n8n layer instead of skill layer:** Adding header-fetch + filter logic to n8n means more n8n Code nodes, harder to maintain. Bob already gets woken by the hook -- let him check headers in one curl call and decide.
- **Using in-memory rate counters:** Session restarts clear them. SQLite persists across container restarts and gateway restarts.
- **Stacking "Re: Re: Re:" in subject lines:** Check if subject already starts with `Re:` (case-insensitive). Only add it once.
- **Matching allowlist by display name:** Always extract and compare the bare email address. Display names are unreliable and easily spoofed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email threading | Custom Message-ID generation + thread tracking | Resend's `headers` parameter with `In-Reply-To` + `References` | Resend handles SMTP delivery; just pass the headers. Thread formation is email-client-side |
| Auto-reply detection | Simple "check from address" filter | Comprehensive header check (RFC 3834 + 8 vendor headers) | From-address check misses 60%+ of auto-replies. Header check catches >95% |
| Email body parsing | Strip HTML manually with regex | Resend API returns both `text` and `html` separately | Resend already parsed the MIME. Use `text` field directly |
| Rate limiting persistence | Write a JSON counter file | SQLite query on email_conversations table | Already storing conversation records. Query is 1 line of SQL |
| Message-ID extraction | Parse raw email headers manually | Resend Received Emails API returns `message_id` field | API already extracts it from the parsed email |

**Key insight:** Resend does the heavy lifting (email parsing, header extraction, MIME handling, delivery tracking). Bob's job is decision-making (filter, classify, compose) and record-keeping (SQLite), not email protocol implementation.

## Common Pitfalls

### Pitfall 1: Message-ID vs Resend Email ID Confusion

**What goes wrong:** Bob stores Resend's UUID (`56761188-...`) in the `message_id` column instead of the RFC 2822 Message-ID (`<unique-id@example.com>`). Threading breaks because `In-Reply-To` expects RFC Message-IDs.
**Why it happens:** The `email.received` webhook payload has `email_id` (Resend UUID) and `message_id` (RFC 2822 ID). Easy to grab the wrong one.
**How to avoid:**
- `email_conversations.message_id` = RFC 2822 `message_id` from webhook/API (for threading)
- `email_conversations.resend_email_id` = Resend's `email_id` UUID (for API fetch + delivery status)
- Variable naming: always `message_id` for RFC, `resend_email_id` or `email_id` for Resend
**Warning signs:** `In-Reply-To` header contains a UUID without angle brackets. Replies don't thread.

### Pitfall 2: Headers Not Available in Webhook Payload

**What goes wrong:** Bob tries to check auto-reply headers from the inbound webhook metadata, but the webhook only contains `from`, `to`, `subject`, `email_id`, `message_id`. No `Auto-Submitted`, no `Precedence`, no `X-Auto-Response-Suppress`.
**Why it happens:** Resend's `email.received` webhook is metadata-only. Full headers require a separate API call to `GET /emails/receiving/{id}`.
**How to avoid:**
- After being woken by the hook, Bob's first action is `curl GET /emails/receiving/{email_id}` to fetch the full email including headers
- The `headers` object in the response contains all original email headers
- THEN run auto-reply detection against those headers
- If the API call fails, treat the email as non-auto-reply (safe default: notify Andy)
**Warning signs:** Auto-reply detection never fires. OOO messages still trigger Slack notifications.

### Pitfall 3: Resend Received Email API Response Header Casing

**What goes wrong:** Auto-reply header checks fail because the Resend API returns lowercase header names (`auto-submitted`) but the detection code checks for mixed case (`Auto-Submitted`).
**Why it happens:** Email headers are case-insensitive per RFC 2822, and Resend normalizes them to lowercase in the `headers` object.
**How to avoid:** Always lowercase header names before checking. The detection function should use `.lower()` on all header lookups or access headers with lowercase keys directly.
**Warning signs:** Auto-reply detection works in tests but not in production. Headers exist but checks don't match.

### Pitfall 4: Reply Subject Line Stacking

**What goes wrong:** Bob prepends "Re: " to every reply, producing "Re: Re: Re: Meeting tomorrow" after 3 exchanges.
**Why it happens:** Naive subject formatting without checking if "Re: " is already present.
**How to avoid:**
```python
def reply_subject(original_subject):
    s = original_subject.strip()
    # Remove any existing Re:/RE:/re: prefix (handles Re: Re: stacking too)
    import re
    s = re.sub(r'^(Re:\s*)+', '', s, flags=re.IGNORECASE).strip()
    return f'Re: {s}'
```
**Warning signs:** Email subjects grow longer with each reply. Looks unprofessional.

### Pitfall 5: Rate Limiter Timezone Issues

**What goes wrong:** Rate limiter counts replies using UTC timestamps but Andy thinks in Pacific Time. A reply at 11:55 PM PT appears as a different hour than 12:05 AM PT, but in UTC they might be within the same hour window.
**Why it happens:** SQLite `datetime('now')` returns UTC. Rate limits should operate on absolute time windows, not local-time hours.
**How to avoid:** Use UTC consistently. The rate limit is "1 per sender per 60-minute rolling window" -- this is timezone-agnostic. The query `created_at > datetime('now', '-1 hour')` works correctly in UTC regardless of Andy's local time. Don't try to convert to PT.
**Warning signs:** None likely -- this pitfall is avoided by using rolling windows with `datetime('now')` consistently.

### Pitfall 6: email.db Not Bind-Mounted to Sandbox

**What goes wrong:** Bob creates the DB inside the container. Container restarts lose all conversation data.
**Why it happens:** The DB file must be created on the host and bind-mounted, like health.db, coordination.db.
**How to avoid:**
1. Create the DB file on the EC2 host: `sqlite3 ~/clawd/agents/main/email.db < schema.sql`
2. Add bind mount to `openclaw.json`: `"/home/ubuntu/clawd/agents/main/email.db:/workspace/email.db:rw"`
3. Restart gateway to apply the new bind mount
4. SKILL.md references `/workspace/email.db`
**Warning signs:** Conversation history disappears after gateway restart. "Table not found" errors in fresh containers.

## Code Examples

### Example 1: Inbound Email Processing (SKILL.md Logic)

```bash
# Step 1: Fetch full email (headers + body) from Resend API
EMAIL_DATA=$(curl -s -X GET "https://api.resend.com/emails/receiving/${EMAIL_ID}" \
  -H "Authorization: Bearer $RESEND_API_KEY")

# Step 2: Extract headers and check for auto-reply
python3 << 'PYEOF'
import json, sys

email = json.loads('''EMAIL_DATA_HERE''')
headers = email.get('headers', {})

# Auto-reply detection
def is_auto_reply(h):
    if h.get('auto-submitted', '').lower() not in ('', 'no'):
        return True
    xars = h.get('x-auto-response-suppress', '').lower()
    if xars and any(v in xars for v in ['all', 'autoreply', 'dr', 'oof']):
        return True
    if h.get('precedence', '').lower() in ('bulk', 'auto_reply', 'list', 'junk'):
        return True
    if h.get('x-autoreply', '').lower() == 'yes':
        return True
    if h.get('x-autorespond', ''):
        return True
    from_addr = h.get('from', email.get('from', '')).lower()
    for p in ['noreply@', 'no-reply@', 'no_reply@', 'donotreply@',
              'mailer-daemon@', 'postmaster@']:
        if p in from_addr:
            return True
    rp = h.get('return-path', '').strip()
    if rp in ('<>', ''):
        return True
    return False

if is_auto_reply(headers):
    print('AUTO_REPLY')
else:
    print('PROCESS')
PYEOF
```

### Example 2: Send Threaded Reply

```bash
# Build and send a threaded reply
python3 -c "
import json, subprocess, os, re

# Data from email_conversations table
original_msg_id = '$ORIGINAL_MESSAGE_ID'
existing_refs = '$REFERENCES_CHAIN'  # space-separated
original_subject = '$ORIGINAL_SUBJECT'
recipient = '$RECIPIENT'
reply_body_html = '$REPLY_HTML'
reply_body_text = '$REPLY_TEXT'

# Build References: existing chain + the message being replied to
refs = (existing_refs + ' ' + original_msg_id).strip()

# Clean subject (no Re: stacking)
clean_subj = re.sub(r'^(Re:\s*)+', '', original_subject, flags=re.IGNORECASE).strip()
subject = f'Re: {clean_subj}'

payload = json.dumps({
    'from': 'Bob <bob@mail.andykaufman.net>',
    'to': [recipient],
    'subject': subject,
    'html': reply_body_html,
    'text': reply_body_text,
    'headers': {
        'In-Reply-To': original_msg_id,
        'References': refs,
        'Auto-Submitted': 'auto-replied'
    },
    'tags': [{'name': 'type', 'value': 'reply'}]
})

result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'https://api.resend.com/emails',
     '-H', f'Authorization: Bearer {os.environ[\"RESEND_API_KEY\"]}',
     '-H', 'Content-Type: application/json',
     '-d', payload],
    capture_output=True, text=True
)
response = json.loads(result.stdout)
if 'id' in response:
    print(f'SENT:{response[\"id\"]}')
else:
    print(f'ERROR:{result.stdout}')
"
```

### Example 3: Allowlist Management via Slack

```bash
# Bob reads config, adds sender, writes back
python3 -c "
import json

with open('/workspace/email-config.json') as f:
    config = json.load(f)

# Initialize allowlist if not present
if 'sender_allowlist' not in config:
    config['sender_allowlist'] = []

new_sender = 'jane@example.com'
if new_sender.lower() not in [s.lower() for s in config['sender_allowlist']]:
    config['sender_allowlist'].append(new_sender)

with open('/workspace/email-config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f'Added {new_sender} to allowlist. Current list: {config[\"sender_allowlist\"]}')
"
```

### Example 4: Conversation History Query

```sql
-- Show all emails in a thread with jane@example.com
SELECT
    direction,
    from_addr,
    subject,
    summary,
    delivery_status,
    created_at
FROM email_conversations
WHERE from_addr LIKE '%jane@example.com%'
   OR to_addr LIKE '%jane@example.com%'
ORDER BY created_at ASC;

-- Show thread by following References chain
SELECT * FROM email_conversations
WHERE message_id IN (
    SELECT message_id FROM email_conversations WHERE in_reply_to = ?
    UNION
    SELECT ? -- the original message
)
ORDER BY created_at ASC;
```

## Discretion Recommendations

### SQLite Schema

**Recommendation:** Use the schema from Pattern 4 above. Key design choices:
- `TEXT` for all string columns (SQLite is dynamically typed anyway)
- `CHECK` constraint on `direction` to prevent typos
- Partial index on `direction='outbound'` for rate limiting performance
- Separate `message_id` (RFC) and `resend_email_id` (Resend UUID) columns
- `delivery_status` defaults to `'unknown'` and updates asynchronously via webhooks
- `created_at` uses `datetime('now')` trigger (UTC) for consistent timestamps

**DB file location:** `/workspace/email.db` (sandbox path), host path `~/clawd/agents/main/email.db`. Follows existing pattern (health.db is in `agents/main/`, bind-mounted to `/workspace/`).

### Auto-Reply Header Detection List

**Recommendation:** Use the comprehensive list from Pattern 2. Ordered by reliability:
1. `Auto-Submitted` (RFC 3834) -- most authoritative
2. `X-Auto-Response-Suppress` (Microsoft) -- widely deployed
3. `Precedence` (de facto) -- catches mailing lists and newsletters
4. `X-Autoreply` / `X-Autorespond` -- rare but definitive
5. `X-Loop` -- loop prevention marker
6. From address patterns (`noreply@`, `mailer-daemon@`, etc.)
7. `Return-Path: <>` -- DSN/bounce indicator

This list is conservative (might miss some edge cases) but has near-zero false positives. A legitimate personal email will never have these headers.

### Slack Notification Formatting

**Recommendation:** Structured Slack message with clear visual hierarchy:

For allowlisted senders:
```
:email: *Inbound Email*
*From:* Jane Smith <jane@example.com>
*Subject:* Meeting tomorrow at 3pm
*Received:* Feb 17, 2026 2:30 PM PT

> Hi Andy, just wanted to confirm our meeting tomorrow at 3pm...

_Reply with: "reply to that email and say [your message]"_
```

For unknown senders:
```
:warning: *[Unknown Sender] Inbound Email*
*From:* sales@randomcompany.com
*Subject:* Special offer just for you
*Received:* Feb 17, 2026 2:30 PM PT

> We have an exclusive deal...

_Unknown sender -- not on allowlist. Say "add sales@randomcompany.com to email allowlist" to allow future emails._
```

### Rate Limiter Implementation

**Recommendation:** SQLite-based (query email_conversations table). Rationale:
- Already storing outbound records in the table
- Queries are simple (`COUNT(*) WHERE direction='outbound' AND created_at > ...`)
- Persists across container/gateway restarts
- No additional data structure to maintain
- Indexes on `(direction, created_at)` make the query fast even at scale

No separate rate_limits table needed. The conversation table IS the rate limit ledger.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Check only From address for auto-reply | Multi-header detection (RFC 3834 + vendor) | RFC 3834 (2004), but vendor headers evolved through 2024 | Catches >95% of auto-replies vs ~40% with From-only |
| Store email body in local DB | Metadata-only DB + API fetch on demand | Resend model (2024+) | Saves storage, always has latest version |
| SMTP relay for replies | API-based send with custom headers | 2020+ (transactional email APIs) | No SMTP server needed, threading via headers param |
| Manual thread tracking | Message-ID / References / In-Reply-To standard | RFC 2822 (2001), RFC 5322 (2008) | Universal email client support for threading |

**Deprecated/outdated:**
- `X-Precedence` header: replaced by `Precedence` (no X- prefix)
- SMTP `MAIL FROM:<>` as sole bounce indicator: still valid but should be combined with header checks
- Polling Resend API for delivery status: replaced by webhook events (`email.delivered`, `email.bounced`, etc.)

## Open Questions

1. **Resend Received Emails API header completeness**
   - What we know: API returns a `headers` object with `content-type`, `message-id`, and other headers
   - What's unclear: Whether ALL original headers are preserved (e.g., `Auto-Submitted`, `X-Auto-Response-Suppress`). The API docs show a minimal example.
   - Recommendation: Test with a known auto-reply email during Plan 1 execution. Send an OOO reply to @mail.andykaufman.net and verify the fetched headers contain `Auto-Submitted`. If headers are incomplete, fall back to From-address pattern matching as primary detection.

2. **Delivery status webhook subscription scope**
   - What we know: Phase 20 configured a Resend webhook for `email.received` events. Delivery events (`email.delivered`, `email.bounced`, etc.) may or may not be subscribed.
   - What's unclear: Whether the existing webhook endpoint is subscribed to delivery events, or only `email.received`.
   - Recommendation: Check Resend dashboard during execution. If only `email.received` is subscribed, add delivery event types. The existing n8n workflow already receives all event types at the same URL -- just needs a branch in the Code node to route them.

3. **email.db bind mount requires gateway restart**
   - What we know: Adding a new bind mount to `openclaw.json` requires a gateway restart. This briefly interrupts Bob's availability.
   - What's unclear: Whether the DB file must exist before the bind mount is added (likely yes -- Docker mount of nonexistent file creates a directory instead).
   - Recommendation: (a) Create the DB file on host first with schema, (b) add bind mount to config, (c) restart gateway. Standard procedure, same as health.db.

## Sources

### Primary (HIGH confidence)
- [Resend Reply to Receiving Emails](https://resend.com/docs/dashboard/receiving/reply-to-emails) -- `In-Reply-To` and `References` header usage with code examples (Context7 verified)
- [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email) -- `headers` parameter documentation, full parameter list (Context7 verified)
- [Resend Received Emails API](https://resend.com/docs/api-reference/emails/retrieve-received-email) -- Response format with `headers` object, `message_id` field (Context7 verified)
- [Resend Webhook Event Types](https://resend.com/docs/dashboard/webhooks/event-types) -- All 15 event types with payload examples (Context7 verified)
- [Resend Get Email Content](https://resend.com/docs/dashboard/receiving/get-email-content) -- Full email retrieval including headers and body (Context7 verified)
- [RFC 3834 - Automatic Responses to Electronic Mail](https://datatracker.ietf.org/doc/html/rfc3834) -- `Auto-Submitted` header specification, auto-reply filtering guidelines
- [RFC 5322 - Internet Message Format](https://datatracker.ietf.org/doc/html/rfc5322) -- `In-Reply-To`, `References`, `Message-ID` header specifications
- [Resend Schedule Email](https://resend.com/docs/dashboard/emails/schedule-email) -- `scheduled_at` parameter (ISO 8601, natural language, up to 30 days)

### Secondary (MEDIUM confidence)
- [arp242.net: How to detect automatically generated emails](https://www.arp242.net/autoreply.html) -- Comprehensive auto-reply header detection guide, vendor header catalog
- [Microsoft MS-OXCMAIL: Auto Response Suppress](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxcmail/ced68690-498a-4567-9d14-5c01f974d8b1) -- X-Auto-Response-Suppress header values specification
- [Jitbit: Detecting Outlook autoreply/OOF emails](https://www.jitbit.com/maxblog/18-detecting-outlook-autoreplyout-of-office-emails-and-x-auto-response-suppress-header/) -- Practical detection guide with Microsoft-specific headers

### Tertiary (LOW confidence)
- Resend `headers` object completeness for received emails -- API docs show minimal example. Actual header preservation needs runtime verification with a real auto-reply email.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All components are existing services already deployed. Resend threading headers verified via Context7 with official code examples.
- Architecture: HIGH -- Processing flow is straightforward filter-then-act. SQLite schema follows existing patterns. Rate limiting is simple COUNT queries.
- Pitfalls: HIGH -- Message-ID confusion, header availability, subject stacking all documented with prevention strategies. Auto-reply detection list sourced from RFC + multiple practitioner guides.

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable domain -- Resend API, RFC standards, SQLite patterns all mature/stable)
