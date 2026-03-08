# Stack Research: v2.9 Memory System Overhaul

**Project:** pops-claw — Bob's Broken Memory System Fix
**Researched:** 2026-03-08
**Confidence:** HIGH (existing deployment validated), MEDIUM (QMD collection bootstrapping — known-buggy area), LOW (specific openclaw.json config values — version-specific behavior)

---

## Executive Summary

v2.9 adds zero new infrastructure. The full tech stack already exists on EC2. The work is:
1. Config edits to `~/.openclaw/openclaw.json` (compaction tuning + QMD paths)
2. CLI commands run on EC2 to bootstrap QMD collections (`qmd collection add`, `qmd update`, `qmd embed`)
3. Markdown file writes to agent workspaces (MEMORY.md seeding, AGENTS.md retrieval protocol)
4. A new API route + panel in Mission Control for memory health visibility

**The single biggest risk:** QMD's collection bootstrapping is a known-buggy area in OpenClaw. Issue #11308 documents "systemic issues requiring comprehensive fix." The collection-name conflict recovery and duplicate-document recovery fixes landed in recent releases — v2026.3.2 should have them, but manual verification after each bootstrap step is mandatory.

---

## What NOT to Change (Working Fine)

| Component | Current State | Why to Leave It Alone |
|-----------|--------------|----------------------|
| `memory.backend = "qmd"` | Already set | QMD is correctly configured as the backend. The problem is empty collections, not backend selection |
| `memory.searchMode = "search"` | Already set to BM25+vectors | Correct for t3.small CPU — avoids the slow LLM reranker. Do not switch to `query` mode |
| `contextPruning: cache-ttl` | Already set with 1h TTL | Working. Leave alone |
| Gemini embeddings config | Already set in `memorySearch.provider: gemini` | Fallback path. QMD uses its own embeddinggemma-300M model for local embeddings |
| `embeddinggemma-300M` model files | Already in `~/.cache/qmd/models/` | Models downloaded. No re-download needed |
| QMD v1.1.0 install | `~/.bun/bin/qmd` | Already installed. No upgrade needed |
| Bun v1.3.10 | `~/.bun/bin/bun` | Required runtime for QMD. Working |
| Docker sandbox / bind-mounts | All 6 DBs bind-mounted | No changes needed |
| 7-agent roster, 24 cron jobs, 13 skills | All verified v2.8 | No changes needed |

---

## Recommended Stack

### Core: QMD Collection Bootstrap (Zero New Dependencies)

| Component | Current State | Target State | Config Location |
|-----------|-------------|-------------|----------------|
| QMD memory-dir-main collection | 19 files (from MEMORY.md context) | 19+ files indexed with valid embeddings | QMD auto-manages at `~/.openclaw/agents/main/qmd/` |
| QMD memory-root-main collection | Exists, 0 documents indexed | Documents indexed via `qmd update && qmd embed` | Same XDG dir |
| QMD memory-alt-main collection | Exists, 0 documents indexed | Documents indexed | Same XDG dir |
| QMD update interval | 15m (current) | 15m (no change) | `memory.qmd.update.interval` in openclaw.json |

**Bootstrap sequence (run on EC2 as ubuntu user):**

```bash
# Step 1: Verify current collection state
~/.bun/bin/qmd collection list --json

# Step 2: If collections exist but have 0 documents, force re-index
~/.bun/bin/qmd update

# Step 3: Force re-embed (generates vectors for all documents)
~/.bun/bin/qmd embed

# Step 4: Verify indexing worked
~/.bun/bin/qmd collection list --json
# Should show document counts > 0 for memory-root-main, memory-alt-main, memory-dir-main

# Step 5: Test search works end-to-end
~/.bun/bin/qmd search "Andy" --collection memory-dir-main
# Should return results from MEMORY.md and daily logs
```

**If collections are missing entirely** (QMD bug: collection-name conflict leaves orphan entry):

```bash
# Remove all managed collections and let OpenClaw recreate them
~/.bun/bin/qmd collection list --json
# Note all collection names, then remove them:
~/.bun/bin/qmd collection remove memory-root-main
~/.bun/bin/qmd collection remove memory-alt-main
~/.bun/bin/qmd collection remove memory-dir-main

# Restart gateway — OpenClaw will recreate collections on boot
systemctl --user restart openclaw-gateway.service
# Wait 60 seconds, then verify:
~/.bun/bin/qmd collection list --json
```

**If `qmd collection add` fails with "collection already occupies same path + pattern"** (Issue #23613 workaround — fixed in recent releases but may still trigger):

```bash
# Identify conflicting collection
~/.bun/bin/qmd collection list --json | python3 -m json.tool

# Remove the conflicting one by name
~/.bun/bin/qmd collection remove <conflicting-name>

# Restart gateway to trigger clean re-add
systemctl --user restart openclaw-gateway.service
```

**Confidence:** MEDIUM. The bootstrap commands are correct per QMD v1.1.0 docs and community guides. The specific error paths depend on current collection state, which requires SSH inspection to determine.

---

### Config: Compaction Tuning

These are the only `openclaw.json` changes needed. Current values are known; target values are research-backed recommendations.

| Parameter | Current Value | Target Value | Why |
|-----------|-------------|-------------|-----|
| `compaction.reserveTokensFloor` | Unknown (default ~20000) | `20000` | Keep at default. Lower values risk context overflow; higher values trigger compaction too early on 200K window |
| `compaction.softThresholdTokens` | `3000` (set in Phase 34) | `8000` | 3000 is too low per Issue #17034 — softThresholdTokens doesn't scale; at 3000 the flush triggers far too late (near window edge) leaving no room to write memories. 8000 gives ~170K tokens of working space in a 200K window |
| `compaction.memoryFlush.enabled` | `true` | `true` (no change) | Already enabled |
| `compaction.memoryFlush.prompt` | Unknown | `"Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."` | Standard prompt per OpenClaw docs. Verify this matches current config |
| `compaction.contextTokens` | Unknown (default) | Do not set | This is a read-only computed field, not a config. Do not touch |

**Why softThresholdTokens 8000 specifically:**
- Formula: `flush_threshold = contextWindow - reserveTokensFloor - softThresholdTokens`
- With contextWindow=200000, reserveTokensFloor=20000, softThresholdTokens=8000: flush triggers at 172000 tokens
- Bob's heartbeat sessions rarely reach 172K — this is why the flush rarely fires
- **The real fix for daily logs is the `daily-memory-flush` cron (already deployed), not compaction tuning**
- softThresholdTokens=8000 is a safety net for long DM sessions; the cron is the primary flush mechanism

**Confidence for compaction values:** MEDIUM. Values are from community benchmarks (Issue #17034, VelvetShark guide). The exact optimal values depend on Bob's session length distribution, which requires observability.db analysis.

**openclaw.json patch (Python3 snippet to apply on EC2):**

```python
import json, shutil, sys
path = '/home/ubuntu/.openclaw/openclaw.json'
shutil.copy(path, path + '.bak')
with open(path) as f:
    cfg = json.load(f)

# Navigate to compaction section
# Adjust path based on actual config structure
agents = cfg.setdefault('agents', {})
defaults = agents.setdefault('defaults', {})
compaction = defaults.setdefault('compaction', {})

# Only change softThresholdTokens — others already correct
compaction['softThresholdTokens'] = 8000

with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
print('Done. Verify with: grep softThresholdTokens ~/.openclaw/openclaw.json')
```

---

### Config: QMD Paths in openclaw.json

Verify (and if missing, add) the `memory.qmd.paths` config. This tells OpenClaw which directories to index beyond the default workspace memory files.

**Target config (verify this exists in openclaw.json):**

```json
{
  "memory": {
    "backend": "qmd",
    "qmd": {
      "update": {
        "interval": "15m"
      },
      "searchMode": "search",
      "limits": {
        "maxResults": 6,
        "timeoutMs": 4000
      }
    }
  }
}
```

**What to check for and add if missing:**
- `memory.qmd.update.interval` — must exist, currently `15m`, leave at `15m`
- `memory.qmd.searchMode` — must be `"search"` (BM25+vectors), NOT `"query"` (LLM reranker — too slow for t3.small)
- `memory.qmd.limits.timeoutMs` — recommend `4000` (4 seconds). Default may be lower; timeouts cause search to silently return empty results

**Confidence:** MEDIUM. Config key names from official docs (`docs.openclaw.ai/concepts/memory`) and Issue #10042. The exact nesting path requires verifying against current openclaw.json.

---

### Config: Memory Flush — Isolated Cron Sessions

**Critical finding:** Memory flush is silently skipped for isolated cron sessions with read-only workspace access.

Per OpenClaw docs and Issue #37634: `workspaceAccess: "ro"` or `"none"` causes memoryFlush to be skipped — the agent can't write `memory/YYYY-MM-DD.md` to a read-only workspace.

**What this means for Phase 34's `daily-memory-flush` cron:**
- The `daily-memory-flush` cron was deployed with `isolated: true`
- If it runs with default sandbox config (workspaceAccess unset or "ro"), the cron fires but memoryFlush writes are silently skipped
- This is separate from the compaction-triggered memoryFlush — the cron sends a message asking Bob to write; if Bob's sandbox allows file writes, this works regardless of memoryFlush setting
- Bob writes via explicit tool call (write_file), not via the compaction flush mechanism — so the cron approach works as long as the workspace is writable (which it is in the existing Docker setup with rw bind-mounts)

**Action:** Verify `daily-memory-flush` cron has NOT set `workspaceAccess: "ro"`. If it's not set explicitly, it inherits from `agents.defaults.sandbox` which has rw bind-mounts, so it should work.

```bash
# Verify on EC2:
python3 -c "
import json
with open('/home/ubuntu/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
crons = cfg.get('crons', [])
flush_cron = [c for c in crons if 'memory-flush' in c.get('id','') or 'memory-flush' in c.get('name','')]
import pprint; pprint.pprint(flush_cron)
"
```

---

### Mission Control: Memory Health Panel

**Pattern:** Identical to existing Mission Control pages. Zero new npm packages.

| Component | Status | Location |
|-----------|--------|----------|
| `/api/memory/health` route | New | `src/app/api/memory/health/route.ts` |
| Memory health panel | New | Added to top of `src/app/memory/page.tsx` |
| SWR polling | Existing 30s provider | No changes to SWR config |
| shadcn/ui Card, Badge | Already installed | Card per agent |
| MEMORY.md file reads | Direct `fs.readFileSync` | Count lines from `~/clawd/agents/{agent}/MEMORY.md` |
| `git log` for flush history | `child_process.execSync` | Shell out from API route |
| Chart component | Recharts (already installed) | 7-bar sparkline for flush frequency |

**Budget visualization data source:**

```typescript
// src/app/api/memory/health/route.ts
import { execSync } from "child_process";
import { readFileSync, existsSync } from "fs";

const AGENT_WORKSPACES = {
  main: "/home/ubuntu/clawd/agents/main",
  landos: "/home/ubuntu/clawd/agents/landos",
  rangeos: "/home/ubuntu/clawd/agents/rangeos",
  ops: "/home/ubuntu/clawd/agents/ops",
  quill: "/home/ubuntu/clawd/agents/quill",
  sage: "/home/ubuntu/clawd/agents/sage",
  ezra: "/home/ubuntu/clawd/agents/ezra",
};

// Line count: readFileSync + split('\n').length
// Staleness: git log --since="7 days ago" --format="%ai" -- agents/{id}/memory/*.md
// Flush frequency: parse git log output into 7-day histogram
```

**Key design decisions (from Phase 36 CONTEXT.md):**
- Warning at 160 lines (80% of 200-line budget), critical at 190 lines (95%)
- Staleness badge: 3+ days with no flush = yellow, not an error
- All 7 agents shown; agents without MEMORY.md show gray "No Memory" card
- Separate `/api/memory/health` endpoint from existing `/api/memory` browse endpoint
- Sparkline: 7-bar chart, 1 bar per day, hidden on mobile

**git log for flush data:**

```bash
# Command to shell out from API route (repo root = /home/ubuntu/Desktop/Projects/pops-claw or ~/clawd/)
git -C /home/ubuntu/Desktop/Projects/pops-claw log \
  --since="7 days ago" \
  --format="%as" \
  -- "agents/main/memory/*.md"
```

**Note:** The git repo is at `/Users/andykaufman/Desktop/Projects/pops-claw` (local Mac), not on EC2. Memory files are on EC2 but not git-tracked there. The health API route must read MEMORY.md line counts via filesystem, not git. For flush frequency, use `ls -lt ~/clawd/agents/main/memory/*.md` and parse timestamps, OR read modification times via `fs.statSync`.

**Revised flush sparkline approach** (no git dependency on EC2):

```typescript
import { readdirSync, statSync } from "fs";
import { join } from "path";

function getFlushHistory(workspace: string): number[] {
  // Returns array of 7 numbers (flushes per day, oldest to newest)
  const memDir = join(workspace, "memory");
  if (!existsSync(memDir)) return [0, 0, 0, 0, 0, 0, 0];

  const now = Date.now();
  const files = readdirSync(memDir).filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/));
  const counts = new Array(7).fill(0);

  for (const file of files) {
    const stat = statSync(join(memDir, file));
    const daysAgo = Math.floor((now - stat.mtimeMs) / 86400000);
    if (daysAgo < 7) counts[6 - daysAgo]++;
  }
  return counts;
}
```

**Confidence:** HIGH. Pattern is established across 7 existing Mission Control pages. The only novel element is shelling out for file stats, which is standard Node.js.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| QMD collection bootstrap | Manual `qmd update && qmd embed` CLI | Restart gateway and wait for auto-bootstrap | Auto-bootstrap silently fails due to collection-name conflicts (Issue #23613). Manual commands give immediate feedback |
| Compaction flush | `softThresholdTokens: 8000` | Lower (3000) or higher (20000) | 3000 is current setting that's too low; 20000 risks never triggering on short sessions. 8000 is community consensus for 200K window |
| Memory flush for daily logs | `daily-memory-flush` cron (already deployed) | Rely on compaction-triggered flush | Compaction flush only fires near context limit — heartbeat sessions never get there. Cron is the reliable mechanism |
| Flash sparkline data source | `fs.statSync` on memory/ files | `git log` | EC2 does not have the pops-claw git repo checked out — git log would fail |
| searchMode | `"search"` (BM25+vectors) | `"query"` (LLM reranker) | t3.small CPU cannot handle LLM reranker latency (3-10s per query). `"search"` is fast (<200ms) |
| Memory health data | API route reads disk directly | Add new SQLite table for memory stats | No new DB needed — MEMORY.md is a file, not a database record. Direct file reads are simpler and more accurate |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `memory.qmd.searchMode: "query"` | LLM reranker kills t3.small CPU (10-30s per query, t3.small has 2 vCPU). Community confirmed "query mode unusable on constrained hardware" | `"search"` — BM25+vectors, fast on any hardware |
| New QMD models (reranker) | embeddinggemma-300M is already downloaded. Adding qmd-query-expansion-1.7B (already installed per MEMORY.md) via "query" mode adds latency, not recall quality | Leave models as-is. `"search"` mode uses embeddinggemma-300M which is already present |
| Per-agent QMD XDG dirs | OpenClaw auto-manages these at `~/.openclaw/agents/<agentId>/qmd/`. Manual intervention causes drift | Let OpenClaw manage. Only intervene when collections are provably empty or corrupt |
| `memory.qmd.paths` custom entries | Adding custom paths to QMD config risks triggering the "collection already occupies same path" bug (Issue #23613) | Let OpenClaw manage default paths (memory-root, memory-alt, memory-dir). Seed content into these paths via MEMORY.md and memory/ files |
| WebSocket for memory health panel | Single user, overnight use case | SWR 30s polling — same as all other Mission Control panels |
| Per-agent memory databases | QMD XDG isolation already provides per-agent scope | Shared QMD binary, per-agent XDG home. No new databases |
| `openclaw memory search` CLI for verification | OpenClaw CLI memory search is the thing that's broken. Don't verify the fix using the broken tool | Use `qmd search "test" --collection memory-dir-main` directly to verify QMD indexing, then test `openclaw memory search` after |

---

## Version Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| OpenClaw | v2026.3.2 | Has collection-name conflict recovery fix (Issue #23613 workaround). Has duplicate-document recovery fix. **Regression in v2026.3.1 (aggressive compaction loop with memoryFlush) — check if this is still present in v2026.3.2** |
| QMD | v1.1.0 | Installed at `~/.bun/bin/qmd`. `qmd collection add`, `qmd update`, `qmd embed` are valid v1.1.0 commands |
| Bun | v1.3.10 | Required by QMD. Working. No upgrade needed |
| embeddinggemma-300M | Current | Already in `~/.cache/qmd/models/`. Used for vector embeddings in `"search"` mode |
| qmd-query-expansion-1.7B | Current | Already downloaded per MEMORY.md. Needed for `"query"` mode LLM reranking. NOT used in `"search"` mode |
| Next.js | 14.2.15 | Mission Control. No upgrade needed for health panel |
| better-sqlite3 | 12.6.2 | Not used for memory health panel (reads files, not SQLite) |
| Node.js `fs` + `child_process` | Built-in | Used by health API route for file reads and timestamp parsing |

**Known v2026.3.1 regression (verify fixed in v2026.3.2):**
Issue #32106: `softThresholdTokens` changes in v2026.3.1 caused aggressive compaction loops when memoryFlush was enabled. The current v2026.3.2 deployment should have this fixed, but after changing `softThresholdTokens`, monitor for unexpected compaction storms in `journalctl --user -u openclaw-gateway.service`.

---

## Installation / Setup Summary

```bash
# On EC2 (100.72.143.9) via SSH

# === STEP 1: QMD Collection Bootstrap ===
# Check current state
~/.bun/bin/qmd collection list --json

# Force re-index existing files
~/.bun/bin/qmd update && ~/.bun/bin/qmd embed

# Verify documents indexed
~/.bun/bin/qmd collection list --json
# Confirm non-zero doc counts for memory-root-main, memory-alt-main, memory-dir-main

# Test search end-to-end
~/.bun/bin/qmd search "Andy" --collection memory-dir-main

# === STEP 2: Compaction Config Tune ===
# Verify current softThresholdTokens
grep softThresholdTokens ~/.openclaw/openclaw.json
# If still 3000, change to 8000:
python3 -c "
import json, shutil
path = '/home/ubuntu/.openclaw/openclaw.json'
shutil.copy(path, path + '.bak')
cfg = json.load(open(path))
# Navigate to compaction config — path varies by config structure
# Edit the softThresholdTokens value
# cfg['agents']['defaults']['compaction']['softThresholdTokens'] = 8000
# Save
open(path, 'w').write(json.dumps(cfg, indent=2))
"

# === STEP 3: MEMORY.md Seeding ===
# Write curated long-term memory for Bob (see Phase plan for content)
# Target: ~/clawd/agents/main/MEMORY.md with 50-80 lines of curated facts
# Verify word count is sane
wc -l ~/clawd/agents/main/MEMORY.md

# === STEP 4: Restart Gateway (batch all config changes) ===
systemctl --user restart openclaw-gateway.service
# Wait for healthy status
journalctl --user -u openclaw-gateway.service --since '1 min ago' | tail -20

# === STEP 5: Verify Memory Search Works ===
# After restart, test via openclaw CLI
/home/ubuntu/.npm-global/bin/openclaw memory search "Andy preferences"
# Should return results from MEMORY.md

# === STEP 6: Mission Control Health Panel ===
# Edit on EC2: ~/clawd/mission-control/
# New file: src/app/api/memory/health/route.ts
# Modify: src/app/memory/page.tsx (add panel at top)
cd ~/clawd/mission-control
npm run build
systemctl --user restart mission-control.service
```

**Packages to install:** None.
**Packages to remove:** None.
**Docker images to build:** None.
**New agents to configure:** None.
**New databases to create:** None.
**New cron jobs to add:** None (daily-memory-flush cron already deployed in Phase 34).

---

## Sources

### HIGH confidence
- [OpenClaw Memory Docs](https://docs.openclaw.ai/concepts/memory) — QMD backend config keys, memoryFlush behavior, workspaceAccess constraint, default collection names
- [OpenClaw Session Management Docs](https://docs.openclaw.ai/reference/session-management-compaction) — reserveTokensFloor, softThresholdTokens, flush threshold formula
- [QMD GitHub: tobi/qmd](https://github.com/tobi/qmd) — `qmd collection add`, `qmd update`, `qmd embed` CLI commands verified
- PROJECT.md (internal) — confirmed QMD v1.1.0 at `~/.bun/bin/qmd`, searchMode=search, update interval=15m, embeddinggemma-300M present, 0 documents indexed
- MEMORY.md (internal) — confirmed QMD backend switch date, collection counts, memory file counts per agent

### MEDIUM confidence
- [OpenClaw Issue #11308](https://github.com/openclaw/openclaw/issues/11308) — QMD systemic issues, collection management bugs
- [OpenClaw Issue #23613](https://github.com/openclaw/openclaw/issues/23613) — "Collection not found: memory-root-main" bug and workaround
- [OpenClaw Issue #17034](https://github.com/openclaw/openclaw/issues/17034) — softThresholdTokens doesn't scale with context window size; community values
- [OpenClaw Issue #32106](https://github.com/openclaw/openclaw/issues/32106) — v2026.3.1 aggressive compaction loop regression with memoryFlush
- [OpenClaw Issue #37634](https://github.com/openclaw/openclaw/issues/37634) — workspaceAccess: "none" keeps workspace off-limits, memoryFlush skipped
- [OpenClaw Discussion #25633](https://github.com/openclaw/openclaw/discussions/25633) — "Memory is broken by default" community discussion with config recommendations
- [VelvetShark OpenClaw Memory Masterclass](https://velvetshark.com/openclaw-memory-masterclass) — softThresholdTokens=8000 for 200K window, community validated
- [Jose Casanova: Fix OpenClaw Memory Search with QMD](https://www.josecasanova.com/blog/openclaw-qmd-memory) — bootstrap command sequence verified
- Phase 34 VERIFICATION.md (internal) — confirmed softThresholdTokens=3000 current, daily-memory-flush cron deployed

### LOW confidence (WebSearch only, needs EC2 verification)
- Exact openclaw.json nesting path for `compaction.softThresholdTokens` — needs `cat ~/.openclaw/openclaw.json | python3 -m json.tool` to confirm
- Whether v2026.3.1 compaction regression is present in v2026.3.2 — needs monitoring after gateway restart
- Whether `daily-memory-flush` cron currently has `workspaceAccess` explicitly set — needs inspection

---

*Stack research for: pops-claw v2.9 Memory System Overhaul — fixing broken QMD collections, compaction config, and memory flush*
*Researched: 2026-03-08*
*Replaces: previous STACK.md covering v2.7 YOLO Dev autonomous builder*
