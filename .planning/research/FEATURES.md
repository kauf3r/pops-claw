# Feature Research

**Domain:** OpenClaw agent memory system fixes (v2.9 — broken components on live v2026.3.2 deployment)
**Researched:** 2026-03-08
**Confidence:** HIGH — verified against live EC2 system state via direct SSH inspection

## Current State Diagnosis

Before features, a diagnosis of what's actually broken vs working — confirmed via SSH.

| Component | Status | Evidence |
|-----------|--------|----------|
| QMD backend configured | WORKING | `memory.backend: "qmd"` in openclaw.json |
| QMD binary installed | WORKING | `/home/ubuntu/.bun/bin/qmd` v1.1.0 responds to commands |
| `memory-dir-main` collection | WORKING | 21 daily log files indexed, search returns scored results |
| QMD search returns results | WORKING | `qmd search "Andy"` returns results from memory/ logs |
| `memory-root-main` collection | BROKEN | Pattern: MEMORY.md, path: `~/clawd/agents/main/` — file does not exist there (0 files) |
| `memory-alt-main` collection | BROKEN | Pattern: memory.md (lowercase alias), same root — 0 files |
| MEMORY.md file itself | EXISTS BUT WRONG PLACE | At `~/clawd/MEMORY.md` (91 lines), QMD looks in `~/clawd/agents/main/` |
| MEMORY.md content freshness | STALE | Last updated 2026-02-23 — 4+ weeks behind. Missing QMD, v2.8 features, 6 DBs, content pipeline status |
| Memory flush produces daily logs | WORKING | Logs exist Feb 2 – Mar 7 in `~/clawd/agents/main/memory/` |
| Memory flush log quality | LOW | Most days are 1-3 lines ("Quiet day — heartbeat only"). Mar 7 (notable day) = 23 lines. Most cron-activity days go unrecorded |
| AGENTS.md retrieval protocol | MISSING | AGENTS.md contains only "Operator Mindset" — no instruction to search QMD before acting |
| Memory health monitoring | MISSING | Nothing verifies QMD is indexing, logs are being written, or search returns results |
| `softThresholdTokens` setting | POORLY TUNED | Set to 1500 — fires flush when only 1500 tokens remain before hard limit. Very tight, leaves little headroom for Bob to write a good summary |
| QMD embed backlog | MINOR ISSUE | `qmd status` shows 1 file pending embedding. Cosmetic but indicates stale embed run |

---

## Feature Landscape

### Table Stakes (System Must Have These to Work)

Features the memory system requires to function at all. Missing these = memory doesn't work.

| Feature | Why Required | Complexity | Current State |
|---------|--------------|------------|---------------|
| MEMORY.md in correct location | QMD `memory-root-main` collection looks in `~/clawd/agents/main/` for `MEMORY.md`. File lives at `~/clawd/MEMORY.md`. Collection has 0 files until this is fixed. Long-term curated facts are never retrievable | LOW — move file or symlink or reconfigure collection path | BROKEN |
| Curated MEMORY.md content (current) | Even after fixing location, MEMORY.md is 4+ weeks stale. Missing: QMD as memory backend, v2.8 build artifacts, all 6 databases, content pipeline operational status, resend outage, memory/ directory pattern | MEDIUM — content writing, requires knowing current system state | STALE |
| Compaction thresholds tuned | `softThresholdTokens: 1500` fires flush when only 1500 tokens of context remain. Bob may not have sufficient context left to write a useful summary. Raising to 8000-12000 gives meaningful headroom | LOW — JSON config edit to openclaw.json | EXISTS but poorly tuned |
| memoryFlush prompt produces consistent logs | Current prompt instructs Bob to write to `memory/$(date +%Y-%m-%d).md`. Shell substitution doesn't execute in JSON — Bob infers the date via LLM (works, but fragile). More importantly, the prompt doesn't tell Bob to check cron DB outputs on quiet days, producing 1-3 line logs when 10-15 lines would be appropriate | LOW — update prompt text in openclaw.json | EXISTS but shallow |
| Retrieval protocol in AGENTS.md | Without explicit instruction to search QMD before acting, Bob never retrieves from memory. The system is technically running but behaviorally unused. This is the single most impactful fix | LOW — add section to AGENTS.md | MISSING |

### Differentiators (What Makes Memory Work Well, Not Just Exist)

Features that separate a memory system that actively helps from one that's merely configured.

| Feature | Value Proposition | Complexity | Current State |
|---------|-------------------|------------|---------------|
| Structured daily log format | Consistent sections in each daily log (Pipeline Status, System Events, User Interactions, Open Items) make QMD search more precise. Unstructured prose produces lower-quality retrieval | LOW — add section structure to flush prompt | INCONSISTENT |
| Flush prompt checks cron DB outputs | Even "quiet" days have cron activity. Morning briefing, heartbeats, content pipeline moves articles. Logs should reflect cron outputs (content.db stage counts, coordination.db tasks, email.db activity) even when no user interaction occurred | MEDIUM — extend flush prompt to include DB queries | MISSING |
| Memory health monitoring cron | Daily check: (a) yesterday's log was written, (b) QMD indexed it, (c) test search returns results. Alert to Slack if any check fails. Currently there is no way to know if the memory system silently stops working | MEDIUM — new cron + shell script on EC2 | MISSING |
| QMD embed run on schedule | `qmd status` shows 1 file pending embedding. Manual `qmd embed` would fix it. Adding embed to the update cycle prevents accumulation | LOW — add `qmd embed` call to cron or existing update hook | NOT CONFIGURED |
| LEARNINGS.md as QMD-indexed operational knowledge | Already exists at `~/clawd/agents/main/LEARNINGS.md` with rules like timezone handling. Currently not in a named QMD collection (falls under `**/*.md` in memory-dir-main if it's in the memory/ subdir — it's NOT). Should be explicitly accessible | LOW — verify LEARNINGS.md is indexed, adjust path if needed | PARTIALLY WORKING |

### Anti-Features (Commonly Attempted, Often Counterproductive)

| Feature | Why Attempted | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Very aggressive compaction (softThresholdTokens: 1500) | Flush more often = more memory written | At 1500 tokens remaining, Bob has barely any context left to write a coherent summary. Also fires on heartbeat-only sessions producing noise. Current setting creates the illusion of frequent flushing while producing low-quality logs | Raise to 8000-12000. Fires earlier in the session lifecycle when Bob still has rich context. Result: better quality summaries, fewer trivially empty writes |
| Storing everything in daily logs indefinitely | Complete audit trail, no data loss | Logs accumulate without bound. `memory-dir-main` will eventually index hundreds of files. QMD search quality degrades as signal-to-noise drops — quiet-day entries dilute relevant content | Quality gate: flush prompt already has `NO_REPLY` escape for pure heartbeat sessions. Enforce it more strictly. Consider monthly summary + archive after 90 days (not v2.9) |
| Multiple MEMORY.md files per agent | Each agent has domain-specific long-term facts | 7 agents × MEMORY.md = 7 files to maintain. Non-interactive content agents (quill, sage, ezra) have no long-term memory needs — they run cron tasks with reference docs, not sessions | Only curate MEMORY.md for interactive agents with real sessions (main, landos, rangeos, ops). Content agents use reference docs |
| Real-time QMD indexing (sub-minute interval) | Memory searchable immediately after write | QMD update is CPU-intensive on t3.small. Current 15m interval is already reasonable. Sub-minute would cause sustained background load during peak agent hours | Keep 15m interval. Manual `qmd update` trigger for immediate needs (can add to flush prompt as a `bash` tool call after writing) |
| Dedicated memory management skill | User can browse, search, curate memory via Bob | Skill adds complexity — YAML frontmatter, installation, maintenance. QMD CLI already provides full functionality via bash tool. Bob can already run `qmd search "query"` directly | Use bash tool for all QMD operations. If a pattern becomes frequent, add it to AGENTS.md as a protocol, not a skill |
| Shell date expansion in flush prompt | Dynamic filename generation | JSON config doesn't execute shell. `$(date +%Y-%m-%d)` is a literal string. Bob's LLM correctly infers the current date anyway — the behavior is correct despite the syntax being wrong. Fixing the syntax (e.g., wrapping in a script) adds complexity without benefit | Leave as-is. The LLM reads intent and uses the current date. Document as "LLM-interpreted" in AGENTS.md retrieval protocol |

---

## Feature Dependencies

```
MEMORY.md in correct location (~/clawd/agents/main/MEMORY.md)
    └──enables──> memory-root-main QMD collection (0 files → 1+ files indexed)
                      └──enables──> QMD retrieval returns long-term curated facts
                                        └──enhanced by──> MEMORY.md content freshness (4+ weeks to catch up)

Retrieval protocol in AGENTS.md
    └──requires──> QMD has something worth retrieving (memory-root-main + memory-dir-main populated)
    └──enables──> Bob searches QMD before acting on user requests
    └──enables──> Bob cites memory in responses ("based on my memory from March 3...")

Compaction threshold tuning (softThresholdTokens: 1500 → 8000)
    └──enables──> flush fires with meaningful context headroom
    └──enables──> higher quality daily log content
    └──enables──> better QMD search results from memory-dir-main

Flush prompt quality improvement
    └──requires──> compaction fires with headroom (otherwise prompt improvement is moot)
    └──enables──> daily logs include DB state queries (content.db, coordination.db, email.db)
    └──enables──> consistent section structure for better QMD retrieval

Memory health monitoring cron
    └──requires──> MEMORY.md location fixed (something in root collection to monitor)
    └──requires──> daily logs being written (something to verify)
    └──enables──> silent failure detection
    └──enables──> alert on indexing gaps
```

### Dependency Notes

- **Fix MEMORY.md location before anything else:** Retrieval protocol in AGENTS.md is worthless if the primary collection (memory-root-main) has 0 files. Fix location first.
- **Seed MEMORY.md content before adding retrieval protocol:** If Bob is instructed to "search memory before acting" but MEMORY.md is 4 weeks stale, he'll retrieve outdated facts and act on them. Current state → stale data. Fix location AND update content together.
- **Compaction tuning before flush prompt improvement:** If softThresholdTokens is still 1500, even a perfectly worded flush prompt won't help — Bob fires it with no context left. Tune threshold first, then refine the prompt.
- **Health monitoring is last:** Cannot monitor what doesn't exist. Build health check after collections are bootstrapped and logs are consistently high quality.

---

## MVP Definition

### Launch With (v2.9 core)

Minimum viable fix — memory meaningfully functional after these.

- [ ] **Fix MEMORY.md location** — move to `~/clawd/agents/main/MEMORY.md` or symlink from there to `~/clawd/MEMORY.md`. `memory-root-main` collection needs 1+ files. This is the single biggest broken component.
- [ ] **Seed MEMORY.md with current facts** — update content from 2026-02-23 baseline to 2026-03-08. Add: QMD memory backend, v2.8 features (YOLO detail page, build trends, agent board polish), all 6 databases and their purposes, content pipeline current status, resend outage status, memory/ directory pattern and daily log behavior.
- [ ] **Add retrieval protocol to AGENTS.md** — explicit section: "Before acting on user requests, domain questions, or system tasks, search QMD for relevant prior context using `qmd search [query]`. Cite retrieved context in responses." This is the behavioral change that makes memory useful.
- [ ] **Tune compaction thresholds** — raise `softThresholdTokens` from 1500 to 8000 in openclaw.json. Ensures flush fires with enough context headroom to write a meaningful 15-30 line summary.
- [ ] **Improve memoryFlush prompt** — add instruction to query coordination.db and content.db even on quiet days. Add consistent section structure (Pipeline Status, System Events, User Interactions, Open Items). Quiet days should produce 10-15 lines minimum (cron activity exists even without user interaction).

### Add After Validation (v2.9 polish)

Add once core is working and producing quality daily logs for 3-5 days.

- [ ] **Memory health monitoring cron** — daily cron that verifies: (a) yesterday's log was written, (b) `qmd status` shows it indexed, (c) `qmd search "recent activity"` returns a result from yesterday. Alert to Slack DM if any check fails. Prevents silent memory death.
- [ ] **QMD embed cleanup** — run `qmd embed` to clear the 1 pending file. Low priority but eliminates the warning from `qmd status`.

### Future Consideration (v3.0+)

Defer — not needed for v2.9 to succeed.

- [ ] **Per-agent MEMORY.md for interactive agents (landos, rangeos, ops)** — domain-specific long-term facts for Scout, Vector, Sentinel. High maintenance, not blocking v2.9.
- [ ] **Monthly memory compaction** — summarize old daily logs into quarterly summary, archive/delete raws. Not a problem yet with 21 files. Revisit at 100+ files.
- [ ] **Cross-agent memory sharing** — shared memory pool between agents. Not in QMD architecture. Requires custom implementation.
- [ ] **Memory browser page in Mission Control** — search/browse QMD index from dashboard. Nice to have, not critical once retrieval protocol is in AGENTS.md.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Fix MEMORY.md location | HIGH | LOW (move/symlink) | P1 |
| Seed MEMORY.md with current facts | HIGH | MEDIUM (content writing) | P1 |
| Add retrieval protocol to AGENTS.md | HIGH | LOW (add section to file) | P1 |
| Tune compaction thresholds | MEDIUM | LOW (JSON config edit) | P1 |
| Improve memoryFlush prompt | MEDIUM | LOW (JSON config edit) | P1 |
| Memory health monitoring cron | MEDIUM | MEDIUM (script + cron) | P2 |
| QMD embed cleanup | LOW | LOW (one command) | P2 |
| Per-agent MEMORY.md | LOW | HIGH (7 files, ongoing) | P3 |
| Monthly memory compaction | LOW | HIGH (new automation) | P3 |
| Cross-agent memory sharing | MEDIUM | HIGH (architecture change) | P3 |

**Priority key:**
- P1: Must have for v2.9 — memory doesn't meaningfully work without these
- P2: Should have — makes memory reliable and observable post-fix
- P3: Future consideration — deferred, not blocking

---

## What Working Memory Looks Like (Target State)

Reference: what success looks like after v2.9.

**QMD status (target):**
```
Collections
  memory-root-main (qmd://memory-root-main/)
    Pattern:  MEMORY.md
    Files:    1 (updated Xh ago)   ← currently 0
  memory-alt-main (qmd://memory-alt-main/)
    Pattern:  memory.md
    Files:    0 (expected — lowercase alias, no file)
  memory-dir-main (qmd://memory-dir-main/)
    Pattern:  **/*.md
    Files:    21+ (grows by 1 per day)
```

**Daily log quality (target):** 15-30 lines on normal days. Includes: pipeline stage counts from content.db, notable cron outputs, user interaction summary, open items. Currently: 1-3 lines on quiet days.

**Retrieval in action (target):** Bob receives "what's the status of the content pipeline?" → `qmd search "content pipeline"` → retrieves March 7 log showing 13 approved / 6 writing / 3 drafts → answers from memory. Currently: no search happens — Bob queries content.db directly every time, treating each session as if it has no prior context.

**MEMORY.md role (target):** Bob opens a new session. QMD surfaces MEMORY.md alongside recent daily logs. Bob immediately knows: Andy is in Santa Cruz, three domains, QMD is the memory backend, mission-control is on port 3001, resend email is broken, content pipeline has 13 approved articles. No re-discovery needed.

---

## Sources

- Live EC2 SSH inspection — `qmd status`, `qmd collection show`, `ls` commands (HIGH confidence)
- openclaw.json direct read — compaction config, memory config, contextTokens (HIGH confidence)
- `~/clawd/agents/main/AGENTS.md` direct read — confirmed no retrieval protocol (HIGH confidence)
- `~/clawd/MEMORY.md` existence confirmed, content read (91 lines, last updated 2026-02-23) (HIGH confidence)
- `~/clawd/agents/main/memory/` directory listing — 21 files, Feb 2 through Mar 7 (HIGH confidence)
- Daily log content inspection — 2026-03-07.md (23 lines), 2026-03-05.md (3 lines) (HIGH confidence)
- `qmd search "Andy"` — confirmed search returns results, scoring visible (HIGH confidence)
- PROJECT.md — v2.9 milestone target features, out-of-scope list (HIGH confidence)

---

*Feature research for: OpenClaw memory system (pops-claw v2.9)*
*Researched: 2026-03-08*
*Replaces: FEATURES.md for YOLO Dev v2.7 (shipped in v2.7/v2.8)*
