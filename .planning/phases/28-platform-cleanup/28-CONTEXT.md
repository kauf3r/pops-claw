# Phase 28: Platform Cleanup - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve all deferred maintenance items: clean `openclaw doctor` output, trim OAuth scopes to minimum required, adopt modern config aliases (`dmPolicy`/`allowFrom`), and document `gateway.remote.url` in PROJECT.md. No new features — pure cleanup.

</domain>

<decisions>
## Implementation Decisions

### OAuth scope trimming
- One-shot re-auth with exactly required scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`, `calendar.readonly`
- Remove and re-add OAuth credential via `gog auth remove` + `gog auth add --manual` with trimmed scope list
- Do both personal and AirSpace accounts in same session
- If a cron job fails post-trim, that tells us we missed a required scope — add it back surgically

### Doctor warnings approach
- Fix all warnings in one pass, but test `openclaw doctor` after each individual fix to confirm it clears
- Known warnings: deprecated auth profile, legacy session key — independent, order doesn't matter
- If a fix breaks gateway startup, revert immediately via service journal

### Config migration style
- Clean switch to `dmPolicy`/`allowFrom` aliases — no old keys left behind, no comments
- One edit to `openclaw.json`, restart gateway, verify with `openclaw doctor`
- If new aliases aren't recognized (version mismatch), revert the JSON change

### Verification order
1. Doctor warnings first (clean baseline diagnostics)
2. Config migration second (JSON-only, low risk, quick to verify)
3. OAuth scope trim third (most disruptive — requires re-auth, cron testing)
4. Document `gateway.remote.url` in PROJECT.md last (pure docs, zero risk)

### Claude's Discretion
- Exact order of individual doctor warning fixes
- How to structure the PROJECT.md gateway URL documentation section
- Whether to batch-test cron jobs or test individually after OAuth re-auth

</decisions>

<specifics>
## Specific Ideas

- Each cleanup item is independently revertible
- OAuth is the only item requiring re-auth to roll back
- Rollback strategy: revert JSON for config, re-auth with old scopes for OAuth

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-platform-cleanup*
*Context gathered: 2026-02-19*
