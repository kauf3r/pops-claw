# Phase 43: Bug Fixes — Plan

**Created:** 2026-03-01
**Goal:** Content pipeline produces WordPress drafts for approved articles, AeroVironment tracking resolved

## Plan Overview

Two bugs. BUG-01 has a clear fix path (5 sub-issues on EC2). BUG-02 turned out to be in a different project (Supabase/airspace-operations-dashboard) — will document findings and create a bead for the correct repo.

---

## Plan 1: Fix Ezra publish-check (BUG-01)

### Wave 1: Remove ghost file + fix mount shadow
1. Delete 0-byte ghost: `rm ~/clawd/agents/main/content.db`
2. Also delete `~/clawd/agents/main/content.db.old` if exists (stale from memory notes)
3. Verify bind-mount works: restart gateway, check content.db visible in main sandbox

### Wave 2: Fix publish-check cron targeting
4. Check if publish-check cron runs as `agent:ezra` or `agent:main` — the cron config says target `ezra` but session keys show `agent:main`
5. If Ezra doesn't get its own container, the cron runs in main's sandbox. Two options:
   a. Add Ezra workspace files to main's workspace (simpler)
   b. Create Ezra-specific agent config with proper workspace mount (correct but more complex)
6. Decision: Use approach (a) — copy PUBLISH_SESSION.md to main workspace or symlink

### Wave 3: Fix WP credentials + Slack delivery
7. Verify WP env vars (WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD) in agents.defaults.sandbox.docker.env
8. Fix Slack delivery target on publish-check cron — needs channel:ID format
9. Test publish-check cron manually

### Wave 4: Recover approved article
10. Query content.db for approved articles missing wp_post_id (article #20 identified)
11. Trigger publish-check or manually create WP draft for article #20
12. Verify WP draft created and wp_post_id populated

### Wave 5: Regression prevention
13. Add content.db size check to nightly health script (alert if 0 bytes)
14. Add Slack alert to publish-check when it can't read content.db

## Plan 2: Resolve AeroVironment fly_status (BUG-02)

### Research Finding
fly_status lives in **Supabase `storage` table** for the airspace-operations-dashboard project (ops.airspaceintegration.com). It is NOT in content.db. No `compliance_flights` table exists anywhere. The only current mechanism is a manual UI toggle in the storage modal.

The agent trust layer (asi-officernd) has a `set_fly_status` tool that calls a non-existent API endpoint (`PUT /api/storage/{companyId}/aircraft/{aircraftId}/status`).

### Resolution
1. This is not a pops-claw bug — it belongs to the asi-officernd project
2. Create a bead tracking the actual fix (build missing API endpoint + automation)
3. Update REQUIREMENTS.md to note BUG-02 is re-scoped to a different project
4. Close BUG-02 in this phase as "wrong repo, tracked elsewhere"

## Plan 3: Verification + Close

1. Verify content.db accessible in sandbox after fixes
2. Verify article #20 has wp_post_id
3. Verify publish-check cron delivers to Slack
4. Update ROADMAP.md progress
5. Commit + push

---

## Success Criteria

- [x] BUG-01: Ezra publish-check creates WP drafts for approved articles → Fixed
- [x] BUG-02: AeroVironment tracking → Re-scoped (different project), bead created
- [x] Regression prevention: health check + Slack alerts added
- [x] Morning briefing reflects accurate content pipeline data (implicit from BUG-01 fix)

---

*Phase: 43-bug-fixes*
*Plan created: 2026-03-01*
