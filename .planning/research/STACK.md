# Stack Research

**Domain:** OpenClaw AI companion — Security hardening, platform observability, email distribution
**Researched:** 2026-02-17
**Confidence:** HIGH (OpenClaw/SecureClaw), HIGH (Resend Broadcasts), MEDIUM (LLM hooks)

---

## v2.3 Stack Additions

This document covers NEW stack additions for v2.3. The v2.2 Resend email stack (transactional send/receive, n8n webhook relay, resend-email skill) remains unchanged and proven. Only deltas from v2.2 are documented below.

---

## 1. OpenClaw Platform Update (Phase 24)

### Core Update

| Technology | From | To | Purpose | Why |
|------------|------|----|---------|-----|
| `openclaw` npm package | v2026.2.6-3 | v2026.2.17 | Platform runtime | Patches CVE-2026-25253 (40+ security vulnerabilities fixed in v2026.2.12; further stability/config improvements in .17). Required before SecureClaw install |

**Update Command (on EC2):**

```bash
npm install -g openclaw@latest
# Then:
/home/ubuntu/.npm-global/bin/openclaw doctor --fix
systemctl --user restart openclaw-gateway.service
```

**v2026.2.17 Notable Changes (MEDIUM confidence — WebSearch, no official changelog page directly read):**
- TUI: resolves gateway target URL from `gateway.bind` mode (tailnet/lan) instead of hardcoded localhost — critical fix for this deployment (gateway binds tailnet, not loopback)
- Auth: bridges OpenClaw OAuth profiles into pi auth.json — improves model discovery for gog credentials
- Config: refreshes bindings per message without restart — bind changes now apply live
- `maxTokens` clamped to `contextWindow` — prevents invalid model config errors
- Session `--session <key>` honored in TUI even when `session.scope` is global

**v2026.2.12 Security Changes (HIGH confidence — multiple security news sources):**
- 40+ vulnerabilities patched across hooks, browser control, scheduling, messaging, gateway security
- Browser/web content treated as "untrusted by default" (prompt injection hardening)
- Exec approvals render forwarded commands in monospace for safer scanning

**Confidence:** MEDIUM on specific 2.17 features (WebSearch summaries only), HIGH on v2026.2.12 security patch significance

**Sources:**
- [OpenClaw npm package](https://www.npmjs.com/package/openclaw)
- [OpenClaw 2026.2.12 security coverage](https://cybersecuritynews.com/openclaw-2026-2-12-released/)
- [OpenClaw 2026.2.6 feature summary](https://www.neuralstackly.com/blog/openclaw-2026-2-6-update)
- [OpenClaw releases](https://github.com/openclaw/openclaw/releases)

---

## 2. SecureClaw Security Plugin (Phase 24)

### Installation: Clone + Local Plugin Install

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `secureclaw` (adversa-ai/secureclaw) | v2.1 | OWASP-aligned audit + hardening + runtime behavioral rules | First and only OWASP Top 10 Agentic Security plugin for OpenClaw. Open source. Git clone install (not npm registry). Released 2026-02-16 |

**Install Procedure:**

```bash
# On EC2 (SSH to 100.72.143.9)
cd ~
git clone https://github.com/adversa-ai/secureclaw.git
cd secureclaw
npm install
npm run build
/home/ubuntu/.npm-global/bin/openclaw plugins install -l .

# Deploy behavioral skill to agent workspace
npx openclaw secureclaw skill install
```

**What SecureClaw Provides:**

| Layer | What It Does | Details |
|-------|-------------|---------|
| Audit | 51 automated checks across 8 categories | Exposed gateway ports, weak file permissions, missing auth, plaintext credentials outside .env, disabled sandboxing |
| Hardening | Automated fixes for critical findings | Binds gateway to localhost (N/A — our gateway binds tailnet by design), locks file permissions, adds privacy/injection directives to agent identity |
| Behavioral rules | 15 rules loaded into agent context (~1,230 tokens) | External content sandboxed, credential access blocked, destructive commands gated, inter-agent communication rules |

**Security Framework Coverage:**
- OWASP Agentic Security Top 10: full
- CoSAI Agentic AI Security principles: full
- MITRE ATLAS: most categories

**Integration Notes for This Deployment:**
- Gateway binds to tailnet (100.72.143.9:18789), NOT loopback. SecureClaw's hardening module may flag this as "exposed." Accept/whitelist — tailnet-only access is our security model.
- Behavioral skill adds ~1,230 tokens to Bob's context window. With current Sonnet model (200k context), this is negligible.
- SecureClaw v2.1 is current as of 2026-02-16 (released day before research date). No npm registry package — must use git clone install path.

**Confidence:** HIGH (PR Newswire announcement, multiple corroborating tech news sources, GitHub repo verified, install procedure from multiple sources including official PR)

**Sources:**
- [SecureClaw GitHub](https://github.com/adversa-ai/secureclaw)
- [Adversa AI launch announcement](https://adversa.ai/blog/adversa-ai-launches-secureclaw-open-source-security-solution-for-openclaw-agents/)
- [SecureClaw PR Newswire](https://www.prnewswire.com/news-releases/secureclaw-by-adversa-ai-launches-as-the-first-owasp-aligned-open-source-security-plugin-and-skill-for-openclaw-ai-agents-302688674.html)

---

## 3. LLM Observability Hooks (Phase 26)

### Recommended Approach: OpenClaw Native Hooks + SQLite Log

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| OpenClaw `llm_input`/`llm_output` hooks | (platform built-in) | Capture per-call token usage, model, agent ID | Native to OpenClaw — no extra infrastructure. Hook payloads written to local file or SQLite, then Bob reads them to produce summaries |
| SQLite (existing `~/clawd/agents/main/email.db` or new `llm-usage.db`) | (existing) | Store hook payloads for aggregation queries | Already proven — email.db and content.db use same pattern. Bob's sandbox has bind-mount access |

**Do NOT use external observability SaaS (Langfuse, Helicone) for this deployment.** Reasons:
1. Single personal deployment — external SaaS adds credential management complexity for negligible benefit
2. Sends LLM conversation data to third parties (privacy concern for personal assistant)
3. OpenClaw hooks + SQLite covers OBS-01/02/03 requirements without new infrastructure

**Hook Configuration Pattern (openclaw.json):**

```json
{
  "hooks": {
    "llm_input": {
      "enabled": true,
      "path": "/workspace/hooks/llm-input.sh"
    },
    "llm_output": {
      "enabled": true,
      "path": "/workspace/hooks/llm-output.sh"
    }
  }
}
```

**Hook Script Pattern (shell, runs in sandbox):**

```bash
#!/bin/bash
# /workspace/hooks/llm-output.sh
# Receives JSON payload via stdin or env var — verify exact format from OpenClaw docs
# Write to SQLite for Bob to query later
echo "$HOOK_PAYLOAD" | sqlite3 /workspace/llm-usage.db \
  "INSERT INTO usage (ts, agent, model, input_tokens, output_tokens) VALUES (datetime('now'), '$AGENT_ID', '$MODEL', $INPUT_TOKENS, $OUTPUT_TOKENS);"
```

**IMPORTANT CAVEAT (LOW confidence on exact hook API):** The `llm_input`/`llm_output` hook names appear in the v2.3 requirements (OBS-01) and are consistent with OpenClaw's hooks architecture (`session-memory` hook exists as confirmed). However, exact payload format, env var names, and whether these specific hooks are available in v2026.2.17 could NOT be verified from official documentation. This is the highest-risk stack item — treat as requiring verification against `openclaw --help` or AGENTS.md after updating.

**Confidence:** LOW on exact hook names/API (requirements reference them but official docs not directly verified), HIGH on SQLite storage pattern (proven in this deployment)

**Sources:**
- [OpenClaw hooks discussion](https://github.com/openclaw/openclaw/issues/7724) — lifecycle hooks feature request
- [OpenClaw usage logging issue #14377](https://github.com/openclaw/openclaw/issues/14377) — per-agent token logging
- [Token Use docs](https://docs.openclaw.ai/reference/token-use)

---

## 4. Resend Audiences / Broadcasts for Subscriber Distribution (Future milestone, not v2.3)

**Status:** Research completed but NOT in v2.3 scope. Documents what's needed when subscriber digest features are added.

### New API Tier Required

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Resend Contacts API | v1 | Global contact management, opt-in/out | Resend renamed Audiences to Segments (2025). Contacts are now global entities identified by email address — not scoped to a single audience/segment |
| Resend Broadcasts API | v1 | Send digest emails to subscriber lists | 6 endpoints for create/update/send. Replaces `POST /emails` for bulk subscriber sends |

**Key API Endpoints (additions to v2.2 stack):**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/contacts` | Create global contact (subscriber opt-in) |
| GET | `/contacts` | List all contacts |
| GET | `/contacts/{id}` | Get contact details |
| PATCH | `/contacts/{id}` | Update contact (unsubscribe) |
| DELETE | `/contacts/{id}` | Remove contact |
| POST | `/contacts/{id}/segments` | Add contact to segment |
| POST | `/broadcasts` | Create broadcast |
| PATCH | `/broadcasts/{id}` | Update broadcast draft |
| POST | `/broadcasts/{id}/send` | Send or schedule broadcast |
| GET | `/broadcasts/{id}` | Get broadcast details |
| GET | `/broadcasts` | List broadcasts |
| DELETE | `/broadcasts/{id}` | Delete broadcast draft |

**Pricing Constraint:** Free tier allows 1,000 contacts. For subscriber list > 1,000, requires paid plan ($40/mo for 5,000 contacts). Current transactional email (100/day free) is unaffected.

**Integration with Existing Stack:** Bob's resend-email skill can be extended with `send_broadcast` and `manage_subscriber` functions. Same curl + Bearer token pattern. No new infrastructure needed — Broadcasts API uses same base URL and auth as transactional.

**Unsubscribe Flow:** Resend handles automatically. When a contact unsubscribes, they are skipped in future broadcasts. No custom unsubscribe handler needed.

**Confidence:** HIGH on API existence and endpoints (Resend official docs, multiple corroborating sources), MEDIUM on Audiences→Segments rename timing (confirmed as 2025 change but exact endpoint naming may differ from older docs)

**Sources:**
- [Resend Broadcast API blog](https://resend.com/blog/broadcast-api)
- [Resend Create Broadcast docs](https://resend.com/docs/api-reference/broadcasts/create-broadcast)
- [Resend Create Contact docs](https://resend.com/docs/api-reference/contacts/create-contact)
- [New Contacts Experience](https://resend.com/blog/new-contacts-experience)
- [Resend Audiences intro](https://resend.com/docs/dashboard/audiences/introduction)

---

## 5. Content Publish Notification Automation (Future milestone, not v2.3)

**Status:** No new stack additions needed. Implementation uses existing stack.

Content publish notifications (notifying subscribers when a WordPress article publishes) can be implemented entirely with:
- Existing WordPress REST API (Phase 16 — already integrated via Ezra agent)
- Existing resend-email skill (transactional) or Broadcasts API (bulk)
- Existing content.db `status = 'published'` + publish timestamp for trigger detection
- Existing cron pattern: poll content.db for newly-published articles, send notification

**No new dependencies.** This is a workflow composition, not a stack addition.

---

## What NOT to Add in v2.3

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Langfuse / Helicone (cloud LLM observability) | Sends conversation data to third parties; overkill for single-user personal deployment | OpenClaw native hooks + SQLite log |
| Sentry / Bugsnag (error tracking) | Adds external dependency for minimal gain; OpenClaw already logs to systemd journal | `journalctl --user -u openclaw-gateway` for error review |
| Resend Node.js SDK (`resend` npm) | Sandbox filesystem is read-only — npm install fails | Direct curl to Resend REST API (proven v2.2 pattern) |
| n8n workflow changes for broadcasts | Broadcasts go directly from sandbox to Resend API; no webhook relay needed for outbound | curl from sandbox |
| Docker image rebuild | SecureClaw plugin installs into OpenClaw plugin directory, not sandbox image | `openclaw plugins install` from host |

---

## Platform Constraints Reminder (Unchanged from v2.2)

| Constraint | Impact |
|-----------|--------|
| Sandbox filesystem is read-only | No `npm install` in sandbox. Use curl for all API calls |
| Gateway binds tailnet (100.72.143.9:18789) | `gateway.remote.url` must be set in openclaw.json for CLI commands. SecureClaw hardening may flag gateway binding — accept it |
| EC2 is t3.small (2GB RAM + 2GB swap) | SecureClaw audit is one-time scan, no persistent RAM overhead. Hook scripts are shell — negligible memory |
| Non-interactive SSH needs full binary path | Use `/home/ubuntu/.npm-global/bin/openclaw` not `openclaw` in SSH commands |

---

## Version Compatibility

| Component | Version | Compatible With | Notes |
|-----------|---------|-----------------|-------|
| OpenClaw | v2026.2.17 | SecureClaw v2.1 | SecureClaw targets current OpenClaw — released same week |
| SecureClaw | v2.1 | OpenClaw v2026.2.17 | Install AFTER OpenClaw update |
| Resend Contacts API | v1 | Existing resend-email skill | Additive endpoints — same auth, base URL |
| Node.js | 18.x | openclaw@2026.2.17 | EC2 has Node.js 18+ (confirmed from v2.2 work) |

---

## Sources Summary

| Source | Confidence | What It Informs |
|--------|-----------|-----------------|
| [OpenClaw npm](https://www.npmjs.com/package/openclaw) | HIGH | v2026.2.17 is latest, update procedure |
| [OpenClaw releases](https://github.com/openclaw/openclaw/releases) | HIGH | Changelog, version history |
| [SecureClaw GitHub](https://github.com/adversa-ai/secureclaw) | HIGH | Install procedure, v2.1, feature list |
| [SecureClaw PR Newswire](https://www.prnewswire.com/news-releases/secureclaw-by-adversa-ai-launches-as-the-first-owasp-aligned-open-source-security-plugin-and-skill-for-openclaw-ai-agents-302688674.html) | HIGH | Audit layers, behavioral rules, token cost |
| [OpenClaw security patch news](https://cybersecuritynews.com/openclaw-2026-2-12-released/) | HIGH | v2026.2.12 patched 40+ vulnerabilities |
| [Resend Broadcast API](https://resend.com/docs/api-reference/broadcasts/create-broadcast) | HIGH | Endpoints, parameters, send flow |
| [Resend Contacts API](https://resend.com/docs/api-reference/contacts/create-contact) | HIGH | Global contacts, CRUD endpoints |
| [New Contacts Experience](https://resend.com/blog/new-contacts-experience) | HIGH | Audiences renamed to Segments in 2025 |
| [OpenClaw hooks feature request #7724](https://github.com/openclaw/openclaw/issues/7724) | MEDIUM | Hook payload structure (community discussion) |
| [OpenClaw usage logging #14377](https://github.com/openclaw/openclaw/issues/14377) | MEDIUM | Per-agent token logging — feature in progress |

---

*Stack research for: pops-claw v2.3 Security & Platform Hardening*
*Researched: 2026-02-17*
