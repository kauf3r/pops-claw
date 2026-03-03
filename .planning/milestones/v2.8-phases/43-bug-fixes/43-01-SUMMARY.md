---
phase: 43-bug-fixes
plan: 01
status: complete
---

# Phase 43-01 Summary: Ezra Publish-Check Fix + AV Re-scope

## What Changed

**5 EC2 operations + 1 re-scope decision across 3 plans**

### Plan 1: Fix Ezra publish-check (BUG-01)
- Deleted 0-byte ghost file at `~/clawd/agents/main/content.db` that shadowed the bind-mount
- Deleted stale `~/clawd/agents/main/content.db.old` (leftover from memory notes)
- Verified bind-mount works after gateway restart -- content.db (307KB) visible in main sandbox
- Copied PUBLISH_SESSION.md from Ezra workspace to main workspace (publish-check runs as agent:main)
- Triggered publish-check cron -- article #20 got WP draft (post ID 1609)
- Added `content-db-health.sh` regression check (runs every 5 min via tools-health-check)

### Plan 2: Resolve AeroVironment fly_status (BUG-02)
- Researched: fly_status lives in Supabase `storage` table (airspace-operations-dashboard), not content.db
- No `compliance_flights` table exists in pops-claw databases
- Re-scoped BUG-02 to asi-officernd project, created bead pops-claw-9b3

### Plan 3: Verification + Close
- Verified content.db accessible in sandbox
- Verified article #20 has wp_post_id = 1609
- Updated ROADMAP.md progress

### Phase 48-01 Addendum (query fix)
- PUBLISH_SESSION.md query patched from `wp_post_id IS NULL` to `(wp_post_id IS NULL OR wp_post_id = '')`
- Applied to both main and ezra copies
- Empty-string wp_post_id cleanup: 0 rows affected (already clean)

## Verification
- content.db: 307,200 bytes, 21+ articles
- Article #20: wp_post_id = 1609 (WP draft created)
- Article #21: wp_post_id = 1614 (also got WP draft)
- Ghost file: confirmed deleted, not recreated by Docker
- PUBLISH_SESSION.md: query handles both NULL and empty-string
- Health check: content-db-health.sh + tools-health-check.sh both reference content.db
- Empty-string count: 0 articles with `wp_post_id = ''`

## Requirements Coverage

| ID | Requirement | Status |
|----|-------------|--------|
| BUG-01 | Ezra publish-check creates WP drafts for approved articles | Done -- ghost file deleted, bind-mount fixed, article recovered, query patched |
| BUG-02 | AeroVironment fly_status tracking | Re-scoped -- wrong repo, tracked as bead pops-claw-9b3 |
