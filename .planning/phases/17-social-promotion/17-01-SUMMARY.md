---
phase: 17-social-promotion
plan: 01
subsystem: infra
tags: [social-media, content-generation, skill, linkedin, twitter, instagram, ezra]

# Dependency graph
requires:
  - phase: 16-wordpress-publishing
    plan: 02
    provides: "wordpress-publisher skill, PUBLISH_SESSION.md, publish-check cron"
  - phase: 12-content-agents
    provides: "content.db with social_posts table, exec-approvals allowlist, content agent cron pattern"
provides:
  - "social-promoter SKILL.md generating copy for LinkedIn, X/Twitter, and Instagram"
  - "Updated PUBLISH_SESSION.md with social promotion step after publication confirmation"
affects: [content-pipeline-e2e]

# Tech tracking
tech-stack:
  added: [social-copy-generation]
  patterns: [copy-only-social-promotion, human-manual-posting]

key-files:
  created:
    - "~/.openclaw/skills/social-promoter/SKILL.md (EC2) — 3-platform social copy generation skill"
  modified:
    - "~/clawd/agents/ezra/PUBLISH_SESSION.md (EC2) — added Step 5 social promotion, renumbered summary to Step 6"

key-decisions:
  - "Copy-only approach: no social API integrations, human posts manually from content.db"
  - "Instagram includes image_prompt field for DALL-E/Midjourney image generation guidance"
  - "Social promotion triggers automatically in existing publish-check cron (no new cron job)"

patterns-established:
  - "Copy-only social promotion: generate platform-specific content, human posts manually"
  - "Skill chaining in session reference docs: PUBLISH_SESSION invokes social-promoter skill"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 17 Plan 01: Social Promotion Summary

**Social-promoter skill deployed for 3-platform copy generation (LinkedIn, X/Twitter, Instagram) with automatic triggering after Ezra confirms article publication**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T23:46:46Z
- **Completed:** 2026-02-09T23:49:27Z
- **Tasks:** 2
- **Files modified:** 2 (all remote EC2)

## Accomplishments
- Deployed social-promoter SKILL.md with 10 sections covering full social copy generation workflow for 3 platforms
- LinkedIn: 1300-char professional post with hook, insights, CTA, and hashtags
- X/Twitter: Single tweet or 2-4 tweet thread with article link
- Instagram: 2200-char caption with hook, line breaks, "link in bio" CTA, 15-25 hashtags, plus image_prompt field
- All social posts stored in content.db social_posts table with pipeline_activity logging
- Updated PUBLISH_SESSION.md from 5 steps to 6 steps — social promotion triggers automatically after publication confirmation
- No new cron job needed — piggybacks on existing daily publish-check cron (2 PM PT)
- Gateway restarted with new skill and updated session reference

## Task Commits

Both tasks involved remote EC2 changes only (no local files). Tracked in metadata commit.

1. **Task 1: Deploy social-promoter SKILL.md** - Remote-only (EC2 ~/.openclaw/skills/social-promoter/SKILL.md)
2. **Task 2: Update PUBLISH_SESSION.md + restart gateway** - Remote-only (EC2 ~/clawd/agents/ezra/PUBLISH_SESSION.md)

**Plan metadata:** See final commit (docs: complete social-promotion plan)

## Files Created/Modified
- `~/.openclaw/skills/social-promoter/SKILL.md` (EC2) - 3-platform social copy generation skill with content.db storage, Slack notifications, error handling
- `~/clawd/agents/ezra/PUBLISH_SESSION.md` (EC2) - Added Step 5 (social promotion after publication confirmation), renumbered Step 6 (session summary includes social post count)

## Decisions Made
- Copy-only approach: no social media API integrations; human retrieves content from content.db and posts manually
- Instagram gets unique image_prompt field (DALL-E/Midjourney guidance); LinkedIn and Twitter get NULL
- Social promotion integrated into existing PUBLISH_SESSION flow (Step 5) rather than separate cron, avoiding additional job complexity
- Step 2 updated: "If no approved articles found" now continues to Step 4 (check published) instead of ending silently, ensuring social posts still trigger even when no new drafts needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Step 2 early exit preventing social generation**
- **Found during:** Task 2 (PUBLISH_SESSION.md update)
- **Issue:** Original Step 2 said "End session silently" when no approved articles found. This would skip Steps 4-5 entirely, preventing social post generation for articles that were already published since last session.
- **Fix:** Changed Step 2 to "Continue to Step 4 to check for published articles" so the session always checks for publication confirmations and generates social posts.
- **Files modified:** ~/clawd/agents/ezra/PUBLISH_SESSION.md (EC2)
- **Verification:** Step 2 now reads "Continue to Step 4" instead of "End session silently"
- **Committed in:** Part of metadata commit

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix — without it, social posts would never generate on sessions where no new articles needed drafting.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Social promotion uses existing infrastructure (content.db, publish-check cron, Slack channel).

## Verification Results

| Check | Result |
|-------|--------|
| SKILL.md exists at ~/.openclaw/skills/social-promoter/ | PASS |
| SKILL.md has valid YAML frontmatter (name: social-promoter) | PASS |
| SKILL.md covers 3 platforms (linkedin, twitter, instagram) | PASS |
| social_posts schema: article_id, platform, content, image_prompt, status | PASS |
| No API posting (COPY ONLY statement) | PASS |
| PUBLISH_SESSION.md has 6 steps | PASS |
| Step 5 references social-promoter skill | PASS |
| Step 6 includes "social media posts generated" | PASS |
| Gateway service active after restart | PASS (PID 210605) |
| No new cron job (existing publish-check) | PASS |

## Next Phase Readiness
- Social copy generation is integrated into the content pipeline end-to-end
- No additional phases needed for social promotion — the pipeline is complete for copy-only workflow
- Future enhancement: API-based posting to LinkedIn/X/Instagram (would be a new phase with OAuth setup)
- Content pipeline E2E flow: research -> write -> review -> approve -> WP draft -> human publish -> social copy generated

## Self-Check: PASSED

- [x] 17-01-SUMMARY.md exists locally
- [x] SKILL.md exists at ~/.openclaw/skills/social-promoter/SKILL.md (EC2)
- [x] PUBLISH_SESSION.md exists at ~/clawd/agents/ezra/PUBLISH_SESSION.md (EC2) with 6 steps
- [x] Gateway service active (EC2)

---
*Phase: 17-social-promotion*
*Completed: 2026-02-09*
