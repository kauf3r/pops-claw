# Phase 47: Build Artifacts - Research

**Researched:** 2026-03-02
**Domain:** YOLO build preview (iframe), automated disk cleanup (cron + SQLite)
**Confidence:** HIGH

## Summary

Phase 47 has two requirements: iframe preview of HTML builds (PREV-01) and automated 30-day build cleanup with top-rated retention (PREV-02). The critical finding is that PREV-01 is **already fully implemented** in Phase 44. The detail page at `/yolo/[slug]/page.tsx` already renders an 80vh sandboxed iframe when `hasHtml` is true, with an "Open in new tab" link. The API at `/api/yolo/files/[...path]/route.ts` already serves index.html with correct MIME types and path traversal protection.

PREV-02 (build cleanup) is the real new work. The approach is a host-level bash+Python cleanup script (matching the pattern of `prune-sessions.sh`) run via crontab. The script queries `yolo.db` for builds older than 30 days, checks self_score to protect top-rated builds (score 4-5), then removes build directories from disk and optionally marks/removes DB rows. Currently there are only 8 builds totaling ~208KB, so cleanup is not urgent -- but the mechanism needs to exist for when overnight builds accumulate.

**Primary recommendation:** Verify PREV-01 is complete (1 plan), then implement a `cleanup-yolo-builds.sh` script + crontab entry for PREV-02 (1 plan). Two plans total.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PREV-01 | User can preview index.html build artifacts in an iframe on the detail page | Already implemented in Phase 44 -- iframe with sandbox="allow-scripts", 80vh height, "Open in new tab" link. See Architecture Pattern 1 for verification approach. |
| PREV-02 | Builds older than 30 days are automatically cleaned up (top-rated retained) | Cleanup script pattern from prune-sessions.sh, crontab at 4:30am UTC daily. See Architecture Pattern 2 for implementation. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | (existing) | Query yolo.db for build metadata | Already used by Mission Control |
| Next.js | 14.2.15 | Serves iframe preview via API routes | Already the dashboard framework |
| bash + python3 | stdlib | Cleanup script (matches prune-sessions.sh pattern) | Existing pattern on this EC2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 (Python) | stdlib | Query yolo.db in cleanup script | For the cleanup cron only |
| crontab | system | Schedule daily cleanup | Same mechanism as prune-sessions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Host crontab script | OpenClaw cron job | OpenClaw cron runs inside Docker sandbox which can't delete host files. Must use host crontab. |
| Python cleanup script | Pure bash with sqlite3 CLI | Python is cleaner for date math + sqlite queries. Matches prune-sessions.sh pattern. |
| Delete DB rows | Keep DB rows, only delete files | Keeping rows preserves historical trend data. Recommend keeping rows, deleting only disk files. |

## Architecture Patterns

### Current YOLO Infrastructure
```
~/clawd/agents/main/yolo-dev/
  yolo.db                     # SQLite DB (builds table)
  000-test/                   # Build directories
  005-pomodoro-timer-cli/
  007-expense-tracker-dashboard/
    index.html                # HTML builds have this
    README.md
    ...
  011-code-scorer/
```

**Key paths:**
- Dashboard reads from: `/home/ubuntu/clawd/agents/main/yolo-dev/`
- DB path (in db-paths.ts): `/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db`
- API file serving: `/api/yolo/files/[...path]/route.ts` (YOLO_DIR = above path)
- Sandbox bind-mount: `~/clawd/agents/main/yolo-dev:/workspace/yolo-dev:rw`
- There is also `~/clawd/yolo-dev/` (different dir, host-only builds, not used by dashboard)

### Pattern 1: Iframe Preview (Already Implemented)
**What:** The YOLO detail page already embeds an iframe for HTML builds
**Status:** COMPLETE from Phase 44
**Existing code (page.tsx lines 743-769):**
```tsx
{build.hasHtml && (
  <Card className="border-zinc-700/50">
    <CardContent className="p-0">
      <div className="px-4 py-2 border-b border-border flex items-center justify-between bg-zinc-900/50">
        <h2 className="text-sm font-semibold">Live Preview</h2>
        <a
          href={`/api/yolo/files/${build.slug}/index.html`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Open in new tab
        </a>
      </div>
      <div className="border-2 border-zinc-700/30 rounded-b-lg m-0.5 mt-0">
        <iframe
          src={`/api/yolo/files/${build.slug}/index.html`}
          sandbox="allow-scripts"
          className="w-full bg-white rounded-b-lg"
          style={{ height: "80vh", minHeight: "500px" }}
          title={`${build.name} preview`}
        />
      </div>
    </CardContent>
  </Card>
)}
```

**Verification approach:**
- Confirm builds with `hasHtml=true` render the iframe (test with 007-expense-tracker-dashboard, 009-git-stats-visualizer, 010-markdown-slide-converter)
- Confirm builds without HTML do NOT show iframe
- Confirm "Open in new tab" works
- Screenshot for VERIFICATION.md

### Pattern 2: Build Cleanup Script
**What:** A host-level cleanup script run by crontab
**When to use:** Daily at 4:30am UTC (offset from prune-sessions at 4:00am)
**Approach (matching prune-sessions.sh pattern):**
```bash
#!/bin/bash
# Cleanup YOLO builds older than 30 days (retain top-rated)
YOLO_DIR="/home/ubuntu/clawd/agents/main/yolo-dev"
DB="$YOLO_DIR/yolo.db"
LOG="/home/ubuntu/scripts/cleanup-yolo-builds.log"

if [ ! -f "$DB" ]; then exit 0; fi

python3 << 'PYEOF'
import sqlite3
import shutil
import os
from datetime import datetime, timedelta

YOLO_DIR = "/home/ubuntu/clawd/agents/main/yolo-dev"
DB = os.path.join(YOLO_DIR, "yolo.db")
RETENTION_DAYS = 30
MIN_SCORE_TO_KEEP = 4  # 4 and 5 are "top-rated"

cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Find old builds NOT top-rated
candidates = conn.execute("""
    SELECT id, slug, date, self_score, status
    FROM builds
    WHERE date < ?
      AND (self_score IS NULL OR self_score < ?)
      AND status IN ('success', 'partial', 'failed')
""", (cutoff, MIN_SCORE_TO_KEEP)).fetchall()

deleted = 0
for build in candidates:
    build_dir = os.path.join(YOLO_DIR, build["slug"])
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
        deleted += 1
        print(f"Deleted: {build['slug']} (score={build['self_score']}, date={build['date']})")

conn.close()
print(f"Cleanup complete: {deleted} build(s) deleted, {len(candidates) - deleted} already gone")
PYEOF
```

### Anti-Patterns to Avoid
- **Deleting DB rows:** Don't delete from the builds table. Keep metadata for historical trends. Only delete files from disk.
- **Using OpenClaw cron for cleanup:** OpenClaw cron runs inside Docker sandbox at `/workspace/`. It CAN write to `/workspace/yolo-dev/` (bind-mounted rw), but host scripts are simpler, more reliable, and match existing patterns (prune-sessions.sh).
- **Deleting the yolo.db:** The cleanup script must NEVER touch yolo.db itself. Only remove build directories.
- **Hardcoding build IDs:** Always query the DB dynamically. Never assume specific build numbers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date arithmetic in bash | Shell date math | Python datetime + timedelta | Consistent, handles edge cases |
| SQLite from bash | sqlite3 CLI piping | Python sqlite3 module | Row factory, proper types, error handling |
| Recursive directory deletion | `rm -rf` in bash | Python shutil.rmtree | Safer, returns errors |

**Key insight:** The prune-sessions.sh pattern (bash wrapper + embedded Python) is battle-tested on this EC2 and handles the complexity well.

## Common Pitfalls

### Pitfall 1: Two yolo-dev Directories
**What goes wrong:** Targeting `~/clawd/yolo-dev/` instead of `~/clawd/agents/main/yolo-dev/`
**Why it happens:** Both exist. The host-level one was used during initial protocol development.
**How to avoid:** Always use `/home/ubuntu/clawd/agents/main/yolo-dev/` -- this is the path used by the dashboard API (YOLO_DIR in route.ts) and the Docker bind-mount.
**Warning signs:** Build slugs don't match between DB and filesystem.

### Pitfall 2: Deleting Builds the Agent is Currently Writing
**What goes wrong:** Cleanup script runs while a YOLO build is in progress (status=building/testing)
**Why it happens:** The cron build runs at 7:30 UTC, cleanup might overlap.
**How to avoid:** Only delete builds with terminal statuses: `status IN ('success', 'partial', 'failed')`. The query in Pattern 2 already includes this filter.
**Warning signs:** "idea" or "building" status builds disappearing.

### Pitfall 3: Iframe Security (Already Handled)
**What goes wrong:** Embedded HTML could access parent page context or make network requests.
**Why it happens:** Missing sandbox restrictions on iframe.
**How to avoid:** The existing `sandbox="allow-scripts"` is correct. It allows JS execution (needed for interactive builds) but blocks forms, popups, same-origin access, and navigation. Since YOLO builds are Python stdlib + vanilla HTML with no external HTTP calls, this is appropriate.
**Warning signs:** None -- already correctly implemented.

### Pitfall 4: Score NULL Handling
**What goes wrong:** Builds with NULL self_score get deleted even though they might be valuable.
**Why it happens:** SQL comparison `self_score < 4` is false when self_score IS NULL. But `self_score IS NULL OR self_score < 4` catches both.
**How to avoid:** The cleanup query explicitly handles NULL: `(self_score IS NULL OR self_score < ?)`. This means NULL-scored builds ARE eligible for cleanup, which is correct -- unscored builds are incomplete.
**Warning signs:** Check that the query uses IS NULL OR, not just <.

### Pitfall 5: Host-Level vs Docker Paths
**What goes wrong:** Writing cleanup script that references `/workspace/yolo-dev/` (Docker path).
**Why it happens:** Copy-pasting from YOLO_BUILD.md which uses sandbox paths.
**How to avoid:** The cleanup script runs on the HOST via crontab, so use host paths: `/home/ubuntu/clawd/agents/main/yolo-dev/`.

## Code Examples

### Querying Build Age from yolo.db
```python
# Source: EC2 yolo.db schema + prune-sessions.sh pattern
import sqlite3
from datetime import datetime, timedelta

DB = "/home/ubuntu/clawd/agents/main/yolo-dev/yolo.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

# Builds eligible for cleanup: older than 30 days, not top-rated, terminal status
old_builds = conn.execute("""
    SELECT id, slug, date, self_score, status
    FROM builds
    WHERE date < ?
      AND (self_score IS NULL OR self_score < 4)
      AND status IN ('success', 'partial', 'failed')
""", (cutoff,)).fetchall()

# Builds protected: top-rated (score 4-5) regardless of age
protected = conn.execute("""
    SELECT id, slug, date, self_score
    FROM builds
    WHERE self_score >= 4
""").fetchall()

conn.close()
```

### Crontab Entry
```bash
# Daily YOLO build cleanup at 4:30am UTC (30min after prune-sessions)
30 4 * * * /home/ubuntu/scripts/cleanup-yolo-builds.sh >> /home/ubuntu/scripts/cleanup-yolo-builds.log 2>&1
```

### Verifying Iframe Preview (for UAT)
```bash
# Check which builds have HTML
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  "sqlite3 ~/clawd/agents/main/yolo-dev/yolo.db \"SELECT slug, name FROM builds\" && echo '---' && for d in ~/clawd/agents/main/yolo-dev/*/; do [ -f \"\$d/index.html\" ] && echo \"HTML: \$(basename \$d)\"; done"

# Test iframe serving
curl -s http://127.0.0.1:3001/api/yolo/files/007-expense-tracker-dashboard/index.html | head -5
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No preview | Iframe with sandbox="allow-scripts" | Phase 44 (2026-03-01) | PREV-01 already satisfied |
| No cleanup | No cleanup (only 8 builds, 208KB) | Current state | PREV-02 needed for sustainability |

**Current build stats:**
- 8 builds total in DB, all score 4, all success
- Oldest build: 2026-02-24 (6 days old -- none would be deleted today)
- Total disk: ~208KB across all builds
- Disk available: 17GB of 38GB (57% used)

## Open Questions

1. **Should DB rows be deleted or just disk files?**
   - What we know: Keeping DB rows preserves trend chart data. Disk files are the only space concern.
   - Recommendation: **Delete only disk files, keep DB rows.** This preserves historical trends. If a build's files are deleted, the detail page just won't show file viewer or iframe -- all metadata still visible.

2. **What score threshold defines "top-rated"?**
   - What we know: Current scale is 1-5. All 8 builds are score 4. Success criteria says "top-rated."
   - Recommendation: **Score >= 4** (solid + impressive). This matches the YOLO_BUILD.md criteria where 4=solid and 5=impressive.

3. **Should `~/clawd/yolo-dev/` also be cleaned?**
   - What we know: This is a separate directory not used by the dashboard. Contains host-level builds (000-test, 005, 007).
   - Recommendation: **Include it in cleanup** for disk hygiene, but as a secondary concern. Primary target is agents/main/yolo-dev/.

## Sources

### Primary (HIGH confidence)
- EC2 filesystem inspection via SSH -- verified all file paths, DB schema, existing code
- `src/app/yolo/[slug]/page.tsx` -- confirmed iframe preview implementation
- `src/app/api/yolo/builds/[slug]/route.ts` -- confirmed hasHtml detection
- `src/app/api/yolo/files/[...path]/route.ts` -- confirmed file serving with MIME types
- `src/lib/queries/yolo.ts` -- confirmed query layer and YOLO_DIR path
- `src/lib/db-paths.ts` -- confirmed yolo DB path
- `yolo.db` schema via `sqlite3 .schema builds`
- `prune-sessions.sh` -- verified existing cleanup pattern
- `crontab -l` -- verified existing scheduled jobs
- [Next.js 14 CSP docs](https://nextjs.org/docs/14/pages/building-your-application/configuring/content-security-policy) -- iframe sandbox best practices

### Secondary (MEDIUM confidence)
- Phase 44 PLAN.md and CONTEXT.md -- confirmed what was built and the existing state

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified all existing code and infrastructure on EC2
- Architecture: HIGH - both patterns (iframe existing, cleanup script) are well-understood
- Pitfalls: HIGH - identified from direct inspection of code and file system

**Research date:** 2026-03-02
**Valid until:** 2026-04-01 (stable infrastructure, no moving targets)
