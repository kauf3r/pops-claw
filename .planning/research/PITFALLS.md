# Pitfalls Research

**Domain:** Security hardening + observability additions to existing AI companion (pops-claw v2.3)
**Researched:** 2026-02-17
**Confidence:** HIGH (most pitfalls derived from direct project history + official docs + known patterns)

> This file supersedes the v2.2-era PITFALLS.md. The v2.2 pitfalls (Resend MX/DMARC setup, agent email loops,
> webhook body metadata, quota math) are still valid and remain in the project's institutional knowledge —
> they are not repeated here. This file covers v2.3-specific pitfalls only.

---

## Critical Pitfalls

### Pitfall 1: OpenClaw Update Restores Default Config Values, Silently Overwriting Customizations

**What goes wrong:**
`npm install -g openclaw@latest` followed by `openclaw doctor --fix` may silently reset certain `openclaw.json` keys to new defaults when the upgrade introduces config schema changes. In particular, the `gateway.bind` address, `gateway.remote.url`, `agents.defaults.sandbox.docker.network`, and plugin `enabled` flags are candidates for reset. The service restarts cleanly and Bob responds to a ping — but 20 cron jobs are orphaned because a cron scheduler config key moved, or browser automation breaks because `docker.network` was reset to `none`.

**Why it happens:**
OpenClaw's `doctor --fix` is an opinionated migration tool. When the internal config schema changes between versions (which it does in major releases), `--fix` writes a fresh section with defaults rather than preserving custom values it doesn't recognize from the old schema path. This project has non-default values for `gateway.remote.url` (added to fix WebSocket CLI issues), `agents.defaults.sandbox.docker.network: bridge` (required for browser), and `discovery.mdns.mode: off` (from ClawdStrike audit). Any of these can be nuked.

**How to avoid:**
- **Before updating**: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.pre-v2.17.bak`
- After `doctor --fix`, run `diff ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.pre-v2.17.bak` and review every changed key
- Keep a local checklist of the non-default values this project requires (see "Looks Done But Isn't" section)
- Do NOT restart the service until the diff has been reviewed

**Warning signs:**
- `openclaw cron list` returns empty or fewer than 20 jobs after update
- Bob can't reach the CLI (WebSocket 1006 closure) — means `gateway.remote.url` was stripped
- Browser agent-browser commands fail with "net::ERR_INTERNET_DISCONNECTED" — means `docker.network` was reset to `none`
- `openclaw doctor` reports zero warnings but config is subtly broken

**Phase to address:** Phase 24 (Critical Security Update) — backup and diff step must be explicit in the plan

---

### Pitfall 2: Service Entrypoint Mismatch Causes Silent Startup Failure

**What goes wrong:**
The systemd service file references `dist/entry.js` as the binary entrypoint. Between v2026.2.6-3 and v2026.2.17, the entrypoint may have moved or renamed (this already happened once: `entry.js` → `index.js` during the v2.2 migration). If the service file is not updated, `systemctl --user start openclaw-gateway.service` exits cleanly (exit code 0) but the gateway never actually starts listening. `systemctl --user status` shows "active (running)" for a few seconds then goes to "failed" or just stops.

**Why it happens:**
Node.js services launched via ExecStart don't fail the systemd unit if the process exits with a non-zero exit code under some configs. The gateway appears to start, then the node process exits immediately because the wrong file is specified. `journalctl` has the real error but most people don't check it after seeing the restart succeed.

**How to avoid:**
- Run `openclaw doctor` immediately after update and before restarting the service — it flags entrypoint mismatches
- If doctor flags a mismatch, update the service file: `sed -i 's|old-path|new-path|' ~/.config/systemd/user/openclaw-gateway.service`
- After restart, verify with: `journalctl --user -u openclaw-gateway.service --since '2 min ago' | tail -30`
- Confirm gateway is actually listening: `curl -s ws://100.72.143.9:18789` (should get a WebSocket upgrade response, not a connection refused)

**Warning signs:**
- Service shows "active" briefly then "failed" or "inactive"
- `openclaw cron list` hangs or returns WebSocket error 1006
- `journalctl` shows "Cannot find module 'dist/entry.js'" or similar

**Phase to address:** Phase 24 (Critical Security Update) — include `openclaw doctor` as mandatory step before service restart

---

### Pitfall 3: SecureClaw Runtime Rules Block Legitimate Cron Payloads as Injection

**What goes wrong:**
SecureClaw's 15 runtime behavioral rules include injection detection that scans agent inputs for patterns resembling prompt injection. The existing cron jobs deliver payloads like `"You are receiving this morning briefing because it's 6 AM. Please synthesize the following data and respond to andy@..."` — natural language that can look like an injection attempt to a pattern-matching rule. SecureClaw blocks the payload delivery, the cron fires silently (returns "ok" status), but Bob never receives the briefing trigger.

More specifically: crons that deliver workspace file paths (`/workspace/emails/YYYY-MM-DD.md`), external URLs (content pipeline, Oura API results), or role-assumption text ("Act as the daily briefing agent and...") are the highest-risk payloads.

**Why it happens:**
Runtime behavioral rules designed to stop prompt injection are pattern-matched. They flag:
- External content being injected into agent context
- Role-assumption or persona override language
- File path references that could indicate exfiltration
- Instructions to "ignore" previous context
The rules are correct for their threat model, but the threat model assumes untrusted external input — and cron payloads are trusted, self-authored inputs. The distinction is not automatic.

**How to avoid:**
- Before enabling SecureClaw's runtime rules, audit ALL 20 cron job payloads against the published 15-rule list
- Add SecureClaw "trusted source" or "allowlist" config entries for the cron scheduler's session target (if the plugin supports it)
- If SecureClaw doesn't support allowlisting by source, rewrite high-risk cron payloads to use indirect triggering: instead of delivering the full prompt in the cron payload, deliver a short trigger word ("BRIEFING_TRIGGER") and have Bob look up the actual instructions from a workspace file
- Test EACH cron job explicitly after SecureClaw install, not just a sample

**Warning signs:**
- Morning briefing stops arriving in Slack after SecureClaw install
- Cron `lastStatus: ok` but no corresponding agent response
- SecureClaw audit log shows blocked events with the cron's sessionTarget

**Phase to address:** Phase 24 (install SecureClaw) AND Phase 25 (post-update audit must explicitly verify each cron fires)

---

### Pitfall 4: SecureClaw Blocks Browser Content Processing as External-Content Injection

**What goes wrong:**
SecureClaw's "external content sandboxed" rule is designed to treat browser-fetched web content as untrusted. This is the correct security posture (SEC-07 requirement). However, existing skills that use agent-browser to fetch web content and then pass it directly to the agent for processing (content pipeline research, market data fetching, WordPress publishing status) will trigger this rule. The agent will refuse to process the content, or SecureClaw will strip it before it reaches the model.

**Why it happens:**
The distinction between "legitimate agent workflow that processes external content" and "prompt injection via fetched web page" is exactly what SecureClaw is designed to enforce. It cannot know that the content pipeline fetching content for the `quill` writing agent is different from an attacker who tricked the browser into visiting a malicious page. The default rule likely applies to all content.

**How to avoid:**
- Read SecureClaw docs for "trusted action" or "workflow" configuration before installing — understand what granularity of allowlisting exists
- For browser content that must flow to the agent, use an intermediary workspace file: browser writes content to `/workspace/research/YYYY-MM-DD-topic.md`, agent reads the file — this separates "browser action" from "agent prompt"
- The content pipeline (quill, sage, ezra agents) likely already uses workspace files as intermediaries (v2.1 architecture) — verify this pattern holds

**Warning signs:**
- Content pipeline research phase fails silently after update
- WordPress publishing skill can't read page content
- Agent-browser skills complete without error but agent reports "no content found"

**Phase to address:** Phase 24 (SecureClaw install) — must pre-assess browser workflow impact before enabling runtime rules

---

### Pitfall 5: llm_input/llm_output Hooks Capture and Persist Sensitive Data

**What goes wrong:**
The observability hooks required by OBS-01 capture every LLM input and output across all 7 agents. This includes: email content (including inbound emails from patients/clients), calendar event details, Oura biometric data, voice notes (`VN:` prefix DMs), AirSpace Integration business information (vendor comparisons, security project details), and Gmail OAuth token operations. If the hook endpoint writes payloads to a log file or database, sensitive data accumulates in plaintext on the EC2 instance.

Specifically: the morning briefing and email-catchup crons pass AirSpace email context to the agent. The observability hook will capture those inputs verbatim.

**Why it happens:**
LLM observability hooks are designed to capture everything — that's the point. But "everything" in this system includes business-confidential and personally-sensitive data. The hook doesn't know to redact it, and log files are often left world-readable or backed up to places with weaker access controls.

**How to avoid:**
- Hook endpoint must write to a file with `chmod 600`, inside `~/.openclaw/` or `~/clawd/` — never `/tmp/`
- Do not log raw `llm_input` payloads — log only: timestamp, agentId, model, inputTokenCount, outputTokenCount, latency_ms, turn_id
- If content inspection is needed for anomaly detection, apply it in-memory in the hook handler and discard the raw payload — log only derived signals (topic classification, sentiment, length buckets)
- Add explicit PII patterns to strip before any persistence: email addresses, names, API keys, biometric values
- The hook endpoint running on the EC2 host (not inside the Docker sandbox) has no sandboxing — it's the host filesystem

**Warning signs:**
- Log files growing rapidly and containing recognizable email content in plaintext
- `ls -la` on the hook log directory shows non-600 permissions

**Phase to address:** Phase 26 (Agent Observability) — privacy-preserving logging must be the default design, not an afterthought

---

### Pitfall 6: Observability Hook Adds Synchronous Latency to Every Agent Turn

**What goes wrong:**
If the `llm_input`/`llm_output` hooks are configured as synchronous HTTP callbacks to a local endpoint (e.g., `http://localhost:8080/hook`), every agent turn blocks until the hook endpoint responds. If the hook handler does anything slow (file I/O, database write, aggregation), it adds latency to every cron job, every Slack DM response, and every briefing generation. A hook that takes 500ms adds 500ms to every turn. A hook that crashes or hangs causes the agent turn to timeout.

**Why it happens:**
Hook endpoints that feel "local" inspire over-confidence. "It's just writing to a file" seems instant but can block on a loaded t3.small. More importantly, if OpenClaw fires hooks synchronously (which is common for input hooks where the hook may need to gate the request), a hung hook brings the gateway to a stop.

**How to avoid:**
- Determine whether OpenClaw fires `llm_input`/`llm_output` hooks synchronously or asynchronously — check OpenClaw docs or v2026.2.17 changelog before Phase 26
- If synchronous: the hook handler MUST be non-blocking. Use append-only file writes (not database queries). No HTTP outbound calls in the hook handler.
- If asynchronous: verify hook payload delivery guarantees — are missed deliveries retried? If not, build a local ring buffer or SQLite log
- Test hook latency under load before enabling in production: `time curl -X POST http://localhost:PORT/hook -d '{"dummy":true}'` should be under 10ms
- Add a hard timeout on the hook endpoint (5 seconds max) so a hung hook doesn't stall the gateway

**Warning signs:**
- Agent Slack responses start arriving noticeably slower after enabling observability
- Cron job `lastDurationMs` values increase significantly vs. pre-observability baseline
- Gateway logs show "hook timeout" or "hook error" entries

**Phase to address:** Phase 26 (Agent Observability) — latency impact must be measured before Phase 26 is marked complete

---

## Moderate Pitfalls

### Pitfall 7: DMARC Escalation to p=quarantine Before Warmup Is Complete Burns Domain Reputation

**What goes wrong:**
The WARMUP.md 5-step checklist requires 2 clean weeks of sending before DMARC escalation. If DMARC is escalated to `p=quarantine` before the domain has sufficient sending history and engagement, two things happen simultaneously: (1) Resend's automated sends (daily briefings, email-catchup notifications) become subject to stricter processing, and (2) any authentication misalignment that was previously visible only in DMARC reports (because `p=none` only monitors) now causes emails to be quarantined. If there's a latent SPF or DKIM misalignment that wasn't caught during `p=none` phase, the first DMARC enforcement causes briefings to vanish silently.

**Why it happens:**
`p=none` is a reporting mode — it reveals misalignment in DMARC reports without acting on it. If you've been ignoring DMARC aggregate reports (which is easy — they go to the `rua` address and require parsing XML), you may have silent authentication failures that become quarantine events overnight when policy is changed.

**How to avoid:**
- Before escalating DMARC policy: read the DMARC aggregate reports (rua) for the most recent 14 days — look for `dkim=fail` or `spf=fail` rows
- Use a DMARC report analyzer (MXToolbox, dmarcian free tier, or `dmarc-report-analyzer` npm package) — don't parse the XML manually
- Verify: `dig TXT _dmarc.mail.andykaufman.net` shows current policy
- Verify: send a test email and check Gmail "Show Original" for `dmarc=pass`
- Escalate DMARC during a low-traffic window (Saturday morning) so that if something breaks, the volume of lost emails is low
- Keep `p=none` on the parent domain (`andykaufman.net`) — only escalate the subdomain record

**Warning signs:**
- DMARC reports show any `dkim=fail` or `spf=fail` entries before escalation
- Bounce rate on Resend dashboard increases after DMARC change
- Morning briefing emails stop appearing in inbox (move to quarantine folder)

**Phase to address:** Phase 27 (Email Domain Hardening) — DMARC aggregate report audit must be step 1

---

### Pitfall 8: Gmail OAuth Scope Reduction Breaks Existing Crons That Use Removed Scopes

**What goes wrong:**
CLN-01 requires removing excess Gmail OAuth scopes and re-authing with `gog auth`. The existing setup was granted `gmail.modify`, `gmail.settings.*`, and `calendar` scopes. The cleanup targets reducing to `gmail.readonly` and `calendar.readonly`. However, existing crons may use write-scope operations: the email-catchup cron marks emails as read (requires `gmail.modify`), and the AirSpace email monitor may archive or label processed emails. After scope reduction and re-auth, these operations silently fail with a 403 from the Gmail API.

**Why it happens:**
Scope reduction is done at the OAuth credential level, not at the skill level. The skills and crons aren't updated to match. The gog CLI returns an error from the Gmail API, but if the cron delivers this error to the agent silently (not via Slack alert), it's invisible.

**How to avoid:**
- Before re-authing: audit every cron job and skill that calls `gog gmail` or `gog calendar` — list the specific operations and their required scope
- Map operations to minimum required scopes:
  - `gog gmail search` → `gmail.readonly`
  - `gog gmail send` → `gmail.send` (not covered by readonly OR modify — separate scope)
  - `gog gmail modify` (mark read, label, archive) → `gmail.modify`
  - `gog calendar events` (read) → `calendar.readonly`
  - `gog calendar events create` → `calendar` (write scope)
- The correct "reduced" set is probably `gmail.readonly`, `gmail.send`, `gmail.modify`, `calendar.readonly` — not the overly restrictive `readonly` only
- Test every affected cron manually after re-auth before considering CLN-01 done

**Warning signs:**
- Email-catchup cron succeeds but emails remain marked unread
- AirSpace email monitor stops categorizing emails into labels after scope change
- `gog gmail` commands return 403 in cron logs

**Phase to address:** Phase 28 (Platform Cleanup)

---

### Pitfall 9: Cron DM Sessions Lost After Gateway Restart During Update

**What goes wrong:**
This is a documented known issue from project memory: "Gateway restart clears DM sessions. After restart, cron `sessions_send` to DM channels fails. User must DM Bob first to re-establish." The v2026.2.17 update requires a gateway restart. If the update is done mid-day and no DM is sent to Bob afterward, the next cron that delivers via Slack DM (evening recap, alert) will fail silently. The cron shows `lastStatus: ok` but the Slack message never arrives.

**Why it happens:**
OpenClaw holds Slack DM session state in memory. The DM channel binding (which maps Bob's Slack DM to a persistent session) is established lazily on first message. A gateway restart clears this binding. The cron attempts to send to the DM session ID that no longer exists. This silently succeeds at the transport layer (no error) but the message is dropped.

**How to avoid:**
- Immediately after restarting the gateway post-update, send a DM to Bob via Slack and wait for a response
- This re-establishes the DM session before any crons fire
- Schedule the update for a time that allows 10-15 minutes for post-restart verification before the next cron fires (check `openclaw cron list` for `nextRunAtMs` of all active jobs)
- If a cron fires before the DM session is re-established, it's a lost message — not recoverable

**Warning signs:**
- No Slack DM from Bob for hours after update, even though crons should have fired
- `openclaw cron list` shows `lastStatus: ok` but no Slack message arrived

**Phase to address:** Phase 24 (Critical Security Update) — post-restart DM re-establishment must be explicit in the plan

---

### Pitfall 10: `openclaw doctor` "Zero Warnings" Is Not a Correctness Signal

**What goes wrong:**
After the update and `doctor --fix`, `openclaw doctor` reports zero warnings. This is used as the success criterion for Phase 24. But `doctor` only checks schema validity and known config patterns — it does NOT verify that 20 cron jobs are still configured correctly, that 7 agents are all responding, or that skills are still detected. A "passing" doctor is necessary but not sufficient.

**Why it happens:**
`openclaw doctor` is a configuration validator, not an integration test. It validates that the config file is well-formed and that known services are reachable. It doesn't test the full operational stack.

**How to avoid:**
- Phase 24 success criteria should include: `openclaw cron list | wc -l` (should be 20+), `openclaw skill list` (10 skills), all 7 agents respond to a ping
- Phase 25 (Post-Update Audit) is designed exactly for this — don't collapse the two phases
- The operational verification in Phase 25 is the real correctness signal

**Warning signs:**
- Doctor passes but Bob doesn't respond to a Slack message
- Doctor passes but `openclaw cron list` returns fewer entries than expected

**Phase to address:** Phase 25 (Post-Update Audit) must not be skipped even if Phase 24 appears clean

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip DMARC report review before escalation | Faster milestone completion | Silent quarantine of all outbound emails | Never — takes 15 min max |
| Enable all SecureClaw rules at once without testing | Simpler config | Multiple cron jobs silently breaking | Never — test rule categories individually |
| Use `full_access` Resend key in sandbox for convenience | No permission errors | Key exposure via prompt injection | Never — use `sending_access` in sandbox |
| Log full `llm_input` payloads for debugging | Easier anomaly detection | PII and business data in plaintext logs | Only with `chmod 600` and no backup |
| Skip `gateway.remote.url` verification after update | Faster execution | All CLI cron management commands fail with 1006 | Never — it's a 30-second check |
| Re-auth Gmail with "all scopes" instead of audited minimal set | No permission failures | Defeats the purpose of CLN-01 | Never |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenClaw update | Running `doctor --fix` without backup | Backup config, run `--fix`, diff the result before restart |
| SecureClaw install | Enabling all 15 runtime rules immediately | Audit cron payloads first; enable rules in categories with testing between each |
| llm hooks | Pointing hook at an HTTP server in Docker sandbox | Hook endpoint must be on host (EC2), not inside the sandbox |
| DMARC escalation | Changing `_dmarc.mail.andykaufman.net` record without reading aggregate reports | Parse 14 days of DMARC reports for failures first |
| Gmail scope reduction | Re-authing without mapping current operations to scopes | Enumerate all `gog gmail` operations across crons/skills before changing scopes |
| t3.small under load | Running the OpenClaw update + doctor + SecureClaw install in one session while crons are active | Update during low-traffic window; check swap usage during install |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous observability hooks | Every agent turn adds hook latency | Verify async delivery; use non-blocking file writes | When hook endpoint has >50ms latency |
| All 20 crons firing at once post-update | t3.small RAM exhaustion (2GB + 2GB swap) | Stagger cron verification; don't trigger all manually at once | When 5+ crons fire simultaneously |
| DMARC report volume after escalation | rua mailbox fills up; reports stop arriving | Set rua to a mailbox you actually check; or use a report aggregator service | After first 7 days at p=quarantine |
| SecureClaw 51-check audit on a loaded host | Audit script causes OOM | Run audit during low-traffic window | On t3.small with Docker + agent active |

---

## Security Mistakes

Domain-specific security issues for this milestone.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Observability hook logs persist in `/tmp/` | Logs wiped on reboot AND readable by any process | Write to `~/.openclaw/observability/` with `chmod 700` dir |
| SecureClaw allowlist configured too broadly | Defeats runtime protection | Allowlist by specific session target or cron job ID, not "all cron jobs" |
| Posting observability summary to public Slack channel | Token usage patterns and agent behaviors exposed | Observability section in morning briefing goes to Andy's DM only, not #clawdbot |
| Running OpenClaw update while gateway has active sessions | In-flight agent turns can corrupt state | Drain active sessions before update (check `openclaw sessions list`) |
| Not rotating Resend `sending_access` key after major update | If key was logged during update output, it's compromised | Rotate Resend key as standard practice after any major update |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Phase 24 Complete:** Doctor passes AND all 20 crons still listed AND Bob responds to DM AND `gateway.remote.url` still present in config
- [ ] **SecureClaw Installed:** Audit runs AND 15 runtime rules are active (not just registered) AND at least one test cron has been verified post-install
- [ ] **Observability Enabled:** Hooks fire AND log file exists with correct permissions (`chmod 600`) AND latency impact is measured (< 50ms per hook call)
- [ ] **DMARC Escalated:** DNS record shows `p=quarantine` AND a test email was sent AND received in inbox (not spam) AND Resend dashboard shows no new bounces for 48 hours post-escalation
- [ ] **Gmail Scopes Reduced:** `gog auth list` shows reduced scopes AND email-catchup cron still marks emails as read AND AirSpace email monitor still functions
- [ ] **Config Diff Reviewed:** `openclaw.json` after update has `discovery.mdns.mode: off`, `agents.defaults.sandbox.docker.network: bridge`, `gateway.remote.url` set, and all 7 agent configs present

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Config values nuked by doctor --fix | LOW | Restore from `.pre-v2.17.bak`, apply only the changes that doctor flagged as required, restart |
| SecureClaw blocking crons | LOW | Disable SecureClaw runtime rules (`secureclaw.runtime.enabled: false`), restart gateway, verify crons fire, re-enable rules one category at a time |
| Observability hook causing latency | LOW | Disable hook endpoint in openclaw.json, restart, rewrite hook handler to be non-blocking |
| DMARC p=quarantine breaking sends | MEDIUM | Change DNS record back to `p=none` immediately (propagates in minutes), diagnose authentication failure from reports, fix alignment, re-escalate |
| Gmail scope reduction breaking crons | MEDIUM | Re-auth gog with correct expanded scopes (`gog auth add --manual`), verify token scopes, re-test affected crons |
| DM sessions lost after restart | LOW | DM Bob "hi" from Slack, wait for response, all subsequent crons will deliver normally |
| Observability logs contain PII | HIGH | Delete log files, audit for copies in backups, implement redaction in hook handler before re-enabling |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Config values nuked by doctor --fix (Pitfall 1) | Phase 24 | Diff openclaw.json before/after update |
| Service entrypoint mismatch (Pitfall 2) | Phase 24 | journalctl after restart shows no entrypoint error |
| SecureClaw blocking cron payloads (Pitfall 3) | Phase 24 + Phase 25 | Each of 20 crons verified to fire post-install |
| SecureClaw blocking browser workflows (Pitfall 4) | Phase 24 | Content pipeline research test after SecureClaw |
| Observability hooks capturing sensitive data (Pitfall 5) | Phase 26 | Log file audit; no recognizable email/biometric content |
| Observability hooks adding latency (Pitfall 6) | Phase 26 | Latency measurement before/after hook enable |
| DMARC escalation before warmup complete (Pitfall 7) | Phase 27 | DMARC report review; test email in inbox not spam |
| Gmail scope reduction breaking crons (Pitfall 8) | Phase 28 | All gog-dependent crons verified post re-auth |
| DM sessions lost after gateway restart (Pitfall 9) | Phase 24 | DM Bob immediately after restart; confirm response |
| doctor "zero warnings" not a correctness signal (Pitfall 10) | Phase 25 | Explicit cron/skill/agent count verification |

---

## Sources

- Project MEMORY.md — "Gateway restart clears DM sessions" (confirmed operational pitfall)
- Project MEMORY.md — "Service entrypoint: doctor flags mismatches (e.g. entry.js → index.js) — always check after update" (confirmed operational pitfall)
- Project MEMORY.md — "gog auth add --manual over SSH: Use Python subprocess to handle interactive OAuth" (confirmed operational pitfall)
- Project findings.md — Version Update section: entrypoint migration, state dir symlinks, service file changes
- [DMARC Policy Options — MxToolbox](https://mxtoolbox.com/dmarc/details/dmarc-tags/dmarc-policy-options) — p=quarantine inheritance and enforcement behavior
- [DMARC Quarantine vs. Reject — Fortra Email Security](https://emailsecurity.fortra.com/blog/pros-cons-dmarc-reject-vs-quarantine) — staged escalation recommendation
- [What DMARC Policy Should Senders Use in 2025? — Email on Acid](https://www.emailonacid.com/blog/article/email-deliverability/why-strong-dmarc-policy/) — legitimate email quarantine risk
- [LLM Observability Best Practices 2025 — Maxim](https://www.getmaxim.ai/articles/llm-observability-best-practices-for-2025/) — async processing, latency, PII handling
- [AI Runtime Security False Positives — Acuvity](https://acuvity.ai/ai-runtime-security/) — intent-based vs. pattern-matching, false positive tradeoffs
- [Runtime AI Agent Protection — Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/01/23/runtime-risk-realtime-defense-securing-ai-agents/) — runtime rule behavioral impacts
- [Resend Account Quotas and Limits](https://resend.com/docs/knowledge-base/account-quotas-and-limits) — quota math: 100/day hard cap (carries forward from v2.2 pitfall)
- [dmarcian — Policy Modes: Quarantine vs Reject](https://dmarcian.com/policy-modes-quarantine-vs-reject/) — report-before-enforce discipline

---
*Pitfalls research for: pops-claw v2.3 Security & Platform Hardening*
*Researched: 2026-02-17*
