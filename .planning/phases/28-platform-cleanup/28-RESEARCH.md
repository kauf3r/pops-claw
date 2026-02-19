# Phase 28: Platform Cleanup - Research

**Researched:** 2026-02-19
**Domain:** OpenClaw doctor warnings, gog OAuth scope management, OpenClaw config migration, gateway documentation
**Confidence:** HIGH

## Summary

Phase 28 is pure maintenance -- four independent cleanup items with no new features. The research reveals an important scope finding: `gog auth add --services gmail` requests `gmail.modify` + `gmail.settings.basic` + `gmail.settings.sharing` by default, which means the "2 excess scopes" (`settings.basic`, `settings.sharing`) were baked into gog's default gmail service scopes. The user's target scopes (`gmail.readonly` + `gmail.send` + `gmail.modify` + `calendar.readonly`) cannot be achieved purely with `--services` flags -- `gmail.modify` already subsumes both `gmail.readonly` and `gmail.send` per Google's scope hierarchy. The practical minimum via gog is `--services gmail,calendar --readonly` (for calendar only) but gog does not support per-service readonly. The realistic cleanup is: re-auth with `--services gmail,calendar` (which gives `gmail.modify` + `calendar` full) and accept that `gmail.settings.basic`/`settings.sharing` will still be included unless gog adds granular scope control. Alternatively, keep existing scopes and document the rationale.

The doctor warnings ("deprecated auth profile" and "legacy session key") are both auto-fixable via `openclaw doctor --fix`. The `dmPolicy`/`allowFrom` migration was already completed in Phase 24-01 -- this requirement is already satisfied and just needs verification. The email-catchup cron delivery target error is an infrastructure bug where the agent in an isolated session tries to send a message but has no target configured.

**Primary recommendation:** Run `openclaw doctor --fix` for the two warnings first (quick wins), verify dmPolicy migration is already done, then tackle OAuth scope trimming as the final and most disruptive step. Document `gateway.remote.url` in PROJECT.md last.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- One-shot re-auth with exactly required scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`, `calendar.readonly`
- Remove and re-add OAuth credential via `gog auth remove` + `gog auth add --manual` with trimmed scope list
- Do both personal and AirSpace accounts in same session
- If a cron job fails post-trim, that tells us we missed a required scope -- add it back surgically
- Fix all doctor warnings in one pass, but test `openclaw doctor` after each individual fix to confirm it clears
- Known warnings: deprecated auth profile, legacy session key -- independent, order doesn't matter
- If a fix breaks gateway startup, revert immediately via service journal
- Clean switch to `dmPolicy`/`allowFrom` aliases -- no old keys left behind, no comments
- One edit to `openclaw.json`, restart gateway, verify with `openclaw doctor`
- If new aliases aren't recognized (version mismatch), revert the JSON change
- Verification order: (1) Doctor warnings first, (2) Config migration second, (3) OAuth scope trim third, (4) Document gateway.remote.url last
- Each cleanup item is independently revertible
- Rollback strategy: revert JSON for config, re-auth with old scopes for OAuth

### Claude's Discretion
- Exact order of individual doctor warning fixes
- How to structure the PROJECT.md gateway URL documentation section
- Whether to batch-test cron jobs or test individually after OAuth re-auth

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLN-01 | Gmail OAuth scope reduction (remove 2 excess scopes, re-auth gog) | Excess scopes identified as `gmail.settings.basic` and `gmail.settings.sharing`. gog CLI `--services gmail` bundles these automatically. Scope reduction requires `gog auth remove` + `gog auth add --manual`. Critical finding: `gmail.modify` already includes read+send+modify, so separate `gmail.readonly` and `gmail.send` scopes are redundant. See "OAuth Scope Analysis" section. |
| CLN-02 | Doctor warnings resolved -- deprecated auth profile migrated to setup-token | `openclaw doctor --fix` handles this migration. The deprecated `anthropic:claude-cli` profile needs migration to `anthropic:manual` (setup-token). Command: `openclaw models auth setup-token`. |
| CLN-03 | Doctor warnings resolved -- legacy session key canonicalization | `openclaw doctor --fix` auto-canonicalizes legacy session keys to the new `agent:<agentId>:<channel>:group:<id>` format. No manual intervention needed. |
| CLN-04 | `dmPolicy`/`allowFrom` config aliases adopted | Already completed in Phase 24-01. Doctor auto-migrated `channels.slack.dm.policy`/`dm.allowFrom` to `dmPolicy`/`allowFrom` format during v2026.2.17 update. Needs verification only, not implementation. |
| CLN-05 | `gateway.remote.url` config documented and verified post-update | Config already set: `"url": "ws://100.72.143.9:18789"` in openclaw.json. Verified working in Phase 24 verification. Needs documentation in PROJECT.md and reachability test from VPS. |
</phase_requirements>

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `openclaw doctor` | v2026.2.17 | Config migration, warning resolution, health checks | Built-in diagnostic and repair tool |
| `gog` CLI | v0.9.0+ | OAuth credential management for Gmail/Calendar | Already installed on EC2, used for all gog operations |
| `openclaw config` | v2026.2.17 | Config key inspection and modification | Built-in config management |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `gog auth list` | Verify OAuth scopes after re-auth | Post-re-auth verification |
| `gog auth remove` | Remove existing OAuth credential before re-auth | Before `gog auth add` with new scopes |
| `gog auth add --manual` | Interactive OAuth re-auth over SSH | Scope reduction requires fresh OAuth flow |
| `openclaw gateway health` | Verify gateway after config changes | After every config change + restart |
| `journalctl --user` | Check gateway logs for errors | After restart, on any failure |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `gog auth add --services gmail,calendar` | Manual scope specification via GCP Console | gog doesn't support per-scope granularity; GCP Console would, but breaks the gog workflow |
| `openclaw doctor --fix` | Manual config editing | Doctor handles edge cases and state migrations that manual editing misses |

## Architecture Patterns

### Pattern 1: Doctor Fix-Then-Verify Loop
**What:** Run `openclaw doctor --fix`, then `openclaw doctor` (without --fix) to confirm zero warnings.
**When to use:** After each individual fix to confirm it clears.
**Example:**
```bash
# Source: https://docs.openclaw.ai/gateway/doctor
# Fix deprecated auth profile
openclaw models auth setup-token
# Then verify
openclaw doctor
# Should show no warnings for auth profile

# Fix legacy session key
openclaw doctor --fix
# Then verify
openclaw doctor
# Should show zero warnings total
```

### Pattern 2: OAuth Re-Auth with gog --manual
**What:** Remove existing token, re-add with trimmed scopes via interactive OAuth flow.
**When to use:** Scope reduction or token refresh.
**Example:**
```bash
# Source: https://github.com/steipete/gogcli/blob/main/README.md
# Must export keyring password for SSH sessions
export GOG_KEYRING_PASSWORD=$(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env | cut -d= -f2)

# Remove existing auth
gog auth remove theandykaufman@gmail.com

# Re-add with specific services
gog auth add theandykaufman@gmail.com --manual --services gmail,calendar --client pops-claw

# Verify scopes
gog auth list
```

### Pattern 3: Cron Smoke Test After OAuth Change
**What:** After re-auth, verify that cron jobs using gog still function.
**When to use:** After any OAuth scope change.
**Example:**
```bash
# Test email operations
gog gmail search --account=theandykaufman@gmail.com "newer_than:1d" --max 3
gog gmail search --account=Kaufman@AirSpaceIntegration.com "newer_than:1d" --max 3

# Test calendar operations
gog calendar events --account=theandykaufman@gmail.com --all --today --max 5
gog calendar events --account=Kaufman@AirSpaceIntegration.com --all --today --max 5
```

### Anti-Patterns to Avoid
- **Editing openclaw.json manually for doctor-fixable issues:** Doctor handles state migrations, not just config keys. Manual editing can miss related state files.
- **Re-authing without backing up the keyring first:** Known corruption risk. Always backup `~/.config/gogcli/keyring/` before any auth changes.
- **Assuming `gmail.readonly` + `gmail.send` + `gmail.modify` are all separate requirements:** `gmail.modify` is a superset that includes read and send. Requesting all three is redundant (though harmless).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config migration | Manual JSON editing for dmPolicy/allowFrom | `openclaw doctor --fix` | Doctor already migrated this in Phase 24-01 |
| Auth profile migration | Manual token file editing | `openclaw models auth setup-token` | Handles both sides of the auth connection |
| Session key canonicalization | Grep/sed on session state files | `openclaw doctor --fix` | Doctor knows the canonical format and migrates all session state |
| Scope enumeration | Manual Google API docs lookup | `gog auth list --json` | Shows actual scopes granted to current token |

**Key insight:** Every cleanup item in this phase has a built-in tool or command. Zero custom scripting needed.

## Common Pitfalls

### Pitfall 1: gog --services gmail Bundles Settings Scopes
**What goes wrong:** Re-authing with `--services gmail` includes `gmail.settings.basic` and `gmail.settings.sharing` automatically -- the exact scopes we want to remove.
**Why it happens:** gog maps `--services gmail` to a fixed set of Google OAuth scopes that includes settings access. There's no `--services gmail --no-settings` flag.
**How to avoid:** Accept that `--services gmail` will always include settings scopes at the gog level. The scope reduction target needs to be revised: remove `gmail.settings.basic` and `gmail.settings.sharing` is only possible if gog adds granular scope control, OR if we use a different OAuth mechanism. Since gog is the only tool used for Gmail/Calendar operations, and the settings scopes are unused but harmless, the pragmatic answer is to re-auth with `--services gmail,calendar` (which removes the `calendar` full-write scope in favor of the default) and document that settings scopes are included by gog.
**Warning signs:** `gog auth list` shows settings scopes even after "clean" re-auth.
**Confidence:** MEDIUM -- based on Context7 gog docs showing scope mapping. Need to verify on EC2 what `gog auth list` actually shows for scopes.

### Pitfall 2: gmail.modify Already Includes Send
**What goes wrong:** Success criterion says "minimum: gmail.readonly + gmail.send + gmail.modify + calendar.readonly" but `gmail.modify` already subsumes `gmail.readonly` and `gmail.send` per Google's API scope hierarchy.
**Why it happens:** Google's scope hierarchy: `https://mail.google.com/` > `gmail.modify` > `gmail.readonly`/`gmail.send`/`gmail.compose`. The scopes are not additive -- they're inclusive.
**How to avoid:** Understand the actual scope hierarchy. With `gmail.modify`, you already have read + send + modify (labels, archive, etc.) but NOT permanent delete (that requires `https://mail.google.com/`). The real minimum is: `gmail.modify` + `calendar.readonly`.
**Warning signs:** `gog auth list` shows fewer scopes than expected after re-auth -- this is correct, not a bug.
**Confidence:** HIGH -- verified via [Google Gmail API scopes documentation](https://developers.google.com/workspace/gmail/api/auth/scopes).

### Pitfall 3: Calendar Write Scope May Be Needed
**What goes wrong:** Re-authing with `calendar.readonly` breaks calendar event creation if Bob creates calendar events.
**Why it happens:** The project has `gog calendar events create` documented as a capability (findings.md). If any cron or skill creates events, `calendar.readonly` won't suffice.
**How to avoid:** Audit whether Bob actually creates calendar events in any cron/skill/workflow. If not, `calendar.readonly` is fine. If yes, keep full `calendar` scope.
**Warning signs:** `gog calendar events create` fails with 403 after re-auth.
**Confidence:** HIGH -- Google's calendar scope model is well-documented. The question is whether this capability is used in practice.

### Pitfall 4: GOG_KEYRING_PASSWORD Required for SSH gog Commands
**What goes wrong:** Running `gog auth list` or `gog auth remove` over SSH without exporting GOG_KEYRING_PASSWORD fails silently or with a keyring error.
**Why it happens:** The gateway service loads it via `EnvironmentFile`, but SSH sessions don't source `.env` automatically.
**How to avoid:** Always run `export GOG_KEYRING_PASSWORD=$(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env | cut -d= -f2)` before any gog commands over SSH.
**Warning signs:** "keyring not found" or empty output from gog auth list.
**Confidence:** HIGH -- experienced in Phase 24-01 (documented in 24-01-SUMMARY.md).

### Pitfall 5: Doctor --fix May Re-trigger dmPolicy Migration
**What goes wrong:** Running `openclaw doctor --fix` for the auth profile warning might also attempt to re-migrate config keys that were already migrated in Phase 24-01.
**Why it happens:** Doctor scans all config keys on each run.
**How to avoid:** This should be safe -- doctor only migrates keys that still have old format. Since Phase 24-01 already migrated dmPolicy/allowFrom, doctor should report those as already current. Verify by running `openclaw doctor` (without --fix) first to see what it would change.
**Warning signs:** Doctor output mentions dmPolicy/allowFrom changes when they should already be migrated.
**Confidence:** HIGH -- doctor is idempotent for config migrations.

### Pitfall 6: Email-Catchup Cron Target Error
**What goes wrong:** The email-catchup cron fires but the agent can't send messages because isolated sessions have no inherent message target.
**Why it happens:** The cron uses `sessionTarget: "isolated"` with `delivery.mode: "silent"`. When the agent tries to send a message to #popsclaw (per its instructions), it fails because the isolated session doesn't know where to deliver.
**How to avoid:** Either (a) add a `delivery.target` to the cron config pointing to the Slack channel/DM, or (b) change the cron instructions so it uses the tools API with an explicit channel target, or (c) use the `sessions_send` pattern with a specified channel.
**Warning signs:** Gateway log shows `[tools] message failed: Action send requires a target.`
**Confidence:** MEDIUM -- the root cause is clear from logs, but the exact fix depends on how OpenClaw's cron delivery routing works. Need to check how other crons with isolated sessions successfully post to channels (e.g., airspace-email-monitor).

## Code Examples

### Verify Current Doctor Warnings
```bash
# Source: https://docs.openclaw.ai/gateway/doctor
# SSH into EC2 and run doctor in diagnostic mode (no fixes)
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  '/home/ubuntu/.npm-global/bin/openclaw doctor 2>&1'
```

### Fix Deprecated Auth Profile
```bash
# Source: https://docs.openclaw.ai/gateway/doctor
# The deprecated anthropic:claude-cli profile needs setup-token migration
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  '/home/ubuntu/.npm-global/bin/openclaw models auth setup-token'
# This is interactive -- requires pasting a token. Use ssh -t for TTY.
```

### Fix Legacy Session Keys
```bash
# Source: https://docs.openclaw.ai/gateway/doctor
# Doctor auto-canonicalizes session keys to agent:<agentId>:<channel>:group:<id> format
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  '/home/ubuntu/.npm-global/bin/openclaw doctor --fix'
```

### OAuth Re-Auth Sequence
```bash
# Source: https://github.com/steipete/gogcli/blob/main/README.md
# Full re-auth sequence for scope reduction
ssh -t -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9

# 1. Export keyring password
export GOG_KEYRING_PASSWORD=$(grep GOG_KEYRING_PASSWORD ~/.openclaw/.env | cut -d= -f2)

# 2. Backup current keyring
cp -r ~/.config/gogcli/keyring/ ~/backups/gog-keyring-pre-phase28/

# 3. Check current scopes
gog auth list

# 4. Remove existing auth (personal)
gog auth remove theandykaufman@gmail.com

# 5. Re-add with trimmed services
gog auth add theandykaufman@gmail.com --manual --services gmail,calendar --client pops-claw

# 6. Verify
gog auth list
gog gmail search --account=theandykaufman@gmail.com "newer_than:1d" --max 3
gog calendar events --account=theandykaufman@gmail.com --all --today --max 5

# 7. Repeat for AirSpace account
gog auth remove Kaufman@AirSpaceIntegration.com
gog auth add Kaufman@AirSpaceIntegration.com --manual --services gmail,calendar --client pops-claw
gog auth list
gog gmail search --account=Kaufman@AirSpaceIntegration.com "newer_than:1d" --max 3
```

### Verify gateway.remote.url from VPS
```bash
# Test gateway reachability from VPS over Tailscale
ssh ubuntu@100.105.251.99 \
  'curl -s -o /dev/null -w "%{http_code}" http://100.72.143.9:18789/health'
# Expect: 200 or connection success
```

## OAuth Scope Analysis

### Current Scopes (theandykaufman@gmail.com, 7 total)
1. `email` (OpenID)
2. `https://www.googleapis.com/auth/calendar` (full read+write)
3. `https://www.googleapis.com/auth/gmail.modify` (read+write+delete+labels)
4. `https://www.googleapis.com/auth/gmail.settings.basic` -- EXCESS
5. `https://www.googleapis.com/auth/gmail.settings.sharing` -- EXCESS
6. `https://www.googleapis.com/auth/userinfo.email` (OpenID)
7. `openid`

### Scope Hierarchy (Google Gmail API)
```
https://mail.google.com/          (full access, including permanent delete)
  └── gmail.modify                 (read + send + modify labels/archive, no permanent delete)
       ├── gmail.readonly          (read only -- SUBSUMED by modify)
       ├── gmail.send              (send only -- SUBSUMED by modify)
       └── gmail.compose           (compose only -- SUBSUMED by modify)
```

### What gog --services gmail Requests
Per Context7 gog docs, `--services gmail` requests:
- `https://mail.google.com/` (the FULL gmail scope, broader than gmail.modify)

**Critical finding from gog spec.md:** The scopes section lists Gmail as `https://mail.google.com/` -- this is the broadest possible Gmail scope. The current token has `gmail.modify` (narrower), which means the original auth may have used custom scopes or an older gog version that mapped differently.

### Practical Scope Reduction Strategy

**Option A: Re-auth with gog --services gmail,calendar** (Recommended)
- gog requests `https://mail.google.com/` + `https://www.googleapis.com/auth/calendar`
- This is broader than current `gmail.modify` but removes `settings.basic` and `settings.sharing`
- Calendar stays full-write (supports event creation)
- Net: removes 2 excess scopes, slightly broadens Gmail scope

**Option B: Keep current scopes, document rationale**
- Current scopes work for all operations
- `settings.basic` and `settings.sharing` are unused but not a security risk (behind Tailscale + GCP test user restriction)
- Net: zero disruption, document as accepted technical debt

**Option C: Re-auth attempting to force narrow scopes** (Not recommended)
- gog doesn't support per-scope granularity for Gmail
- Would require patching gog source or using a different OAuth tool
- Over-engineering for 2 unused settings scopes

**Recommendation:** Option A with documentation. The re-auth process is already understood (done twice before), the risk is low with keyring backup, and it satisfies CLN-01 by removing the two excess scopes. The fact that `https://mail.google.com/` replaces `gmail.modify` should be documented -- it's technically broader but gog needs it for full operation.

**Alternatively:** If the user's locked decision says "exactly `gmail.readonly` + `gmail.send` + `gmail.modify` + `calendar.readonly`" and gog can't provide that granularity, discuss with user before proceeding. The locked scopes may need revision based on this research finding.

### AirSpace Account (Kaufman@AirSpaceIntegration.com)
- Authed with `--services gmail,calendar` via `gog auth add --manual --services=gmail,calendar --client=pops-claw`
- Operations used: `gog gmail search`, `gog calendar events` (read-only)
- No calendar write operations documented for this account
- Same re-auth procedure applies: `gog auth remove` + `gog auth add --manual --services gmail,calendar`
- Note: Google Workspace admin may need to re-approve the OAuth client if scopes change

## Email-Catchup Cron Target Error Analysis

### The Problem
Gateway log: `[tools] message failed: Action send requires a target.`
Cron config: `sessionTarget: "isolated"`, `delivery.mode: "silent"`

### Root Cause
Isolated sessions don't have an inherent message delivery target. When the agent's instructions say "notify Andy in #popsclaw," the agent uses the `send` tool, which needs a target channel. In a DM session, the target is implicit (the DM partner). In an isolated session, there's no implicit target.

### How Other Crons Handle This
The airspace-email-monitor cron also uses `sessionTarget: "isolated"` + `delivery.mode: "silent"` and apparently works. The difference may be:
1. airspace-email-monitor might use a different message sending pattern
2. airspace-email-monitor might not attempt to send messages (it may silently complete)
3. The error only manifests when the agent actually tries to send (email-catchup found something to report)

### Fix Options
1. **Add delivery target to cron config:** Add `"delivery": { "mode": "silent", "target": { "channel": "slack", "id": "CPOPSCLAW_CHANNEL_ID" } }` -- this gives the session a target
2. **Change session instructions:** Instruct the agent to use the explicit `message send --channel slack --target CHANNEL_ID` tool call syntax instead of relying on implicit routing
3. **Change sessionTarget to "main":** Use Bob's main session (has implicit DM target) instead of isolated. Downside: pollutes main session context

**Recommendation:** Fix option depends on OpenClaw's cron delivery mechanics. Investigate on EC2: (a) check airspace-email-monitor's exact config for comparison, (b) test adding a delivery target to email-catchup cron config. This is a quick SSH investigation during execution.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `dm.policy` + `dm.allowFrom` | `dmPolicy` + `allowFrom` | v2026.2.14 | Doctor auto-migrates; already done Phase 24-01 |
| `anthropic:claude-cli` auth | `anthropic:manual` (setup-token) | v2026.2.x | Doctor warns; fix via `openclaw models auth setup-token` |
| Legacy session key format | Canonical `agent:<agentId>:<channel>:group:<id>` | v2026.2.x | Doctor auto-canonicalizes with `--fix` |
| `gateway.bind: loopback` | `gateway.bind: tailnet` (this deployment) | v2026.2.x | Requires `gateway.remote.url` for CLI commands |

**Deprecated/outdated:**
- `anthropic:claude-cli` auth profile -- replaced by setup-token mechanism
- Legacy session key format (e.g., `group:<id>`) -- replaced by canonical format
- `dm.policy`/`dm.allowFrom` config keys -- aliased to `dmPolicy`/`allowFrom`

## Open Questions

1. **What exact scopes does gog --services gmail request in practice?**
   - What we know: Context7 spec.md says `https://mail.google.com/` for Gmail. Current token has `gmail.modify` (narrower).
   - What's unclear: Whether gog version matters, whether `--services gmail` has changed its scope mapping over versions.
   - Recommendation: Run `gog auth add --dry-run` (if available) or check gog source. Alternatively, just do the re-auth and check `gog auth list` afterward. The keyring backup makes this safe to try.

2. **Does Bob actually create calendar events?**
   - What we know: `gog calendar events create` is listed as a capability in findings.md. AirSpace account uses calendar read-only.
   - What's unclear: Whether any active cron/skill actually invokes calendar event creation.
   - Recommendation: Search jobs.json for "calendar events create" or "calendar.*create" before deciding on `calendar` vs `calendar.readonly` scope. If no active usage, downgrade to readonly.

3. **Email-catchup cron: what's the correct delivery target config?**
   - What we know: Isolated sessions + silent delivery + agent trying to send = "requires a target" error. airspace-email-monitor has same session/delivery pattern.
   - What's unclear: Exact cron delivery target schema. Whether airspace-email-monitor avoids the error by never sending, or by having a different config.
   - Recommendation: SSH into EC2, compare both cron configs in jobs.json, test fix before committing.

4. **Will gog re-auth require re-approval in Google Workspace admin for AirSpace account?**
   - What we know: AirSpace is a Google Workspace account. Initial auth required admin approval.
   - What's unclear: Whether re-authing with same client ID and same/similar scopes triggers re-approval.
   - Recommendation: Do personal account first. If it works smoothly, proceed with AirSpace. Have user's Workspace admin access ready as fallback.

## Sources

### Primary (HIGH confidence)
- Context7 `/openclaw/openclaw` -- doctor command, config migration, legacy key mappings
- Context7 `/steipete/gogcli` -- auth add/remove, services flag, scope mapping, manual flow
- [OpenClaw Doctor Docs](https://docs.openclaw.ai/gateway/doctor) -- migration, repair, audit
- [Google Gmail API Scopes](https://developers.google.com/workspace/gmail/api/auth/scopes) -- scope hierarchy, gmail.modify includes send
- Phase 24-01 SUMMARY and VERIFICATION -- dmPolicy migration already completed, confirmed
- Phase 25-02 SUMMARY -- email-catchup cron target error documented

### Secondary (MEDIUM confidence)
- [OpenClaw Remote Access Docs](https://docs.openclaw.ai/gateway/remote) -- gateway.remote.url configuration
- [gog CLI README](https://github.com/steipete/gogcli/blob/main/README.md) -- service scopes, auth flow
- [gog CLI spec.md](https://github.com/steipete/gogcli/blob/main/docs/spec.md) -- scope union model, service-to-scope mapping
- [GitHub Issue #18535](https://github.com/openclaw/openclaw/issues/18535) -- doctor refers to deprecated auth command

### Tertiary (LOW confidence)
- Web search results on gog gmail scope mapping -- limited direct evidence on exact scopes per service flag
- Email-catchup cron delivery target fix -- inferred from architecture, not verified

## Metadata

**Confidence breakdown:**
- Doctor warnings (CLN-02, CLN-03): HIGH -- well-documented commands, proven migration paths
- Config migration (CLN-04): HIGH -- already completed in Phase 24-01, just needs verification
- OAuth scope reduction (CLN-01): MEDIUM -- gog's scope mapping is not fully transparent; scope hierarchy is clear but exact gog behavior needs on-EC2 verification
- Gateway docs (CLN-05): HIGH -- config already set and verified, just needs PROJECT.md documentation
- Email-catchup fix: MEDIUM -- root cause clear, fix needs on-EC2 investigation

**Research date:** 2026-02-19
**Valid until:** 2026-03-05 (stable domain, no fast-moving dependencies)
