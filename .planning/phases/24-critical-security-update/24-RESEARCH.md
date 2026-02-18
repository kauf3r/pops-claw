# Phase 24: Critical Security Update - Research

**Researched:** 2026-02-17
**Domain:** OpenClaw version update + SecureClaw security plugin installation & configuration
**Confidence:** MEDIUM-HIGH

## Summary

Phase 24 requires updating OpenClaw from v2026.2.6-3 to v2026.2.17 on EC2 and installing the SecureClaw security plugin by Adversa AI. The update patches CVE-2026-25253 (1-click RCE via auth token exfiltration, CVSS 8.8) and brings ~11 minor versions of improvements. SecureClaw is a three-layer security solution: 51 automated audit checks, 5 hardening modules, and 15 behavioral rules loaded into the agent's context (~1,230 tokens). It was released on February 16, 2026 by Adversa AI and is the first OWASP ASI Top 10-aligned security plugin for OpenClaw.

The update procedure is well-established from two prior successful updates (v2026.1.24-3 to v2026.2.3-1, then v2026.2.3-1 to v2026.2.6-3). Key risks include: the v2026.2.14 device-token auth regression (relevant since gateway binds to tailnet, not localhost), potential service entrypoint changes, and gog keyring token corruption. SecureClaw installation is via `openclaw plugins install` from a local clone or npm, plus a separate skill deployment step for the 15 behavioral rules.

**Primary recommendation:** Execute as a three-stage operation: (1) pre-update baseline capture + backup, (2) OpenClaw binary update + doctor + regression check for tailnet gateway binding, (3) SecureClaw plugin install + audit + behavioral rule deployment with pre-mapped workflow exceptions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Start strict + whitelist: enable all 15 rules at max strictness, carve exceptions for Bob's known workflows
- Pre-approve known exceptions: audit Bob's workflows (browser, email, file writes, external APIs, crons) against the 15 rules BEFORE enabling, so nothing breaks on day one
- Gate cron jobs too: cron-triggered actions go through SecureClaw gates, no exemptions
- External content sandboxing: full sandbox for web-fetched content; known-source APIs (Gmail, Resend, Oura, Govee, Wyze, WordPress, gog) treated as semi-trusted since already behind Tailscale + SG + Docker
- No scheduling constraints: execute whenever ready, missing a cron run or two is fine
- Target under 30 minutes total downtime
- No downtime announcement needed (single user, running the update ourselves)
- Verify delivery immediately after restart: DM Bob to re-establish session, trigger a test cron to confirm delivery works
- SecureClaw 51-check audit: zero critical findings required, warnings OK and logged
- `openclaw doctor`: no NEW critical findings from the update; pre-existing warnings (deprecated auth profile, legacy session key) are Phase 28's problem
- Fix critical findings in Phase 24: if SecureClaw audit reveals a critical that requires config changes, fix it now rather than deferring to Phase 25
- Capture security baseline BEFORE update: run ClawdStrike + doctor pre-update for before/after comparison
- Copy binary + config before update: backup current openclaw binary and openclaw.json to a backup dir for instant swap-back
- Backup gog keyring tokens before update: known corruption risk during major version migration; if corrupt, remove and re-auth with `--manual`
- Escape hatch: if SecureClaw causes unresolvable issues, disable the plugin but keep the patched binary; update and SecureClaw are separable
- Smoke test only in Phase 24: verify gateway is up, Bob responds to Slack, one cron fires; full 20-cron verification is Phase 25's scope

### Claude's Discretion
- Specific SecureClaw rule-to-workflow mapping (which rules need which exceptions)
- Backup directory location and naming
- Order of operations during the update procedure
- Which cron to use for smoke test

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SEC-01 | OpenClaw updated from v2026.2.6-3 to v2026.2.17 (CVE-2026-25253 patched) | Update procedure documented in findings.md, npm install + doctor + restart pattern validated twice. v2026.2.14 device-token auth regression is the main risk for tailnet-bound gateway. |
| SEC-02 | SecureClaw plugin installed and 51-check audit passes with no critical findings | SecureClaw installs via `openclaw plugins install` from local clone or npm. 51 checks across 8 categories. Plugin also includes `openclaw plugins doctor` for troubleshooting. Existing ClawdStrike baseline (16/25 OK, 3 warn) provides comparison point. |
| SEC-03 | SecureClaw runtime behavioral rules active (15 rules governing external content, credentials, destructive commands) | Rules deployed via SKILL.md into agent workspace (~1,230 tokens). 15 rules cover: prompt injection defense, destructive command gating, credential protection, read-then-exfiltrate detection, supply chain scanning, privacy safeguards, and inter-agent communication. Bob's known workflows (browser, email, file writes, external APIs, crons) need pre-mapped exceptions. |
</phase_requirements>

## Standard Stack

### Core

| Component | Version/Source | Purpose | Why Standard |
|-----------|---------------|---------|--------------|
| OpenClaw | v2026.2.17 (npm: `openclaw@latest`) | AI agent gateway | Target version, patches CVE-2026-25253 |
| SecureClaw plugin | GitHub: `adversa-ai/secureclaw` | Security audit + hardening + behavioral rules | First OWASP ASI Top 10-aligned security plugin for OpenClaw |
| ClawdStrike | Already installed at `~/.openclaw/skills/clawdstrike/` | Pre-existing security audit skill | Baseline comparison tool |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `openclaw doctor --fix` | Config migration, entrypoint fix, state repair | After every version update |
| `openclaw security audit --deep` | Built-in security scan | Pre- and post-update comparison |
| `openclaw plugins doctor` | Plugin troubleshooting | If SecureClaw fails to load |
| `openclaw plugins list` | Verify plugin loaded | After SecureClaw install |

### Installation Commands

```bash
# OpenClaw update
npm install -g openclaw@latest

# SecureClaw plugin install (from local clone)
git clone https://github.com/adversa-ai/secureclaw.git /tmp/secureclaw
cd /tmp/secureclaw/secureclaw
npm install
npm run build
openclaw plugins install -l .

# Alternative: if published to npm
openclaw plugins install @adversa-ai/secureclaw

# SecureClaw skill deployment (behavioral rules)
npx openclaw secureclaw skill install
```

## Architecture Patterns

### SecureClaw Three-Layer Architecture

```
SecureClaw
├── Layer 1: Audit (51 checks, 8 categories)
│   ├── Gateway exposure
│   ├── File permissions
│   ├── Authentication
│   ├── Credentials (plaintext outside .env)
│   ├── Sandbox configuration
│   ├── Network exposure
│   ├── Supply chain
│   └── Discovery/mDNS
│
├── Layer 2: Hardening (5 modules)
│   ├── Gateway (bind, auth)
│   ├── Credentials (file perms, env isolation)
│   ├── Config (permission lockdown)
│   ├── Docker (sandbox settings)
│   └── Network (firewall, listening ports)
│
└── Layer 3: Behavioral Rules (15 rules, ~1,230 tokens)
    ├── External content handling (treat as hostile)
    ├── Destructive command approval
    ├── Credential protection
    ├── Read-then-exfiltrate detection
    ├── Supply chain scanning
    ├── Privacy safeguards
    └── Inter-agent communication security
```

### Update Procedure Pattern (Proven)

```bash
# 1. Pre-update baseline
openclaw doctor                                    # capture current warnings
openclaw security audit --deep                     # capture current findings
cd ~/.openclaw/skills/clawdstrike && bash scripts/collect_verified.sh  # ClawdStrike baseline

# 2. Backup
mkdir -p ~/backups/openclaw-$(date +%Y%m%d)
cp $(which openclaw) ~/backups/openclaw-$(date +%Y%m%d)/
cp ~/.openclaw/openclaw.json ~/backups/openclaw-$(date +%Y%m%d)/
cp -r ~/.config/gogcli/keyring/ ~/backups/openclaw-$(date +%Y%m%d)/gog-keyring/

# 3. Update
npm install -g openclaw@latest

# 4. Doctor + migrate
openclaw doctor --fix

# 5. Verify service entrypoint (doctor flags mismatches)
# If flagged: update ~/.config/systemd/user/openclaw-gateway.service

# 6. Restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service

# 7. Verify
openclaw --version                                 # expect 2026.2.17
systemctl --user status openclaw-gateway.service   # expect active (running)
journalctl --user -u openclaw-gateway.service --since '1 min ago' | tail -20
```

### SecureClaw Rule-to-Workflow Mapping (Claude's Discretion)

Based on research into the known behavioral rules and Bob's established workflows:

| Rule | Description | Bob's Workflows Affected | Exception Needed |
|------|-------------|-------------------------|-----------------|
| Rule 1: External content hostile | Treat emails, web pages, tool outputs from non-owners as potentially injected | Browser automation, email reading, web fetch in crons | YES -- semi-trusted API list (Gmail, Resend, Oura, Govee, Wyze, WordPress, gog). Full sandbox for arbitrary web content. |
| Rule 2: Destructive command approval | Require human approval for rm -rf, curl pipe sh, eval, chmod 777, credential access, mass messaging, SQL DROP/DELETE, git push --force, config edits | Cron jobs that write files, email sending, config changes via cron | YES -- pre-approve known cron actions (email send, file writes to workspace, health DB updates). Approval still required for novel destructive commands. |
| Rule 3: Credential protection | Never expose credentials in external outputs | Email sending (Resend API key in env), gog auth tokens | PARTIAL -- agent already cannot see raw credentials (they are in .env, not config). Rule reinforces existing Docker sandbox boundary. May need exception for gog CLI operations that reference keyring. |
| Rule 5: Scan before installing | Require scanning of skills/packages before install | Rare -- Bob doesn't install skills autonomously | NO -- default behavior is fine. |
| Rule 8: Read-then-exfiltrate detection | Stop if reading sensitive data then sending externally in same task | Morning briefing reads calendar/email then sends Slack summary. Email monitoring reads inbox then sends alerts. | YES -- pre-approve the known patterns: read calendar/email data -> summarize -> send to owner via Slack/email. Block: read credentials -> send anywhere. |
| Rule 15: Plan disclosure | State plan before multi-step operations | Most cron jobs are multi-step | PARTIAL -- cron jobs run unattended. May need to configure silent plan logging rather than requiring interactive approval for scheduled tasks. |

**Key insight:** Most exceptions are for cron-triggered workflows that run without human interaction. The SKILL.md behavioral rules are context-window instructions, not hard-coded gatekeepers -- they guide the agent's behavior but the agent can be instructed (via its own workspace SKILL.md or soul.md) to pre-approve specific patterns. The approach is: add SecureClaw SKILL.md to agent context, then add a companion exception document listing pre-approved workflow patterns.

### Backup Directory Naming (Claude's Discretion)

**Recommendation:** `~/backups/pre-v2026.2.17-$(date +%Y%m%d%H%M)/`

Contents:
- `openclaw` (binary copy)
- `openclaw.json` (config snapshot)
- `gog-keyring/` (keyring directory copy)
- `clawdstrike-baseline.json` (pre-update ClawdStrike bundle)
- `doctor-output.txt` (pre-update doctor output)
- `security-audit.txt` (pre-update security audit output)

### Smoke Test Cron (Claude's Discretion)

**Recommendation:** Use `daily-heartbeat` (fires at 09:00 UTC daily). If update happens outside that window, trigger it manually with `openclaw cron trigger daily-heartbeat` (or equivalent CLI command) to verify the cron system processes and delivers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Security audit | Custom audit scripts | SecureClaw 51-check audit | Covers 8 categories, OWASP-aligned, maintained by Adversa AI |
| Runtime behavioral rules | Custom SKILL.md rules | SecureClaw's 15 rules | Expert-crafted, maps to OWASP ASI Top 10 and MITRE ATLAS |
| Config hardening | Manual config edits | SecureClaw hardening modules | Automated, consistent, repeatable |
| Supply chain scanning | grep for patterns | SecureClaw's 4 JSON pattern databases | Injection patterns, dangerous commands, privacy rules, supply chain indicators |
| Version update migration | Manual config editing | `openclaw doctor --fix` | Handles config schema changes, entrypoint updates, state migrations |

**Key insight:** SecureClaw and `openclaw doctor` handle the heavy lifting. The only manual work is: mapping exceptions to Bob's known workflows, verifying gateway binding survives the update, and confirming gog tokens aren't corrupted.

## Common Pitfalls

### Pitfall 1: Device Token Auth Regression (v2026.2.14)
**What goes wrong:** Commit d8a2c80cd in v2026.2.14 flipped client-side token priority, breaking non-localhost device-authenticated connections with "unauthorized: device token mismatch" error.
**Why it happens:** The regression removed the `canFallbackToShared` self-healing mechanism. Clients with both a stored device token and a config/env token send the wrong one.
**How to avoid:** After update, immediately verify gateway is accessible on the tailnet IP (100.72.143.9:18789). If auth fails, manually align the gateway token in config with the active device token and restart. Check if v2026.2.17 has fixed this regression (it may have, given it's 3 versions later).
**Warning signs:** `journalctl` shows "unauthorized: device token mismatch" or gateway WebSocket connections fail.
**Confidence:** MEDIUM -- regression was reported in v2026.2.14, unknown if fixed by v2026.2.17.

### Pitfall 2: Service Entrypoint Mismatch After Update
**What goes wrong:** Major version updates can change the gateway entrypoint (e.g., `entry.js` to `index.js` happened in the v2026.2.3-1 update).
**Why it happens:** OpenClaw refactors its dist/ structure between versions. The systemd service file hardcodes the entrypoint path.
**How to avoid:** Run `openclaw doctor` -- it flags mismatches. Then update `~/.config/systemd/user/openclaw-gateway.service` if needed and `systemctl --user daemon-reload`.
**Warning signs:** Gateway fails to start after `systemctl restart`. Doctor output shows entrypoint warning.
**Confidence:** HIGH -- documented from prior experience.

### Pitfall 3: Gog Keyring Token Corruption
**What goes wrong:** OAuth tokens stored in gog's file-based keyring can corrupt during major version migrations.
**Why it happens:** Unknown root cause, but experienced during v2026.1.24 to v2026.2.3 migration (aes.KeyUnwrap integrity check failed).
**How to avoid:** Backup `~/.config/gogcli/keyring/` before update. After update, test with `gog calendar events --max 1` or similar. If corrupt, remove tokens and re-auth with `gog auth add --manual --services gmail,calendar`.
**Warning signs:** `aes.KeyUnwrap integrity check failed` in logs.
**Confidence:** HIGH -- experienced firsthand.

### Pitfall 4: Gateway Restart Clears DM Sessions
**What goes wrong:** After gateway restart, cron `sessions_send` to DM channels fails because session state is lost.
**Why it happens:** DM sessions are established when a user sends a message; they don't persist across restarts.
**How to avoid:** After restart, immediately DM Bob via Slack to re-establish the session. Then trigger a test cron to confirm delivery works.
**Warning signs:** Cron runs complete but messages don't arrive in Slack DM.
**Confidence:** HIGH -- documented known behavior.

### Pitfall 5: SecureClaw Hardening Overwriting Existing Config
**What goes wrong:** SecureClaw's 5 hardening modules may try to "fix" settings that are intentionally configured (e.g., binding gateway to tailnet instead of loopback).
**Why it happens:** SecureClaw defaults assume loopback binding is the safe default. Tailnet binding is valid but non-default.
**How to avoid:** Run the SecureClaw audit first (read-only). Review findings before applying any hardening modules. Skip gateway-bind hardening since tailnet + token auth is the intentional configuration. Apply hardening selectively.
**Warning signs:** Gateway stops being accessible on tailnet IP after hardening.
**Confidence:** MEDIUM -- inferred from SecureClaw's documented hardening behavior (binds gateway to localhost).

### Pitfall 6: Behavioral Rules Blocking Cron-Triggered Workflows
**What goes wrong:** SecureClaw Rule 2 (destructive command approval) and Rule 8 (read-then-exfiltrate) could block cron jobs that run unattended.
**Why it happens:** Rules assume a human is available to approve actions. Cron jobs run without human interaction.
**How to avoid:** Pre-approve known cron workflow patterns in a companion exception document. Load exceptions into agent context alongside SecureClaw SKILL.md. Test with a manual cron trigger before relying on scheduled execution.
**Warning signs:** Cron jobs fire but produce no output, or agent logs show "awaiting approval" with no one to approve.
**Confidence:** MEDIUM -- behavioral rules are context-window guidance, not hard gatekeepers, so the agent may or may not strictly enforce them depending on prompt design.

## Code Examples

### Plugin Install from Local Clone (Verified Pattern)
```bash
# Source: https://github.com/openclaw/openclaw/blob/main/docs/cli/plugins.md
# Source: https://github.com/adversa-ai/secureclaw

git clone https://github.com/adversa-ai/secureclaw.git /tmp/secureclaw
cd /tmp/secureclaw/secureclaw
npm install
npm run build
openclaw plugins install -l .
# -l flag creates a symlink (useful for dev/updates)
# Alternatively, without -l, copies files to ~/.openclaw/extensions/secureclaw/
```

### Verify Plugin Loaded
```bash
# Source: https://github.com/openclaw/openclaw/blob/main/docs/tools/plugin.md
openclaw plugins list
# Should show secureclaw as loaded/enabled

openclaw plugins info secureclaw
# Shows plugin details, version, status

# If plugin fails to load:
openclaw plugins doctor
```

### SecureClaw Skill Deployment
```bash
# Deploy behavioral rules to agent workspace
npx openclaw secureclaw skill install
# Installs SKILL.md + scripts to agent's skill directory

# Verify skill detected
openclaw skills list
# Should show secureclaw skill as ready
```

### Run SecureClaw Audit
```bash
# 51-check audit (read-only)
openclaw secureclaw audit

# With JSON output for comparison
openclaw secureclaw audit --json > /tmp/secureclaw-audit-$(date +%Y%m%d).json
```

### Tailnet Gateway Binding Verification
```bash
# Source: Context7 /openclaw/openclaw — gateway security docs
# Verify gateway still binds to tailnet after update
ss -tlnp | grep 18789
# Should show 100.72.143.9:18789

# Verify CLI can connect via gateway.remote.url
openclaw gateway health
# Should show OK with timing info
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ClawdStrike only (community audit skill) | SecureClaw plugin + ClawdStrike | Feb 16, 2026 | SecureClaw adds runtime behavioral rules + plugin-level audit; ClawdStrike remains useful for comparison |
| Manual security hardening | SecureClaw 5 hardening modules | Feb 16, 2026 | Automated, repeatable hardening |
| No prompt injection defense | SecureClaw Rule 1 (external content hostile) + Rule 8 (read-then-exfiltrate) | Feb 16, 2026 | Agent-level defense against injection attacks |
| `gateway.bind: loopback` default | `tailnet` bind with token auth (this deployment) | v2026.2.x | Non-default but valid; must verify SecureClaw doesn't flag/override |
| `dm.policy` + `dm.allowFrom` | `dmPolicy` + `allowFrom` config aliases (v2026.2.14+) | Feb 2026 | Doctor can migrate; Phase 28 scope |

**Deprecated/outdated:**
- ClawdStrike alone is no longer sufficient for runtime protection (only does static audit)
- Manual security checklists replaced by automated SecureClaw modules
- `canFallbackToShared` device token fallback removed in v2026.2.14

## Open Questions

1. **v2026.2.14 device-token regression -- fixed in v2026.2.17?**
   - What we know: Bug reported as issue #17270 on GitHub. Affects non-localhost gateway binds.
   - What's unclear: Whether v2026.2.15/2.16/2.17 includes the fix.
   - Recommendation: After update, immediately test gateway connectivity on tailnet IP. Have rollback binary ready. Check release notes for v2026.2.15+ during execution. If regression persists, workaround is to manually align OPENCLAW_GATEWAY_TOKEN with the active device token.

2. **SecureClaw npm package name**
   - What we know: Plugin installs via `openclaw plugins install`. GitHub repo is `adversa-ai/secureclaw`. Local install via clone + build + `openclaw plugins install -l .` is documented.
   - What's unclear: Whether `@adversa-ai/secureclaw` is published to npm, or if local clone is the only install method.
   - Recommendation: Try npm install first (`openclaw plugins install @adversa-ai/secureclaw`). Fall back to local clone if not on npm. SecureClaw was released Feb 16, 2026 (1 day ago) so npm publishing may lag.

3. **SecureClaw behavioral rules -- complete list of all 15**
   - What we know: Rules 1 (external content hostile), 2 (destructive command approval), 3 (credential protection), 5 (scan before install), 8 (read-then-exfiltrate detection), 15 (plan disclosure) are documented in search results.
   - What's unclear: Rules 4, 6, 7, 9-14 are not documented in available sources.
   - Recommendation: After installing SecureClaw skill, read the full SKILL.md to map all 15 rules to Bob's workflows before enabling. This is a do-on-execution research task, not a blocker.

4. **SecureClaw hardening vs. tailnet gateway binding**
   - What we know: SecureClaw hardening includes "binding gateways to localhost." This deployment intentionally uses tailnet binding.
   - What's unclear: Whether hardening is modular (can skip gateway-bind module) or all-or-nothing.
   - Recommendation: Run audit first (read-only). If hardening is modular, skip gateway module. If all-or-nothing, skip hardening entirely and rely on audit + behavioral rules. The deployment is already well-hardened per ClawdStrike 16/25 baseline.

5. **SecureClaw + existing ClawdStrike -- overlap and conflict**
   - What we know: Both are security tools for OpenClaw. ClawdStrike is a skill; SecureClaw is a plugin + skill.
   - What's unclear: Whether they conflict (both modifying agent context, both scanning for similar issues).
   - Recommendation: Keep both installed. SecureClaw is the primary runtime security layer; ClawdStrike provides an independent baseline check. If they conflict at runtime, disable ClawdStrike skill and keep it as a manual host-level audit tool only.

## Sources

### Primary (HIGH confidence)
- Context7 `/openclaw/openclaw` -- plugin install commands, gateway security config, doctor command
- [OpenClaw Plugin CLI Docs](https://github.com/openclaw/openclaw/blob/main/docs/cli/plugins.md) -- `openclaw plugins install` syntax
- [OpenClaw Security Docs](https://docs.openclaw.ai/gateway/security) -- gateway bind modes, token auth
- [OpenClaw Doctor Docs](https://docs.openclaw.ai/cli/doctor) -- migration, repair, audit
- [GitHub Advisory GHSA-g8p2-7wf7-98mq](https://github.com/openclaw/openclaw/security/advisories/GHSA-g8p2-7wf7-98mq) -- CVE-2026-25253 details
- [NVD CVE-2026-25253](https://nvd.nist.gov/vuln/detail/CVE-2026-25253) -- CVSS 8.8, CWE-669

### Secondary (MEDIUM confidence)
- [SecureClaw GitHub](https://github.com/adversa-ai/secureclaw) -- installation, rule descriptions, audit categories
- [Adversa AI Blog: SecureClaw Launch](https://adversa.ai/blog/adversa-ai-launches-secureclaw-open-source-security-solution-for-openclaw-agents/) -- 3-layer architecture, rule descriptions
- [Adversa AI Blog: 5 Security Frameworks](https://adversa.ai/blog/secureclaw-open-source-ai-agent-security-for-openclaw-aligned-with-owasp-mitre-frameworks/) -- OWASP/MITRE mapping
- [SecureClaw PR Newswire](https://www.prnewswire.com/news-releases/secureclaw-by-adversa-ai-launches-as-the-first-owasp-aligned-open-source-security-plugin-and-skill-for-openclaw-ai-agents-302688674.html) -- feature overview
- [GitHub Issue #17270](https://github.com/openclaw/openclaw/issues/17270) -- v2026.2.14 device-token auth regression
- [OpenClaw v2026.2.14 Release](https://github.com/openclaw/openclaw/releases/tag/v2026.2.14) -- dmPolicy aliases, security fixes

### Tertiary (LOW confidence)
- [AISecHub tweet](https://x.com/AISecHub/status/2022292973430448462) -- mentions "12 behavioral rules" (may be older count before v1.0 bumped to 15)
- Prior update experience documented in `progress.md` and `findings.md` -- HIGH confidence for this deployment but not independently verifiable

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- update procedure proven twice, SecureClaw install path documented in official OpenClaw plugin docs
- Architecture: MEDIUM-HIGH -- SecureClaw's 3-layer model well-documented, but specific rule details (9 of 15 rules) not found in public sources
- Pitfalls: MEDIUM-HIGH -- 4 of 6 pitfalls based on direct prior experience; 2 inferred from documented issues
- Rule-to-workflow mapping: MEDIUM -- based on known rules (6 of 15) mapped to known workflows; remaining 9 rules need on-execution review

**Research date:** 2026-02-17
**Valid until:** 2026-03-01 (SecureClaw is brand new, may iterate quickly; OpenClaw releases weekly)
