---
phase: 49-install-top-5-clawhhub-skills-on-ec2
plan: 01
subsystem: infra
tags: [clawhub, skills, uv, summarize, blogwatcher, ec2, openclaw]

# Dependency graph
requires:
  - phase: 48-pipeline-fix
    provides: "Stable EC2 platform with OpenClaw v2026.2.17"
provides:
  - "5 ClawhHub skills installed under ~/.openclaw/skills/"
  - "uv v0.10.8 binary at ~/.local/bin/uv"
  - "summarize v0.11.1 CLI at ~/.npm-global/bin/summarize"
  - "blogwatcher v0.0.2 binary at ~/.local/bin/blogwatcher"
affects: [49-02-PLAN, gateway-restart, sandbox-binds]

# Tech tracking
tech-stack:
  added: [uv, "@steipete/summarize", blogwatcher, clawhub]
  patterns: ["npx clawhub@latest install <slug> --workdir ~/.openclaw for skill management"]

key-files:
  created:
    - "~/.openclaw/skills/nano-banana-pro/SKILL.md"
    - "~/.openclaw/skills/summarize/SKILL.md"
    - "~/.openclaw/skills/blogwatcher/SKILL.md"
    - "~/.openclaw/skills/real-estate-lead-machine/SKILL.md"
    - "~/.local/bin/uv"
    - "~/.npm-global/bin/summarize"
    - "~/.local/bin/blogwatcher"
  modified:
    - "~/.openclaw/skills/youtube-full/SKILL.md"

key-decisions:
  - "Installed blogwatcher pre-built binary instead of deferring (Linux amd64 release found at v0.0.2)"
  - "All 5 skills passed clawhub inspect security review before install"

patterns-established:
  - "clawhub inspect before install: Always run npx clawhub@latest inspect <slug> to review metadata before committing to install"

requirements-completed: [SKILL-INSTALL, CLI-DEPS]

# Metrics
duration: 4min
completed: 2026-03-04
---

# Phase 49 Plan 01: Install CLI Dependencies and ClawhHub Skills Summary

**Installed uv, summarize, blogwatcher CLIs and 5 ClawhHub skills (youtube-full, nano-banana-pro, summarize, blogwatcher, real-estate-lead-machine) on EC2**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-04T21:47:08Z
- **Completed:** 2026-03-04T21:50:44Z
- **Tasks:** 2
- **Files modified:** 8 (on EC2)

## Accomplishments
- Installed 3 CLI dependencies: uv v0.10.8, summarize v0.11.1, blogwatcher v0.0.2
- Updated youtube-full to v1.4.1 (was older version from Feb 16)
- Installed 4 new skills: nano-banana-pro v1.0.1, summarize v1.0.0, blogwatcher v1.0.0, real-estate-lead-machine v1.0.0
- Found and used pre-built blogwatcher Linux binary (no Go installation needed)
- All 5 skills passed security inspection before install

## Task Commits

Each task was committed atomically:

1. **Task 1: Install CLI dependencies (uv, summarize, blogwatcher)** - `fd22d0b` (chore)
2. **Task 2: Install/update all 5 ClawhHub skills** - `5f5ffd8` (feat)

## Files Created/Modified
- `~/.local/bin/uv` - Python package runner (for nano-banana-pro)
- `~/.npm-global/bin/summarize` - URL/file/YouTube summarization CLI
- `~/.local/bin/blogwatcher` - RSS/blog feed monitor binary
- `~/.openclaw/skills/youtube-full/SKILL.md` - Updated to v1.4.1
- `~/.openclaw/skills/nano-banana-pro/SKILL.md` - New image generation skill
- `~/.openclaw/skills/summarize/SKILL.md` - New summarization skill
- `~/.openclaw/skills/blogwatcher/SKILL.md` - New blog monitoring skill
- `~/.openclaw/skills/real-estate-lead-machine/SKILL.md` - New lead scraping skill

## Decisions Made
- Installed blogwatcher pre-built binary from GitHub releases (v0.0.2) instead of deferring -- the plan said to check for pre-built first, and one was available
- Ran `npx clawhub@latest inspect` on all 5 skills before install as security check per ClawHavoc risk

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Installed blogwatcher binary (plan expected it might be deferred)**
- **Found during:** Task 1
- **Issue:** Plan anticipated blogwatcher might not have a pre-built binary and prepared a deferral path
- **Fix:** Found pre-built Linux amd64 binary at v0.0.2 on GitHub releases, downloaded and installed
- **Files modified:** ~/.local/bin/blogwatcher
- **Verification:** `blogwatcher --version` returns 0.0.2
- **Committed in:** fd22d0b (Task 1 commit)

---

**Total deviations:** 1 (positive deviation -- binary was available)
**Impact on plan:** No scope creep. Better outcome than expected.

## Issues Encountered
None -- all installations completed on first attempt.

## User Setup Required
None for this plan. Plan 49-02 will handle environment variables (APIFY_API_TOKEN) and gateway restart.

## Next Phase Readiness
- All 5 skills installed, ready for gateway configuration in 49-02
- APIFY_API_TOKEN still needed for real-estate-lead-machine (deferred to 49-02)
- TRANSCRIPT_API_KEY status for youtube-full needs checking (deferred to 49-02)
- Sandbox bind-mounts may be needed for uv/summarize/blogwatcher (deferred to 49-02)
- Gateway restart needed to load new skills (49-02)

## Self-Check: PASSED

- SUMMARY.md: FOUND
- Commit fd22d0b (Task 1): FOUND
- Commit 5f5ffd8 (Task 2): FOUND
- EC2 verification: All 5 SKILL.md files present, uv/summarize/blogwatcher binaries working

---
*Phase: 49-install-top-5-clawhhub-skills-on-ec2*
*Completed: 2026-03-04*
