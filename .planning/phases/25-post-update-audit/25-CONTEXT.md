# Phase 25: Post-Update Audit - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify all existing automations (20 crons, 11 skills, 7 agents) survived the OpenClaw v2026.2.17 update, and confirm SecureClaw's prompt injection protections are functioning. Fix anything broken inline. No new capabilities — audit and repair only.

</domain>

<decisions>
## Implementation Decisions

### Verification method
- Config check only for crons — verify all 20 appear in `openclaw cron list` with correct schedules. Do NOT wait for crons to fire or force-trigger them.
- Skills: verify all 11 appear in `openclaw skill list` and are loadable
- Agents: verify all 7 respond (heartbeat or DM test)
- Fix broken items inline during audit — don't just flag for later

### Expected manifests
- Build hardcoded expected lists for ALL three categories: crons (20), skills (11), agents (7)
- Diff expected vs actual to catch missing, renamed, or extra items
- Manifest includes name + schedule (crons), name (skills), name (agents)

### Injection test approach
- Craft test payloads and feed through browser fetch AND inbound email (the two real external content vectors)
- Confirm blocking via BOTH: (1) verify Bob's response didn't follow injected instruction, AND (2) check SecureClaw logs for block events
- Test should cover the SecureClaw behavioral rules around external content sandboxing

### Claude's Discretion
- Number and variety of injection test payloads (recommend 5-8 diverse patterns covering direct injection, indirect injection, encoding tricks)
- Exact skill invocation method (non-destructive — avoid triggering real email sends, etc.)
- Agent verification method (heartbeat vs DM vs status check — whatever's simplest)
- How to structure the audit report/output

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Key context:
- STATE.md notes "11 skills" (roadmap says 10 — verify the actual count)
- SecureClaw exceptions doc at `~/clawd/agents/main/SECURECLAW_EXCEPTIONS.md` lists pre-approved patterns (cron/email/browser) — don't flag those as injection failures
- SecureClaw is at `/tmp/secureclaw/` which is NOT persistent — note this but don't fix it here (Phase 28 scope)

</specifics>

<deferred>
## Deferred Ideas

- Move SecureClaw from `/tmp/secureclaw/` to permanent location — Phase 28 (Platform Cleanup)
- Force-trigger/smoke-test individual crons — out of scope, config check sufficient

</deferred>

---

*Phase: 25-post-update-audit*
*Context gathered: 2026-02-18*
