# Project Research Summary

**Project:** pops-claw v2.3 — Security & Platform Hardening
**Domain:** AI companion hardening, LLM observability, email domain hardening, and platform cleanup for existing OpenClaw/EC2 deployment
**Researched:** 2026-02-17
**Confidence:** HIGH (SecureClaw, DMARC), MEDIUM-HIGH (architecture), LOW (llm hook API names)

## Executive Summary

This is a hardening and observability milestone for an established personal AI companion deployment, not a greenfield build. The existing stack (OpenClaw v2026.2.6-3, 7 agents, 20 crons, 10 skills, Resend transactional email, Tailscale-only access) is fully operational. v2.3 adds security layers and visibility tooling on top without disrupting the live system. The recommended approach is to execute phases sequentially in dependency order: update the platform binary first (Phase 24), verify nothing broke (Phase 25), then add observability (Phase 26), harden email domain (Phase 27), and clean up platform config (Phase 28).

The single highest-risk action in this milestone is the OpenClaw binary update (v2026.2.6-3 to v2026.2.17). This deployment has non-default config values (`gateway.remote.url`, `docker.network: bridge`, `discovery.mdns.mode: off`) that `doctor --fix` has historically silently overwritten during major upgrades. SecureClaw installation immediately follows — its 15 runtime behavioral rules can silently break existing cron payloads by flagging legitimate self-authored instructions as prompt injection. Both risks are manageable with explicit backup-diff-verify steps documented in the plans.

Content distribution features (subscriber notifications, weekly digest, pitch copy) are scoped to a future v2.4 milestone. They are architecturally well-understood and depend on Phase 27 (DMARC hardening) completing cleanly before subscriber sends begin. The research for those features is complete and captured in FEATURES.md and ARCHITECTURE.md so the v2.4 roadmap can start without additional research.

## Key Findings

### Recommended Stack

The v2.3 stack additions are minimal and targeted. The v2.2 proven stack (Resend transactional API via curl, SQLite databases, n8n webhook relay, Tailscale networking) remains entirely unchanged. Three additions are required: (1) OpenClaw binary update to v2026.2.17 to patch CVE-2026-25253 and 40+ vulnerabilities from the v2026.2.12 security release; (2) SecureClaw v2.1 plugin installed via git clone and `openclaw plugins install -l .` (not npm registry — git clone only); and (3) LLM observability via native OpenClaw hooks writing to `~/clawd/logs/llm-usage.jsonl`. External observability SaaS (Langfuse, Helicone, Datadog) is explicitly excluded — privacy risk and overkill for a single-user personal deployment.

**Core technologies:**
- `openclaw` v2026.2.17: Platform runtime update — patches 40+ CVEs including CVE-2026-25253; required before SecureClaw install
- `secureclaw` v2.1 (adversa-ai/secureclaw): OWASP-aligned security plugin — 51-check audit + 15 behavioral runtime rules + 70+ injection patterns; git clone install only
- OpenClaw `llm_input`/`llm_output` hooks + JSONL log: LLM observability — native platform hooks, zero new infrastructure, Bob aggregates from log file in morning briefing
- Resend Audiences/Broadcasts API: Documented for future v2.4 — separate marketing quota from transactional, automatic unsubscribe handling

**Critical version constraint:** SecureClaw v2.1 targets OpenClaw v2026.2.17 released the same week. Install SecureClaw AFTER updating OpenClaw, not before.

**Unresolved stack item (LOW confidence):** Hook names `llm_input`/`llm_output` appear in requirements and community discussions (GitHub #16724, changelog reference) but are not confirmed in official OpenClaw docs. Must run `openclaw hooks list` after v2026.2.17 update to verify. Fallback: `diagnostics-otel` plugin with local file exporter.

### Expected Features

The v2.3 feature set is security and observability only. Content distribution features are deferred to v2.4 pending email domain hardening. Research identified 5 feature clusters (SecureClaw, LLM observability, subscriber notifications, weekly digest, pitch copy) — only the first two are in scope for v2.3.

**Must have (v2.3 table stakes):**
- OpenClaw update to v2026.2.17 — CVE-2026-25253 is unpatched; security obligation
- SecureClaw 51-check automated audit — produces structured JSON report; run before hardening
- SecureClaw 15 behavioral runtime rules — active prompt injection defense; ~1,230 tokens context cost (acceptable on Sonnet)
- llm_input/llm_output hook configuration — no observability data without hooks; all downstream analysis depends on this
- Per-agent token usage aggregation in morning briefing — daily operational visibility without manual querying
- DMARC escalation from p=none to p=quarantine — blocks domain spoofing; prerequisite for v2.4 subscriber sends
- Post-update audit of all 20 crons, 10 skills, 7 agents — `doctor` passing is not sufficient; must verify operational stack

**Should have (v2.3 differentiators):**
- Anomaly detection with thresholds in observability section — "Landos ran 120 turns vs usual 8" is actionable; simple algorithm, high value
- Email health metrics (bounce/complaint rate) in morning briefing — early warning for domain reputation
- Gmail OAuth scope reduction to minimal required set — reduce attack surface without breaking existing operations

**Defer to v2.4:**
- Subscriber notification emails — requires DMARC hardening first; p=none domain sending to subscribers risks reputation damage
- Weekly digest email — same dependency; requires p=quarantine before activating subscriber sends
- Pitch copy generation workflow — no urgency; well-understood implementation, no blocking dependencies
- OpenTelemetry export — no external backend configured; overkill for single-user deployment

**Anti-features confirmed (do not build):**
- SecureClaw as a real-time intercepting firewall — OpenClaw has no request interception API; runtime rules work via Bob's judgment
- Full LLM prompt/response logging — PII risk; log metadata only (token counts, model, agentId, duration)
- Running SecureClaw audit inside Docker sandbox — needs host-level data (iptables, systemd, file perms); must run on host
- Automated SecureClaw hardening without human review — could break Bob's identity (SOUL.md) or gateway config

### Architecture Approach

The architecture is additive to an existing proven system. The existing 7-agent content pipeline (Vector researches → Quill writes → Sage reviews → [human approves] → Ezra publishes) is unchanged. Three integration points are added as layers: SecureClaw plugin runs at the gateway level (no individual agent config changes needed), LLM hooks write to a JSONL log that Bob reads on morning briefing schedule (same pattern as the ClawdStrike verified-bundle.json), and DMARC escalation is a DNS record change with no code involved.

**Major components (v2.3):**
1. OpenClaw gateway v2026.2.17 — updated binary with CVE patches + correct tailnet-binding TUI fix
2. SecureClaw plugin (gateway-level) — 51-check audit runner + 15 behavioral rules in agent context; installed at `~/.openclaw/extensions/secureclaw/`
3. LLM observability hook + JSONL log — hook script appends per-call metadata to `~/clawd/logs/llm-usage.jsonl` (chmod 600)
4. Morning briefing cron (modified) — gains "Agent Observability" section aggregating llm-usage.jsonl; 24h rolling per-agent stats + anomaly flags
5. DNS DMARC record (_dmarc.mail.andykaufman.net) — p=none → p=quarantine after confirming 14-day aggregate report health

**Key patterns to follow:**
- Plugin Enforces / Skill Audits: SecureClaw plugin = always-on runtime. ClawdStrike skill = periodic on-demand audit. No conflict, different layers.
- JSONL Hook Log → Bob Aggregates: zero new infrastructure; proven pattern from ClawdStrike verified-bundle.json consumption
- Backup / Update / Diff / Verify: mandatory config backup before update, diff after `doctor --fix`, verify non-default values checklist before restart

**Architecture open questions (must verify during Phase 26 planning):**
- Are `llm_input`/`llm_output` valid hook event names in v2026.2.17? Run `openclaw hooks list` post-update.
- Does SecureClaw `configPatch` auto-merge into openclaw.json on install, or require manual JSON editing?
- Does `gateway.remote.url` survive the version jump to v2026.2.17 (or does `doctor --fix` strip it)?

### Critical Pitfalls

1. **`doctor --fix` silently overwrites non-default config values** — Back up `~/.openclaw/openclaw.json` before update. After `doctor --fix`, diff against backup. Verify `gateway.remote.url`, `docker.network: bridge`, and `discovery.mdns.mode: off` are preserved before restarting. Recovery: restore from backup, apply only the changes doctor flagged.

2. **SecureClaw runtime rules block existing cron payloads as injection** — Audit ALL 20 cron job payloads against the 15 behavioral rules before enabling. Crons that deliver role-assumption language, file paths, or external URLs are highest risk. Enable rules in categories with cron verification between each; rewrite high-risk payloads to use short trigger words pointing to workspace instruction files.

3. **DM sessions lost after gateway restart** — After ANY gateway restart (including the v2026.2.17 update), immediately DM Bob in Slack and wait for a response before the next cron fires. Lost before DM re-establishment = not recoverable.

4. **`doctor` zero warnings is not a correctness signal** — Doctor validates config schema, not operational stack. Phase 25 post-update audit (20 crons listed, 10 skills present, 7 agents responding) is the real correctness test. Do not collapse Phase 25 into Phase 24.

5. **Observability hooks capture sensitive PII** — LLM hooks will capture email content, calendar details, Oura biometrics, and AirSpace business data. Hook scripts must log metadata only (timestamp, agentId, model, token counts, session_key). Log file must be `chmod 600`. Never log raw `llm_input` payloads.

6. **DMARC escalation before warmup complete burns domain reputation** — Read 14 days of DMARC aggregate reports (rua) before escalating. Any `dkim=fail` or `spf=fail` rows = do not escalate yet. Escalate only subdomain record, not parent domain. Target p=quarantine, not p=reject.

## Implications for Roadmap

The v2.3 roadmap has a clear dependency chain that dictates phase order. The existing 5-phase structure (Phases 24-28) from the requirements document is validated by research and should be preserved as-is.

### Phase 24: Critical Security Update (OpenClaw + SecureClaw)
**Rationale:** Platform binary must be updated before any other work — CVE-2026-25253 is unpatched, and SecureClaw requires v2026.2.17. This is the highest-risk phase because the update can silently break 20 crons, browser automation, and CLI connectivity.
**Delivers:** Patched gateway + SecureClaw audit report + 15 behavioral rules active
**Addresses:** OpenClaw update, SecureClaw Layer 1 audit, Layer 2 hardening, Layer 3 behavioral rules
**Avoids:** Pitfall 1 (config overwrite), Pitfall 2 (service entrypoint mismatch), Pitfall 3 (cron blocking by runtime rules), Pitfall 9 (DM session loss after restart)
**Must include:** config backup step, post-`doctor` diff, DM re-establishment verification, cron payload pre-audit before SecureClaw rules activate

### Phase 25: Post-Update Audit
**Rationale:** Separate from Phase 24 because `doctor` passing is not sufficient. Operational verification (all 20 crons, 10 skills, 7 agents, browser automation, SecureClaw injection test) requires dedicated focus and must not be rushed inside the update phase.
**Delivers:** Confirmed operational stack with SecureClaw active and verified
**Avoids:** Pitfall 10 (`doctor` false pass), Pitfall 4 (SecureClaw blocking browser workflows)
**Must include:** explicit cron count check (`openclaw cron list | wc -l` — expect 20+), prompt injection test with known payload, browser workflow smoke test

### Phase 26: Agent Observability
**Rationale:** Depends on Phase 24 (hooks require v2026.2.17). Independent of Phases 27-28. Delivers daily visibility into the 7-agent system before adding more capability in v2.4.
**Delivers:** LLM hook configured, llm-usage.jsonl populating, morning briefing gains observability section with per-agent stats and anomaly flags
**Uses:** OpenClaw native hooks + JSONL log + existing morning briefing cron (proven pattern)
**Avoids:** Pitfall 5 (PII in logs), Pitfall 6 (synchronous hook latency)
**Must verify first:** Run `openclaw hooks list` to confirm hook names before implementing; measure latency before/after hook enable

### Phase 27: Email Domain Hardening
**Rationale:** Independent of Phases 25-26. Must complete before v2.4 subscriber sends begin. DMARC escalation is a DNS change with meaningful risk if done before warmup is confirmed.
**Delivers:** DMARC at p=quarantine, email health metrics in morning briefing
**Avoids:** Pitfall 7 (premature DMARC escalation)
**Must include:** 14-day DMARC aggregate report review as mandatory first step, test email inbox confirmation post-escalation, Saturday timing for low-volume window

### Phase 28: Platform Cleanup
**Rationale:** Independent of Phases 25-27. Lowest risk phase. Gmail scope reduction requires careful operation-to-scope mapping before re-auth — this is the main risk in this phase.
**Delivers:** Reduced OAuth scope, resolved doctor warnings, config alias adoption
**Avoids:** Pitfall 8 (scope reduction breaking crons)
**Must include:** Enumerate all `gog gmail` operations across crons/skills BEFORE re-authing (correct minimum scope is likely `gmail.readonly` + `gmail.send` + `gmail.modify` + `calendar.readonly`, not readonly-only)

### Phase Ordering Rationale

- Phase 24 is a prerequisite for all others: binary update required for SecureClaw (version dependency) and observability hooks (new API in v2026.2.17)
- Phase 25 must follow Phase 24 immediately: operational verification before layering more changes; a broken cron is harder to diagnose with 3 more changes on top
- Phases 26-28 are independent of each other; current ordering (observability → email hardening → cleanup) reflects risk priority, not strict dependency
- Content distribution (v2.4) hard dependency on Phase 27: sending subscriber emails from a p=none domain risks domain reputation before the list is established

### Research Flags

Phases needing deeper research or verification during planning:
- **Phase 26:** llm hook API names are LOW confidence. Do not write Phase 26 plan until `openclaw hooks list` is verified post-Phase 24. If `llm_input`/`llm_output` don't exist, pivot to `diagnostics-otel` plugin with local file exporter as documented in ARCHITECTURE.md.
- **Phase 24 (SecureClaw configPatch):** Whether `openclaw plugins install` auto-merges plugin config into openclaw.json is unconfirmed (GitHub issue #6792 — proposed, not verified released). Check during Phase 24 execution.

Phases with well-documented standard patterns (skip additional research):
- **Phase 25:** Verification checklist is fully known; no research needed — explicit count checks and smoke tests.
- **Phase 27 (DMARC):** DNS record change with established escalation path; process is well-documented from multiple authoritative sources.
- **Phase 28 (Gmail scopes):** gog auth re-auth procedure is confirmed from MEMORY.md. Risk is operational mapping, not technical unknowns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH (SecureClaw, Resend) / LOW (llm hooks) | SecureClaw verified via PR Newswire + GitHub + official blog. llm hook names `llm_input`/`llm_output` not confirmed in official OpenClaw docs — only requirements and community discussion |
| Features | HIGH | v2.3 scope is well-defined. Anti-features and deferral decisions are clear. v2.4 content distribution cluster is well-researched for future roadmap. |
| Architecture | MEDIUM-HIGH | Resend Broadcasts/Audiences patterns confirmed. SecureClaw plugin install pattern confirmed. JSONL hook log pattern fits deployment. Two open questions remain (hook names, configPatch). |
| Pitfalls | HIGH | 6 of 10 pitfalls derived directly from project MEMORY.md (confirmed operational history). 4 from official docs and security research. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **llm hook API names (Phase 26 blocker):** Cannot finalize Phase 26 plan until verified. Action: immediately after Phase 24 update, run `openclaw hooks list` before writing any Phase 26 implementation plan.
- **SecureClaw configPatch behavior (Phase 24):** Check during Phase 24 execution whether `openclaw plugins install` auto-merges config. If not, manual `openclaw.json` editing steps must be added to the plan.
- **Ezra's current instructions (pre-v2.4):** Before v2.4 roadmap creation, read Ezra's existing WORKING.md/SOUL.md to understand what triggers the current publish step. Distribution hook must insert after WordPress confirm, not before.
- **DMARC rua mailbox (Phase 27 prerequisite):** Verify where DMARC aggregate reports are being delivered and whether 14+ days of reports have accumulated. Phase 27 requires this data before escalating.

## Sources

### Primary (HIGH confidence)
- [SecureClaw GitHub — adversa-ai/secureclaw](https://github.com/adversa-ai/secureclaw) — install procedure, audit check count (51), behavioral rule count (15), OWASP coverage
- [SecureClaw PR Newswire](https://www.prnewswire.com/news-releases/secureclaw-by-adversa-ai-launches-as-the-first-owasp-aligned-open-source-security-plugin-and-skill-for-openclaw-ai-agents-302688674.html) — feature counts, context cost (~1,230 tokens), layer breakdown confirmed
- [OpenClaw npm package](https://www.npmjs.com/package/openclaw) — v2026.2.17 as latest, update procedure
- [OpenClaw v2026.2.12 security coverage](https://cybersecuritynews.com/openclaw-2026-2-12-released/) — 40+ CVEs patched
- [Resend Broadcast API docs](https://resend.com/docs/api-reference/broadcasts/create-broadcast) — Broadcasts API endpoints confirmed
- [Resend Contacts API docs](https://resend.com/docs/api-reference/contacts/create-contact) — global contacts, CRUD endpoints
- [DMARC Policy Options — MxToolbox](https://mxtoolbox.com/dmarc/details/dmarc-tags/dmarc-policy-options) — p=quarantine behavior, escalation path
- Project MEMORY.md — gateway.remote.url requirement, DM session loss, service entrypoint migration, sandbox bind-mount patterns (all confirmed from project history)

### Secondary (MEDIUM confidence)
- [OpenClaw v2026.2.17 feature summary — NeuralStackly](https://www.neuralstackly.com/blog/openclaw-2026-2-6-update) — specific v2.17 features (WebSearch summaries only, no official changelog)
- [OpenClaw Changelog February 2026](https://www.gradually.ai/en/changelogs/openclaw/) — PR #16724 llm_input/llm_output hook mention
- [Resend New Contacts Experience](https://resend.com/blog/new-contacts-experience) — Audiences renamed to Segments in 2025
- [diagnostics-otel plugin config — deepwiki](https://deepwiki.com/openclaw/openclaw/10-extensions-and-plugins) — OTEL fallback fields and config structure
- [LLM Observability Best Practices 2025 — Maxim](https://www.getmaxim.ai/articles/llm-observability-best-practices-for-2025/) — async processing, PII handling guidance
- [AI Runtime Security False Positives — Acuvity](https://acuvity.ai/ai-runtime-security/) — intent-based vs. pattern-matching tradeoffs (SecureClaw cron blocking risk)

### Tertiary (LOW confidence — needs validation during implementation)
- [OpenClaw hooks discussion — GitHub #7724](https://github.com/openclaw/openclaw/issues/7724) — hook payload structure (community discussion, not official docs)
- [OpenClaw usage logging — GitHub #14377](https://github.com/openclaw/openclaw/issues/14377) — per-agent token logging (feature in progress, not released)
- [configPatch plugin manifest — OpenClaw Issue #6792](https://github.com/openclaw/openclaw/issues/6792) — auto-merge config on install (proposed, not confirmed released)

---
*Research completed: 2026-02-17*
*Ready for roadmap: yes*
