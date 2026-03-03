# Phase 48: Pipeline Fix & Verification Backfill - Research

**Researched:** 2026-03-02
**Domain:** Documentation backfill, SQL query fix, EC2 file cleanup
**Confidence:** HIGH

## Summary

This phase closes audit gaps from the v2.8 milestone audit. The work splits into four distinct categories: (1) fix a SQL query mismatch in PUBLISH_SESSION.md where `wp_post_id IS NULL` misses articles with `wp_post_id = ''` (empty string), (2) delete a 0-byte ghost file at `/home/ubuntu/clawd/agents/main/content.db` that was supposed to be removed in Phase 43, (3) backfill VERIFICATION.md and SUMMARY.md for phases 43, 44, and 45 which completed work but never created verification artifacts, and (4) update REQUIREMENTS.md checkboxes for all completed requirements.

This is primarily a documentation and cleanup phase with one targeted code fix (the SQL query). The PUBLISH_SESSION.md file lives on EC2 at Bob's workspace and controls how the publish-check cron identifies articles needing WordPress drafts. The verification backfill requires reading the existing PLAN.md and CONTEXT.md files for phases 43-45, cross-referencing with live EC2 state, and producing VERIFICATION.md and SUMMARY.md in the established formats (see Phase 46 and 47 examples).

**Primary recommendation:** Execute as four independent plans -- one per gap category. The SQL fix and ghost file deletion are EC2 SSH operations. The verification backfill is local documentation work informed by SSH inspection. The REQUIREMENTS.md update is a local file edit.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUG-01 (fix partial) | Ezra publish-check creates WordPress drafts for approved articles | SQL query fix pattern documented below; PUBLISH_SESSION.md location and query identified; empty-string vs NULL gap confirmed by milestone audit |
| TREND-01 | /yolo page shows build success rate chart over time | Verification backfill only -- implementation confirmed wired by audit integration check; needs VERIFICATION.md artifact |
| TREND-02 | /yolo page shows average self-score chart over time | Verification backfill only -- implementation confirmed wired by audit integration check; needs VERIFICATION.md artifact |
| YOLO-01-05 | YOLO detail page requirements (card click, log, errors, eval, files) | Verification backfill only -- all 5 confirmed wired by audit; Phase 44 PLAN.md documents what was built; needs VERIFICATION.md artifact |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| SSH | n/a | EC2 access for SQL fix + ghost file deletion | All EC2 ops use `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9` |
| sqlite3 | n/a (system) | Query content.db to verify fix | Already on EC2, used by health checks and cron jobs |
| better-sqlite3 | Bundled w/ Next.js 14.2.15 | Mission Control reads yolo.db, observability.db | Existing stack -- verification queries only |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| sed/vim | Edit PUBLISH_SESSION.md on EC2 | For the SQL query fix in Bob's workspace |
| cat/ls | Inspect EC2 filesystem state | Verify ghost file, check content.db, inspect artifacts |
| curl | Hit Mission Control APIs | Verify YOLO/trends endpoints for backfill evidence |

### Alternatives Considered
None -- this phase uses only existing tools and patterns.

**Installation:** None required.

## Architecture Patterns

### Pattern 1: SQL Query Fix for NULL vs Empty String
**What:** PUBLISH_SESSION.md contains a query filtering `WHERE status = 'approved' AND wp_post_id IS NULL`. Article #21 has `wp_post_id = ''` (empty string) instead of NULL, so the cron skips it.
**When to use:** Anytime SQLite text columns may contain empty strings vs NULL.
**Fix:**
```sql
-- Before (misses empty strings):
WHERE status = 'approved' AND wp_post_id IS NULL

-- After (catches both):
WHERE status = 'approved' AND (wp_post_id IS NULL OR wp_post_id = '')
```

**Alternative approach:** Set `wp_post_id = NULL` directly in the database for article #21. This fixes the immediate case but leaves the query vulnerable to future empty-string inserts. The query fix is more robust.

**Recommended: Do both.** Fix the query AND set article #21's wp_post_id to NULL. Belt and suspenders.

### Pattern 2: PUBLISH_SESSION.md Location
**What:** The publish-check cron uses PUBLISH_SESSION.md as session instructions.
**Location:** On EC2 at Bob's workspace. Phase 43 Plan noted Ezra workspace files were copied to main's workspace because publish-check runs as agent:main.
**Expected paths to check:**
- `~/clawd/agents/main/PUBLISH_SESSION.md`
- `~/clawd/agents/ezra/PUBLISH_SESSION.md` (original)

### Pattern 3: Verification Backfill
**What:** Create VERIFICATION.md and SUMMARY.md for phases that completed work but never produced verification artifacts.
**Format:** Follow the established format from Phase 46 and Phase 47.

**VERIFICATION.md structure:**
```markdown
---
phase: {phase-name}
verified: {ISO timestamp}
status: passed
score: X/X must-haves verified
---

# Phase X: Name Verification Report

## Goal Achievement
### Observable Truths (table: #, Truth, Status, Evidence)
### Required Artifacts (table: Artifact, Expected, Status, Details)
### Key Link Verification (table: From, To, Via, Status, Details)
### Requirements Coverage (table: Requirement, Source Plan, Description, Status, Evidence)
### Anti-Patterns Found
### Human Verification Required
### Gaps Summary
```

**SUMMARY.md structure (per plan):**
```markdown
---
phase: {phase-name}
plan: {plan-number}
status: complete
---

# Phase X Plan Y: Title Summary

## What Changed
## Verification
## Requirements Coverage
```

### Pattern 4: Requirements Checkbox Update
**What:** REQUIREMENTS.md has unchecked boxes for completed requirements.
**Current state from audit:**
- TREND-01, TREND-02: `[ ]` -> need `[x]`
- AGENT-01, AGENT-02: `[ ]` -> need `[x]` (noted in audit, but already checked in current file)
- BUG-01: `[ ]` -> stays `[ ]` until query fix confirmed

**Note:** Audit flagged AGENT-01/AGENT-02 as unchecked, but current REQUIREMENTS.md shows them as `[x]`. TREND-01/TREND-02 are confirmed `[x]` in current file too. The REQUIREMENTS.md may have been updated after the audit ran. Need to re-verify current state during execution.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verification reports | Custom format | Copy Phase 46/47 VERIFICATION.md format exactly | Consistency across milestone; audit tooling expects this structure |
| Summary reports | Custom format | Copy Phase 46/47 SUMMARY.md format exactly | Same reason |
| SQL fix validation | Manual spot-check only | Query content.db for ALL articles with empty-string wp_post_id | May be more than just #21 |

**Key insight:** This phase is about closing process gaps, not building new features. Follow existing patterns exactly.

## Common Pitfalls

### Pitfall 1: Fixing Only Article #21 Without Fixing the Query
**What goes wrong:** Setting article #21's wp_post_id to NULL fixes the immediate case but future articles may also get empty strings inserted.
**Why it happens:** The INSERT/UPDATE code path that creates empty strings is upstream in the content pipeline.
**How to avoid:** Fix the query in PUBLISH_SESSION.md to handle both NULL and empty string. Then also clean up article #21's value.
**Warning signs:** After fix, run a count of articles where `wp_post_id = ''` to find all affected rows.

### Pitfall 2: Wrong PUBLISH_SESSION.md File
**What goes wrong:** Editing PUBLISH_SESSION.md in Ezra's workspace instead of main's workspace.
**Why it happens:** Phase 43 revealed publish-check runs as agent:main, not agent:ezra. Ezra's files were copied to main's workspace.
**How to avoid:** Verify which file the publish-check cron actually reads. Check cron config: `openclaw cron list` and look at the session file path.
**Warning signs:** After editing, trigger a test run and verify the correct file is loaded.

### Pitfall 3: Ghost File Recreated by Docker
**What goes wrong:** Deleting `/home/ubuntu/clawd/agents/main/content.db` but Docker recreates it on next container start.
**Why it happens:** Docker creates 0-byte files at mount points. If the bind-mount config still references this path, Docker will recreate the stub.
**How to avoid:** Check openclaw.json bind-mount config BEFORE deleting. If the bind-mount was properly fixed in Phase 43, Docker should no longer create a stub here. If it does, the mount config needs updating.
**Warning signs:** File reappears after gateway restart.

### Pitfall 4: Verification Backfill Without Live Evidence
**What goes wrong:** Writing VERIFICATION.md based only on local PLAN.md files without checking actual EC2 state.
**Why it happens:** Tempting to just document what the plan said it would do.
**How to avoid:** SSH to EC2 and verify: run curl against APIs, check file existence, query databases. The verification must reflect actual current state, not planned state.
**Warning signs:** VERIFICATION.md says "VERIFIED" but no SSH commands were run.

### Pitfall 5: REQUIREMENTS.md Checkbox State Confusion
**What goes wrong:** The audit found checkboxes unchecked, but the file may have been updated since the audit ran.
**Why it happens:** Multiple sessions editing the same file without coordination.
**How to avoid:** Read REQUIREMENTS.md immediately before editing. Diff against what the audit expected. Only change what's actually wrong.

## Code Examples

### Fixing the SQL Query in PUBLISH_SESSION.md
```bash
# SSH to EC2
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9

# Find the PUBLISH_SESSION.md file
find ~/clawd/agents/main/ -name "PUBLISH_SESSION.md" -type f 2>/dev/null
find ~/clawd/agents/ezra/ -name "PUBLISH_SESSION.md" -type f 2>/dev/null

# Check current query pattern
grep -n "wp_post_id" ~/clawd/agents/main/PUBLISH_SESSION.md

# Fix: replace IS NULL with (IS NULL OR = '')
sed -i 's/wp_post_id IS NULL/(wp_post_id IS NULL OR wp_post_id = '\'''\'')/g' ~/clawd/agents/main/PUBLISH_SESSION.md

# Verify fix
grep -n "wp_post_id" ~/clawd/agents/main/PUBLISH_SESSION.md
```

### Cleaning Up Article #21
```bash
# Check article #21 current state
sqlite3 ~/clawd/content.db "SELECT id, title, status, wp_post_id, typeof(wp_post_id) FROM articles WHERE id = 21;"

# Check ALL articles with empty-string wp_post_id
sqlite3 ~/clawd/content.db "SELECT id, title, status, wp_post_id FROM articles WHERE wp_post_id = '';"

# Fix: set empty strings to NULL
sqlite3 ~/clawd/content.db "UPDATE articles SET wp_post_id = NULL WHERE wp_post_id = '';"
```

### Deleting Ghost File
```bash
# Check if ghost file exists
ls -la ~/clawd/agents/main/content.db

# Check bind-mount config (make sure it won't recreate)
cat ~/.openclaw/openclaw.json | python3 -c "import json,sys; c=json.load(sys.stdin); print(json.dumps(c.get('agents',{}).get('defaults',{}).get('sandbox',{}).get('docker',{}).get('binds',[]), indent=2))"

# Delete ghost file
rm ~/clawd/agents/main/content.db

# Verify after gateway restart
sudo systemctl --user restart openclaw-gateway
sleep 5
ls -la ~/clawd/agents/main/content.db  # should not exist
```

### Verification Backfill SSH Evidence Gathering
```bash
# Phase 43 evidence: content.db accessible, article #20 has wp_post_id
sqlite3 ~/clawd/content.db "SELECT id, title, wp_post_id FROM articles WHERE id = 20;"
sqlite3 ~/clawd/content.db "SELECT id, title, status, wp_post_id FROM articles WHERE status = 'approved';"

# Phase 44 evidence: YOLO detail page API works
curl -s http://localhost:3001/api/yolo/builds | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"builds\"])} builds')"
curl -s http://localhost:3001/api/yolo/builds/007-expense-tracker-dashboard | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['build']['name'], 'hasHtml:', d['build']['hasHtml'])"

# Phase 45 evidence: trends API works
curl -s http://localhost:3001/api/yolo/trends | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"trends\"])} trend data points')"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Verification during execution | Verification as separate artifact | v2.8 Phase 46+ | Audit can check requirement satisfaction independently |
| PLAN.md only | PLAN.md + VERIFICATION.md + SUMMARY.md | v2.8 Phase 46+ | Full audit trail per phase |

**Key shift:** Phase 46 established the pattern of creating VERIFICATION.md and SUMMARY.md as explicit artifacts. Phases 43-45 predate this pattern and need backfill.

## Open Questions

1. **Exact PUBLISH_SESSION.md content**
   - What we know: It contains a query with `wp_post_id IS NULL` that needs fixing
   - What's unclear: The exact file contents and whether other queries in the file also need the same fix
   - Recommendation: Cat the full file on EC2 before editing; fix ALL occurrences of the pattern

2. **Article #21 origin of empty string**
   - What we know: wp_post_id is '' (empty string) instead of NULL
   - What's unclear: Which code path inserted the empty string (agent behavior, skill code, or manual entry)
   - Recommendation: Fix the query defensively; root cause analysis of the INSERT path is out of scope for this phase

3. **Whether ghost file is auto-recreated**
   - What we know: Phase 43 roadmap says it was deleted, but audit says it still exists
   - What's unclear: Whether it was recreated by Docker on gateway restart, or never actually deleted
   - Recommendation: Check bind-mount config first, then delete, then restart gateway and verify it stays deleted

4. **REQUIREMENTS.md current state**
   - What we know: Audit found TREND-01/TREND-02 unchecked and AGENT-01/AGENT-02 unchecked
   - What's unclear: Current file shows them all as `[x]` -- may have been updated after audit
   - Recommendation: Read current file during execution, only fix what's actually wrong. BUG-01 stays `[ ]` until SQL fix is confirmed.

## Sources

### Primary (HIGH confidence)
- `.planning/v2.8-MILESTONE-AUDIT.md` -- Full gap analysis identifying all 4 categories of work
- `.planning/REQUIREMENTS.md` -- Current checkbox state and requirement definitions
- `.planning/ROADMAP.md` -- Phase 48 definition and success criteria
- `.planning/phases/43-bug-fixes/PLAN.md` -- What Phase 43 did (mount fix, article recovery)
- `.planning/phases/44-yolo-detail-page/PLAN.md` -- What Phase 44 built (detail page polish)
- `.planning/phases/45-build-trends/PLAN.md` -- What Phase 45 built (trend charts)
- `.planning/phases/46-agent-board-polish/46-VERIFICATION.md` -- Template for VERIFICATION.md format
- `.planning/phases/46-agent-board-polish/46-01-SUMMARY.md` -- Template for SUMMARY.md format
- `.planning/phases/47-build-artifacts/47-VERIFICATION.md` -- Another VERIFICATION.md example

### Secondary (MEDIUM confidence)
- Phase 43 CONTEXT.md -- Original discussion context for bug fix approach

### Tertiary (LOW confidence)
- None -- all findings from project artifacts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all tools are already in use on EC2
- Architecture: HIGH - patterns established in Phase 46/47, SQL fix is straightforward
- Pitfalls: HIGH - all identified from actual project history (audit findings, known Docker behavior)

**Research date:** 2026-03-02
**Valid until:** 2026-03-09 (phase should be executed within days; EC2 state may change)
