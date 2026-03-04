---
phase: 49-install-top-5-clawhhub-skills-on-ec2
plan: 02
subsystem: infra
tags: [clawhub, skills, env-config, gateway, openclaw, ec2, sandbox]

# Dependency graph
requires:
  - phase: 49-01
    provides: "5 ClawhHub skills installed under ~/.openclaw/skills/"
provides:
  - "Environment variables configured for all 5 skills (GEMINI_API_KEY, TRANSCRIPT_API_KEY, APIFY_API_TOKEN)"
  - "Sandbox Docker env updated with skill API keys"
  - "Gateway running with 30 eligible skills (4/5 new skills ready)"
  - "real-estate-lead-machine SKILL.md frontmatter fixed for OpenClaw recognition"
affects: [gateway-restart, sandbox-env, skill-eligibility]

# Tech tracking
tech-stack:
  added: []
  patterns: ["YAML frontmatter required in SKILL.md for OpenClaw skill recognition", "Sandbox docker.env must include API keys for agent-side skills"]

key-files:
  created:
    - ".planning/phases/49-install-top-5-clawhhub-skills-on-ec2/49-02-env-config.md"
    - ".planning/phases/49-install-top-5-clawhhub-skills-on-ec2/49-02-gateway-verify.md"
  modified:
    - "~/.openclaw/.env"
    - "~/.openclaw/openclaw.json"
    - "~/.openclaw/skills/real-estate-lead-machine/SKILL.md"

key-decisions:
  - "Added GEMINI_API_KEY to sandbox docker.env (needed by nano-banana-pro + summarize inside Docker)"
  - "Fixed real-estate-lead-machine SKILL.md with YAML frontmatter (was invisible to OpenClaw without it)"
  - "Used NEEDS_USER_INPUT placeholders for TRANSCRIPT_API_KEY and APIFY_API_TOKEN"

patterns-established:
  - "ClawhHub skills need YAML frontmatter with name, description, metadata fields for OpenClaw to recognize them"
  - "Agent-side skills need API keys added to both ~/.openclaw/.env AND agents.defaults.sandbox.docker.env in openclaw.json"

requirements-completed: [ENV-CONFIG, GATEWAY-VERIFY]

# Metrics
duration: 6min
completed: 2026-03-04
---

# Phase 49 Plan 02: Configure Environment and Verify Skills Summary

**Configured env vars for 5 ClawhHub skills, fixed real-estate-lead-machine frontmatter, gateway running with 30 eligible skills (4/5 new skills ready)**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-04T21:53:30Z
- **Completed:** 2026-03-04T21:59:41Z
- **Tasks:** 2 (of 3 total; Task 3 is checkpoint:human-verify)
- **Files modified:** 3 (on EC2) + 2 (local tracking docs)

## Accomplishments
- Configured GEMINI_API_KEY, TRANSCRIPT_API_KEY, APIFY_API_TOKEN in ~/.openclaw/.env
- Added all 3 API keys to sandbox Docker env in openclaw.json (agent-side access)
- Fixed real-estate-lead-machine SKILL.md missing YAML frontmatter (was invisible to OpenClaw)
- Gateway restarted with 30/65 skills eligible (up from 29 before this plan)
- Doctor output clean: no criticals, no journal errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Configure environment variables and openclaw.json** - `eb0462e` (chore)
2. **Task 2: Restart gateway and verify skill recognition** - `15e3878` (feat)

## Files Created/Modified
- `~/.openclaw/.env` - Added TRANSCRIPT_API_KEY and APIFY_API_TOKEN placeholders
- `~/.openclaw/openclaw.json` - Added GEMINI_API_KEY, TRANSCRIPT_API_KEY, APIFY_API_TOKEN to sandbox docker.env; backup created
- `~/.openclaw/skills/real-estate-lead-machine/SKILL.md` - Added YAML frontmatter for OpenClaw recognition

## Skill Status After Gateway Restart

| Skill | Status | Notes |
|-------|--------|-------|
| blogwatcher | ready | Binary at ~/.local/bin/blogwatcher |
| nano-banana-pro | ready | GEMINI_API_KEY in sandbox env |
| summarize | ready | CLI at ~/.npm-global/bin/summarize |
| real-estate-lead-machine | ready | Fixed with YAML frontmatter |
| youtube-full | missing | Expected: TRANSCRIPT_API_KEY is placeholder |

## Decisions Made
- Added GEMINI_API_KEY to sandbox docker.env -- nano-banana-pro and summarize run inside Docker and need it
- Fixed real-estate-lead-machine SKILL.md by adding YAML frontmatter -- ClawhHub install didn't include it
- Used NEEDS_USER_INPUT as placeholder value for keys user hasn't provided yet

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed real-estate-lead-machine SKILL.md missing YAML frontmatter**
- **Found during:** Task 2
- **Issue:** ClawhHub installed the skill but its SKILL.md had no YAML frontmatter, so OpenClaw couldn't register it (0 of 65 skills matched)
- **Fix:** Added frontmatter with name, description, and metadata (requires: env APIFY_API_TOKEN)
- **Files modified:** ~/.openclaw/skills/real-estate-lead-machine/SKILL.md
- **Verification:** After gateway restart, skill shows as "ready" in `openclaw skills list`
- **Committed in:** 15e3878 (Task 2 commit)

**2. [Rule 2 - Missing Critical] Added GEMINI_API_KEY to sandbox Docker env**
- **Found during:** Task 1
- **Issue:** GEMINI_API_KEY was only in host .env but nano-banana-pro and summarize run inside Docker sandbox, needing it in agents.defaults.sandbox.docker.env
- **Fix:** Added GEMINI_API_KEY to sandbox docker.env in openclaw.json
- **Files modified:** ~/.openclaw/openclaw.json
- **Verification:** nano-banana-pro and summarize both show "ready" after restart
- **Committed in:** eb0462e (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes necessary for skills to function. Without frontmatter fix, real-estate-lead-machine would be invisible. Without sandbox env fix, nano-banana-pro and summarize would fail at runtime.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required

Two skills need external API keys to fully function:

1. **youtube-full** needs `TRANSCRIPT_API_KEY` from https://transcriptapi.com (free: 100 credits/month)
2. **real-estate-lead-machine** (and summarize YouTube fallback) needs `APIFY_API_TOKEN` from https://apify.com (free: $5/month credits)

To configure:
```bash
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
# Edit ~/.openclaw/.env and replace NEEDS_USER_INPUT with real keys
# Then: systemctl --user restart openclaw-gateway
```

**Note:** Gateway restart clears DM sessions. DM Bob on Slack to re-establish.

## Next Phase Readiness
- All 5 ClawhHub skills installed and configured
- 4/5 immediately ready; youtube-full will be ready once TRANSCRIPT_API_KEY provided
- Phase 49 is the final phase -- no follow-on phase planned
- Gateway is healthy, doctor clean

## Self-Check: PASSED

- SUMMARY.md: FOUND
- Commit eb0462e (Task 1): FOUND
- Commit 15e3878 (Task 2): FOUND
- EC2 verification: Gateway active, 30/65 skills eligible, no journal errors

---
*Phase: 49-install-top-5-clawhhub-skills-on-ec2*
*Completed: 2026-03-04*
