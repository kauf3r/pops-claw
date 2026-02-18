# Architecture: Content Distribution, Security Hardening & LLM Observability

**Domain:** Integration architecture for content distribution, SecureClaw plugin, and LLM observability hooks into existing OpenClaw/EC2 deployment
**Researched:** 2026-02-17
**Confidence:** MEDIUM-HIGH

---

## System Context: What Already Exists

The following components are LIVE and must not be disrupted:

```
EC2 (100.72.143.9) — OpenClaw v2026.2.6-3
├── Gateway: :18789 (tailnet bind)
├── Agents (7):
│   ├── main (Bob) — Andy's primary assistant
│   ├── landos (Scout) — research agent
│   ├── rangeos (Vector) — topic researcher
│   ├── ops (Sentinel) — operations/monitoring
│   ├── quill (Quill) — writer
│   ├── sage (Sage) — reviewer
│   └── ezra (Ezra) — WordPress publisher
├── Databases (SQLite, bind-mounted):
│   ├── content.db — content pipeline state (status, drafts, published)
│   ├── email.db — email send/receive tracking + subscriber records
│   ├── health.db — system health metrics
│   └── coordination.db — inter-agent coordination
├── Skills (10): resend-email, clawdstrike, save-voice-notes, + 7 others
├── Crons (20): morning briefing, airspace monitor, email-catchup, + 17 others
└── Config: ~/.openclaw/openclaw.json + ~/.openclaw/.env

VPS (165.22.139.214 / Tailscale: 100.105.251.99)
├── n8n: webhook relay for Resend inbound email
└── Caddy: TLS termination for public webhooks

External Services:
├── Resend API: transactional email (bob@mail.andykaufman.net)
│   ├── email.db tracks sent/received emails
│   └── DMARC currently p=none (target: p=quarantine)
├── Anthropic API: LLM calls (Claude Haiku/Sonnet/Opus)
├── WordPress: Ezra publishes approved content
└── Slack: primary notification channel (Socket Mode)
```

---

## Component Boundaries: New vs Modified

### Feature 1: Content Distribution (Subscriber Notifications, Weekly Digest, Pitch Copy)

```
EXISTING:
  content.db
    └── articles table: status field (researched → drafted → reviewed → approved → published)
  email.db
    └── sent_emails, received_emails tables
  Ezra (agent): publishes to WordPress on human approval

NEW/MODIFIED:
  content.db
    └── (MODIFIED) articles table: add `notified_at` column to track send status
  email.db
    └── (MODIFIED) add subscribers table (email, name, subscribed_at, unsubscribed_at)
  Resend Audiences API
    └── (NEW) subscriber list synced from email.db subscribers table
  Resend Broadcasts API
    └── (NEW) weekly digest sent as Broadcast to Audience
  Ezra (agent)
    └── (MODIFIED) gets new distribution responsibilities:
        1. After WordPress publish: trigger subscriber notification via Resend transactional
        2. Weekly: compile digest from content.db, send via Resend Broadcast
  pitch-copy skill
    └── (NEW) SKILL.md at ~/.openclaw/skills/pitch-copy/ — Quill or Bob drafts social/pitch copy
  content-distribution cron
    └── (NEW) weekly digest trigger cron, e.g. Friday 9am PT
```

**Key Architectural Decision:** Use Resend Audiences + Broadcasts for the weekly digest (not individual transactional emails). Broadcasts handle list management, unsubscribe flows, and throttling automatically. Individual article notifications use transactional sends from the existing resend-email skill — simpler and already proven.

**Confidence: MEDIUM-HIGH** — Resend Broadcasts API confirmed functional (released March 2025, documented at resend.com/docs/dashboard/broadcasts/introduction). Integration with existing resend-email skill pattern is LOW-risk. Subscriber table schema is straightforward SQLite.

---

### Feature 2: SecureClaw Plugin Installation

```
EXISTING:
  ~/.openclaw/openclaw.json
    └── plugins.entries section (other plugins loaded here)
  Gateway: v2026.2.6-3 (CVE-2026-25253 unpatched)
  ClawdStrike skill: ~/.openclaw/skills/clawdstrike/ (16/25 OK, 3 warn)

NEW:
  OpenClaw binary: v2026.2.17 (CVE patched)
  SecureClaw plugin: ~/.openclaw/extensions/secureclaw/
    └── 51 automated checks across 8 categories
    └── 15 behavioral rules loaded into agent context (~1,230 tokens)
    └── 9 bash scripts (audit, harden, scan, integrity check, etc.)
    └── 4 JSON pattern databases
  openclaw.json (MODIFIED):
    └── plugins.entries.secureclaw: { enabled: true, config: { mode: "enforce" } }
```

**Plugin Install Pattern:**
SecureClaw uses the standard OpenClaw plugin installation flow:
```bash
openclaw plugins install secureclaw
# or direct: npm install -g @adversa-ai/secureclaw
# then: openclaw plugins enable secureclaw
```

SecureClaw's `openclaw.plugin.json` manifest uses `configPatch` to auto-merge security config into `openclaw.json` on install. No manual JSON editing required for the plugin config block. Manual editing may be needed for mode (`enforce` vs `audit`) and any custom behavioral rules.

**Relationship to Existing ClawdStrike:**
ClawdStrike is a SKILL (passive scanner, on-demand). SecureClaw is a PLUGIN (active runtime enforcement). They do not conflict — ClawdStrike audits, SecureClaw enforces. Run ClawdStrike after SecureClaw install to confirm score improves.

**Confidence: HIGH** — SecureClaw GitHub confirms plugin architecture, `configPatch` pattern confirmed for OpenClaw plugins, behavioral rules count (15) and check count (51) confirmed by Adversa AI press release.

---

### Feature 3: LLM Observability Hooks

```
EXISTING:
  openclaw.json:
    └── hooks.internal.entries.session-memory (already enabled)
  Morning briefing cron: pulls from health.db, coordination.db

NEW — Two approaches, pick one:

APPROACH A (diagnostics-otel plugin — MEDIUM confidence):
  openclaw.json (MODIFIED):
    └── plugins.entries.diagnostics-otel: { enabled: true }
    └── diagnostics.otel: {
          enabled: true,
          endpoint: "http://localhost:4318",   // or file export
          traces: true,
          metrics: true,
          logs: true
        }
  Limitation: Requires an OTEL collector endpoint. Adding Prometheus/Grafana
  or a managed OTEL backend is more infra than warranted for personal use.
  Workaround: Export to file, Bob reads file on morning briefing schedule.

APPROACH B (llm hooks → SQLite → Bob queries — HIGH confidence for fit):
  openclaw.json (MODIFIED):
    └── hooks.internal.entries.llm_input: { enabled: true }
    └── hooks.internal.entries.llm_output: { enabled: true }
  Each hook fires on every LLM call, writes payload to a script/file.
  A lightweight hook script appends JSON Lines to ~/clawd/logs/llm-usage.jsonl.
  Morning briefing cron: Bob reads llm-usage.jsonl, aggregates per-agent stats.

  NOTE: Existence of llm_input/llm_output as valid hook names in OpenClaw
  v2026.2.17 is UNCONFIRMED via official docs. The REQUIREMENTS.md references
  them as targets. Verify during Phase 26 planning by checking `openclaw hooks list`
  on the updated gateway.
```

**Recommendation: Start with Approach B (hook → JSONL → Bob reads).** No new infrastructure. Fits the existing pattern of Bob reading local files for context. If `llm_input`/`llm_output` hooks don't exist in v2026.2.17, fall back to diagnostics-otel with a local file exporter, or use the hook `llm:used` if it exists.

**Confidence: LOW-MEDIUM** for the specific hook names (`llm_input`, `llm_output`). The diagnostics-otel plugin is MEDIUM confidence as a fallback. The morning briefing integration pattern is HIGH confidence (Bob already aggregates multiple data sources).

---

## Data Flow: Publish → Notify Pipeline

```
Vector (rangeos) researches topic
    |
    v
content.db: status = 'researched'
    |
    v
Quill writes draft
    |
    v
content.db: status = 'drafted'
    |
    v
Sage reviews
    |
    v
content.db: status = 'reviewed'
    |
    v
[HUMAN APPROVAL GATE — Andy approves in Slack]
    |
    v
content.db: status = 'approved'
    |
    v
Ezra publishes to WordPress
    |
    v
content.db: status = 'published', published_url = 'https://...'
    |
    +---> [NEW] Ezra triggers subscriber notification:
    |         Resend transactional email to each subscriber
    |         (uses resend-email skill, curl to api.resend.com/emails)
    |         content.db: notified_at = NOW()
    |         email.db: records each send
    |
    +---> [NEW] Ezra drafts pitch copy (or triggers pitch-copy skill):
              Social media copy + outreach copy saved to coordination.db or Slack
```

## Data Flow: Weekly Digest

```
content-distribution cron fires (e.g., Friday 9am PT)
    |
    v
Bob (or Ezra) queries content.db:
    SELECT * FROM articles
    WHERE status = 'published'
    AND published_at >= date('now', '-7 days')
    |
    v
Compile digest content (titles, excerpts, URLs)
    |
    v
Create Resend Broadcast:
    POST api.resend.com/broadcasts
    Body: { audienceId: "...", subject: "Weekly Digest", html: "..." }
    |
    v
Send broadcast:
    POST api.resend.com/broadcasts/{id}/send
    (Resend handles throttling, unsubscribe links, list management)
    |
    v
email.db: record broadcast send (broadcast_id, sent_at, recipient_count)
```

## Data Flow: LLM Observability

```
Any agent makes LLM call
    |
    v
OpenClaw gateway processes LLM response
    |
    v
llm_output hook fires (if configured in openclaw.json)
    |
    v
Hook script appends to ~/clawd/logs/llm-usage.jsonl:
    { ts: "...", agent: "main", model: "claude-sonnet-4-5", input_tokens: 1200,
      output_tokens: 450, cost_usd: 0.0032 }
    |
    v
Morning briefing cron fires
    |
    v
Bob reads llm-usage.jsonl (last 24h), aggregates:
    - Total tokens by agent
    - Model distribution (Haiku/Sonnet/Opus ratio)
    - Turn counts
    - Anomalies (spike > 2x average)
    |
    v
Morning briefing: "Agent Observability" section added
```

## Data Flow: SecureClaw Runtime

```
External content arrives (web fetch, email, webhook)
    |
    v
SecureClaw plugin intercepts (runtime layer)
    |
    v
Content tagged as "untrusted" — behavioral rules applied:
    - Embedded prompt injection attempts blocked/flagged
    - Credential access requests gated
    - Destructive commands require confirmation
    |
    v
Agent processes sanitized content
```

---

## Component Table

| Component | New/Modified | Location | Communicates With | Notes |
|-----------|-------------|----------|-------------------|-------|
| content.db | MODIFIED | ~/clawd/agents/main/content.db | Ezra (write), all pipeline agents (read) | Add `notified_at` column to articles table |
| email.db | MODIFIED | ~/clawd/agents/main/email.db | Bob/Ezra (write), morning-briefing cron (read) | Add `subscribers` table |
| Resend Audiences | NEW (external) | api.resend.com/audiences | Ezra or Bob via resend-email skill | Synced from email.db subscribers table |
| Resend Broadcasts | NEW (external) | api.resend.com/broadcasts | Weekly digest cron via resend-email skill | Handles list management, unsubscribes |
| pitch-copy skill | NEW | ~/.openclaw/skills/pitch-copy/ | Quill or Bob (invoke) | SKILL.md with pitch/social copy protocol |
| content-distribution cron | NEW | openclaw cron system | Bob or Ezra (target) | Weekly digest trigger |
| Ezra (agent) | MODIFIED | ~/.openclaw/agents/ezra/ | content.db, resend-email skill, WordPress | Add distribution + pitch responsibilities |
| OpenClaw binary | MODIFIED | /home/ubuntu/.npm-global/bin/openclaw | All | v2026.2.6-3 → v2026.2.17 |
| SecureClaw plugin | NEW | ~/.openclaw/extensions/secureclaw/ | Gateway (runtime hook) | 51-check audit + 15 behavioral rules |
| llm-usage.jsonl | NEW | ~/clawd/logs/llm-usage.jsonl | Hook script (write), Bob morning briefing (read) | LLM call telemetry log |
| llm_output hook config | NEW | openclaw.json hooks.internal | Gateway → hook script | Unconfirmed exact key name in v2026.2.17 |
| morning-briefing cron | MODIFIED | openclaw cron system | Bob (target) | Add observability section reading llm-usage.jsonl |
| subscribers table (email.db) | NEW schema | email.db | Bob/Ezra (CRUD), resend-email skill | Seed list only, no public signup |

---

## Recommended Project Structure

```
~/.openclaw/
├── skills/
│   ├── resend-email/        # EXISTING — transactional send/receive
│   │   └── SKILL.md         # (modified to add Broadcast + Audience API calls)
│   └── pitch-copy/          # NEW — draft pitch/social copy from published content
│       └── SKILL.md
├── extensions/
│   └── secureclaw/          # NEW — security plugin (installed via npm/openclaw plugins)
~/clawd/
├── agents/
│   ├── main/                # Bob's workspace
│   │   ├── content.db       # EXISTING + modified schema
│   │   ├── email.db         # EXISTING + modified schema
│   │   └── ...
│   └── ezra/                # Ezra's workspace — add distribution WORKING.md updates
└── logs/
    └── llm-usage.jsonl      # NEW — LLM call telemetry
```

---

## Architectural Patterns

### Pattern 1: Status-Triggered Distribution

**What:** Watch content.db `status` field for `published` → trigger downstream notification as part of the publish step (Ezra's responsibility), not as a separate polling cron.

**When to use:** When notification is coupled to a discrete event (publish), not a time schedule.

**Why this fits:** Ezra already calls WordPress API as part of publish. Adding Resend notify after WordPress confirm is natural extension. Decouples notification timing from digest schedule. Prevents duplicate notifications if cron polls before `notified_at` is set.

**Example logic (in Ezra's WORKING.md or instructions):**
```
After WordPress publish succeeds:
1. UPDATE content.db SET status='published', published_url=?, published_at=NOW() WHERE id=?
2. SELECT email FROM subscribers WHERE unsubscribed_at IS NULL
3. For each subscriber: POST api.resend.com/emails with article summary + link
4. UPDATE content.db SET notified_at=NOW() WHERE id=?
5. Draft pitch copy → post to Slack for Andy's review
```

### Pattern 2: Broadcast for Digest (Not Transactional Loop)

**What:** Use Resend Broadcasts API for the weekly digest instead of sending individual transactional emails in a loop.

**When to use:** Sending same content to a list (digest, newsletter). Not when sending unique content per-recipient.

**Why this fits:** Broadcasts handle unsubscribe links automatically (legal compliance). Resend throttles broadcasts internally (doesn't burn 100/day transactional quota in one burst). Broadcasts are reviewable in the Resend dashboard before sending. Free tier allows marketing emails up to 1,000 contacts/month (separate from transactional quota).

**Quota implication:** Subscriber notification emails (individual, unique content per article) count against the 100/day transactional quota. Weekly digest sent as Broadcast counts against the separate marketing quota. Keep subscriber list small (seed only) to stay within free tier.

### Pattern 3: Plugin Enforces, Skill Audits

**What:** SecureClaw plugin provides runtime enforcement (active). ClawdStrike skill provides on-demand audit (passive). Run both, they serve different purposes.

**When to use:** SecureClaw = always-on guardrails. ClawdStrike = periodic security posture check.

**No conflict:** SecureClaw runs as a plugin (gateway-level). ClawdStrike runs as a skill (agent invokes on demand). They operate at different layers.

### Pattern 4: JSONL Hook Log → Bob Aggregates

**What:** LLM observability via a hook script that appends JSON Lines to a log file, which Bob reads and aggregates on the morning briefing schedule.

**When to use:** When you want observability without adding external infrastructure (no OTEL collector, no Prometheus, no Grafana).

**Trade-offs:**
- Pro: Zero new infrastructure. Bob already reads local files (verified-bundle.json pattern from ClawdStrike).
- Pro: Fits existing skill/cron pattern.
- Con: Log file grows unboundedly. Must add rotation (cron to truncate logs older than 30 days).
- Con: No real-time alerting — only surfaced at morning briefing.
- Con: Hook key name (`llm_input`/`llm_output`) must be verified against actual v2026.2.17 API.

---

## Build Order (Dependency-Aware)

Phase 24 must complete before Phases 25-28 because it upgrades the gateway binary. Phases 25-28 are independent after Phase 24 but execute sequentially.

```
Phase 24: OpenClaw Update + SecureClaw Install
  24a. Backup openclaw.json + cron jobs
  24b. npm install -g openclaw@latest (target: v2026.2.17)
  24c. openclaw doctor --fix
  24d. Verify gateway starts, Bob responds in Slack
  24e. openclaw plugins install secureclaw (or npm install -g @adversa-ai/secureclaw)
  24f. openclaw plugins enable secureclaw
  24g. Run SecureClaw 51-check audit
  24h. Apply SecureClaw hardening fixes
  24i. Verify 15 behavioral rules active (check openclaw.json for plugin config)
  NOTE: gateway.remote.url may need re-verification after update (known issue from MEMORY.md)

Phase 25: Post-Update Audit
  25a. openclaw cron list → verify all 20 cron jobs present
  25b. openclaw skill list → verify all 10 skills present
  25c. Heartbeat each of 7 agents
  25d. Test prompt injection with known payload → SecureClaw should block
  DEPENDS ON: Phase 24

Phase 26: LLM Observability
  26a. Check openclaw v2026.2.17 for available hook names (openclaw hooks list or docs)
  26b. Configure llm_output hook in openclaw.json (or diagnostics-otel if hooks unavailable)
  26c. Create hook script: appends to ~/clawd/logs/llm-usage.jsonl
  26d. Restart gateway, make test LLM calls, verify log populates
  26e. Modify morning-briefing cron payload to include observability section
  26f. Verify morning briefing shows agent observability section
  DEPENDS ON: Phase 24 (gateway must be v2026.2.17 for correct hook API)
  RISK: llm_input/llm_output hook names unconfirmed — verify before implementation

Phase 27: Email Domain Hardening
  27a. Verify WARMUP.md 5-step checklist (DNS, auth, inbox, monitoring)
  27b. Check bounce/complaint rates in Resend dashboard
  27c. If clean: update DNS _dmarc.mail.andykaufman.net → p=quarantine
  27d. Verify: dig TXT _dmarc.mail.andykaufman.net
  27e. Confirm morning briefing shows email health metrics
  DEPENDS ON: Phase 24 (gateway running), independent of 25-26

Phase 28: Platform Cleanup
  28a. gog auth scope reduction (remove 2 excess scopes, re-auth)
  28b. openclaw doctor → resolve deprecated auth profile warning
  28c. openclaw doctor → resolve legacy session key warning
  28d. Review openclaw.json for dmPolicy/allowFrom alias adoption
  28e. Verify gateway.remote.url still reachable from VPS (n8n relay)
  DEPENDS ON: Phase 24 (gateway running), independent of 25-27

NEW Content Distribution Phases (Post-v2.3 cleanup):
  Phase N: Content Distribution Setup
    Na. Add notified_at column to content.db articles table
    Nb. Create subscribers table in email.db (schema below)
    Nc. Create Resend Audience, sync initial subscribers
    Nd. Modify resend-email skill to add Broadcast + Audience API calls
    Ne. Create pitch-copy skill (SKILL.md)
    Nf. Update Ezra's instructions to handle post-publish notification + pitch copy draft
    Ng. Test: publish test article → verify subscriber notification fires
    Nh. Test: weekly digest broadcast sends to Audience
    DEPENDS ON: Phase 24 (gateway updated), Phase 27 (email domain hardened for deliverability)
    NOTE: build this after email hardening — don't send subscriber emails from p=none domain
```

---

## Schema: New Database Tables

### subscribers table (email.db)

```sql
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    source TEXT DEFAULT 'seed',          -- 'seed', 'manual', 'form'
    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at DATETIME,            -- NULL = active
    resend_contact_id TEXT,              -- Resend Audiences contact ID for sync
    notes TEXT
);
```

### articles table modification (content.db)

```sql
ALTER TABLE articles ADD COLUMN notified_at DATETIME;
ALTER TABLE articles ADD COLUMN notification_count INTEGER DEFAULT 0;
-- notified_at = NULL means notification not yet sent
-- Check: WHERE status='published' AND notified_at IS NULL to find unsent
```

### llm-usage.jsonl format

```jsonl
{"ts":"2026-02-17T09:00:00Z","agent":"main","model":"claude-sonnet-4-5","input_tokens":1200,"output_tokens":450,"session_key":"morning-briefing","cost_usd":0.0032}
{"ts":"2026-02-17T09:00:05Z","agent":"rangeos","model":"claude-haiku-4-5","input_tokens":800,"output_tokens":200,"session_key":"topic-research","cost_usd":0.0004}
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Resend Transactional API | curl from sandbox via resend-email skill (existing) | Subscriber notifications (individual emails per article) |
| Resend Audiences API | curl from sandbox via resend-email skill (new endpoints) | Manage subscriber list, sync from email.db |
| Resend Broadcasts API | curl from sandbox via resend-email skill (new endpoints) | Weekly digest — separate from transactional quota |
| SecureClaw plugin | openclaw plugins install + openclaw.json configPatch | Gateway-level runtime, auto-configures on install |
| OTEL collector (optional) | diagnostics-otel plugin if llm hooks unavailable | Only needed if hook-based observability doesn't work |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| content.db → Ezra | Ezra reads status column; triggers on 'published' | Ezra is responsible for post-publish distribution |
| email.db → resend-email skill | Skill reads subscribers table for notification sends | Ezra invokes skill; skill queries db |
| llm-usage.jsonl → morning briefing | Bob reads file, aggregates stats | Log rotation needed to prevent unbounded growth |
| SecureClaw plugin → all agents | Runtime interception at gateway level | No changes to individual agent configs needed |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: New "Distribution Agent" Instead of Extending Ezra

**What people do:** Create an 8th agent specifically for content distribution.

**Why it's wrong:** Ezra already owns the "publish" step. Distribution is the natural next step after publish. A new agent adds coordination overhead (inter-agent messaging, shared state) without benefit. At this scale, distribution is 2-3 extra API calls after the WordPress publish.

**Do this instead:** Extend Ezra's instructions/WORKING.md to include the post-publish notification + pitch copy draft steps.

### Anti-Pattern 2: Transactional Loop for Weekly Digest

**What people do:** Send the weekly digest by looping through subscribers and sending individual transactional emails.

**Why it's wrong:** Burns 100/day quota. No unsubscribe management. No throttling. If subscriber list grows past 100, hits quota wall immediately.

**Do this instead:** Use Resend Broadcasts API. Designed for this use case. Separate quota from transactional. Handles unsubscribes, throttling, and scheduling.

### Anti-Pattern 3: Skipping Backup Before OpenClaw Update

**What people do:** `npm install -g openclaw@latest` without backup.

**Why it's wrong:** Major version jumps (v2026.2.6 → v2026.2.17) have broken cron job format, session key canonicalization, and entrypoint paths in this deployment's history. Recovery without backup requires reconstructing all 20 cron job configs from memory or logs.

**Do this instead:** Always backup `~/.openclaw/openclaw.json` and export `openclaw cron list` output before update.

### Anti-Pattern 4: Treating DMARC Escalation as Risk-Free

**What people do:** Change p=none to p=reject immediately.

**Why it's wrong:** p=none → p=quarantine → p=reject is the correct escalation path. p=quarantine is the right target after warmup, not p=reject. p=reject drops emails that fail DMARC; p=quarantine routes them to spam. Wrong SPF include or misconfigured DKIM causes legitimate emails to disappear silently under p=reject.

**Do this instead:** Escalate from p=none to p=quarantine only. Monitor for 2 clean weeks before considering p=reject (which is out of scope for this milestone).

### Anti-Pattern 5: Sending Subscriber Notifications Before Email Hardening

**What people do:** Build the subscriber notification flow (Phase N), then do DMARC escalation (Phase 27) later.

**Why it's wrong:** Sending from a p=none domain to subscribers risks reputation damage. Subscribers may mark early emails as spam, damaging the domain score before it's properly warmed.

**Do this instead:** Complete Phase 27 (email hardening, DMARC escalation, confirm warmup clean) BEFORE launching subscriber notifications.

---

## Scalability Considerations

This is a personal deployment. Scaling is not a concern. For reference:

| Concern | Current Scale | If subscriber list grows |
|---------|--------------|--------------------------|
| Resend transactional quota | 100/day — article notifications use ~1-5/day | Sufficient for seed list (<100 subscribers) |
| Resend marketing quota | 1,000/month — weekly digest | Sufficient for ~250 active subscribers |
| LLM observability log | JSONL, <1KB per call | Rotate after 30 days; ~500KB/day max at current agent usage |
| SecureClaw context cost | 1,230 tokens per agent context | Fixed cost, not a scaling concern |
| content.db size | Grows with articles | SQLite handles thousands of rows fine |

---

## Open Questions (Must Verify Before Implementation)

1. **llm_input/llm_output hook names:** Are these valid event names in OpenClaw v2026.2.17? Run `openclaw hooks list` after update to confirm. Fallback: diagnostics-otel plugin or a custom hook on `session:end` that reads usage from session metadata.

2. **SecureClaw configPatch behavior:** Does `openclaw plugins install secureclaw` auto-merge the plugin config into openclaw.json, or does it require manual openclaw.json edits? The `configPatch` feature was proposed as a GitHub issue (#6792) — confirm it's released and supported in v2026.2.17.

3. **Resend free tier Broadcasts quota:** Confirmed: marketing emails separate from transactional. Verify exact monthly limit for Broadcasts on free tier (search results indicate 1,000 contacts/month for marketing).

4. **Ezra's current agent instructions:** Before adding distribution responsibilities, read Ezra's existing WORKING.md/SOUL.md to understand what triggers the current publish step, so the notification hook can be inserted correctly.

5. **gateway.remote.url after update:** MEMORY.md notes this was needed for CLI commands. Verify it still works after the version jump to v2026.2.17, as CLI behavior may have changed.

---

## Sources

- [SecureClaw GitHub (adversa-ai/secureclaw)](https://github.com/adversa-ai/secureclaw) — Plugin architecture, 51 checks, 15 behavioral rules, install pattern
- [SecureClaw Launch Press Release (PRNewswire)](https://www.prnewswire.com/news-releases/secureclaw-by-adversa-ai-launches-as-the-first-owasp-aligned-open-source-security-plugin-and-skill-for-openclaw-ai-agents-302688674.html) — Feature count confirmed, OWASP coverage
- [SecureClaw: First Open-Source Security Solution for OpenClaw (Adversa AI Blog)](https://adversa.ai/blog/adversa-ai-launches-secureclaw-open-source-security-solution-for-openclaw-agents/) — Layer-by-layer breakdown
- [OpenClaw Logging Documentation](https://docs.openclaw.ai/logging) — Gateway logging and diagnostics
- [diagnostics-otel plugin configuration](https://deepwiki.com/openclaw/openclaw/10-extensions-and-plugins) — OTEL plugin config fields, metrics exported
- [OpenClaw Hooks Documentation (openclawlab.com)](https://openclawlab.com/docs/hooks/) — Hook types, internal hooks, session-memory pattern
- [OpenClaw Observability (Shinzo Labs)](https://shinzo.ai/blog/openclaw-observability-how-to-track-openclaw-sessions-and-tasks) — Observability patterns for OpenClaw sessions
- [Instrumenting OpenClaw with LangWatch/OpenTelemetry](https://langwatch.ai/blog/instrumenting-your-openclaw-agent-with-opentelemetry) — OTEL integration alternative
- [Resend Audiences Introduction](https://resend.com/docs/dashboard/audiences/introduction) — Audience management API, contact import
- [Resend Broadcast API](https://resend.com/blog/broadcast-api) — Programmatic broadcast creation/send
- [Resend Broadcasts Documentation](https://resend.com/docs/dashboard/broadcasts/introduction) — Broadcast management workflow
- [Resend Manage Subscribers with Audiences](https://resend.com/blog/manage-subscribers-using-resend-audiences) — Audience/subscriber sync patterns
- [configPatch plugin manifest (OpenClaw Issue #6792)](https://github.com/openclaw/openclaw/issues/6792) — Auto-merge plugin config on install
- [OpenClaw Security Documentation](https://docs.openclaw.ai/gateway/security) — Baseline security config reference
- OpenClaw MEMORY.md (internal) — gateway.remote.url requirement, sandbox bind-mount patterns, update procedure

---

*Architecture research: 2026-02-17*
*Scope: v2.4 Content Distribution & Security Hardening integration points*
