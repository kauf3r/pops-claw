# Phase 52: MEMORY.md & Content Seeding - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Create MEMORY.md at ~/clawd/agents/main/MEMORY.md with curated long-term knowledge, improve the compaction flush prompt to produce rich structured daily summaries, and verify QMD indexes the new content into memory-root-main. No retrieval protocol changes (Phase 53), no health monitoring (Phase 54), no LEARNINGS.md (Phase 53).

</domain>

<decisions>
## Implementation Decisions

### Knowledge Scope & Depth
- Full institutional memory: system facts + personal preferences + milestone/decision history
- One-liner telegram format (~15 words per entry) to maximize density in budget
- AirSpace Integration: minimal reference only — note existence, point to SECURITY_PROJECT.md and workspace protocol docs. Don't duplicate.
- Key Decisions: Claude selects operationally relevant subset from PROJECT.md Key Decisions table (ones Bob encounters in daily cron/DM sessions)

### File Structure & Format
- Categorized sections with H2 headers (Infrastructure, Agents, Databases, Crons, Skills, Preferences, History, etc.)
- "Last curated: YYYY-MM-DD" timestamp at top for staleness visibility
- Start lean at 80-100 lines — leave headroom for organic growth via flush
- LEARNINGS.md deferred to Phase 53 (separate file, separate purpose)

### Delivery Method
- Write MEMORY.md locally on Mac, verify content, SCP to ~/clawd/agents/main/MEMORY.md
- Verify QMD indexes it (qmd update && qmd search test query on memory-root-main)

### Flush Prompt Redesign
- Structured template with defined sections: ## Session Summary, ## DB State, ## Decisions, ## Open Items
- Embed specific SQL queries in prompt (SELECT COUNT(*) from each DB, recent entries, etc.) — concrete numbers, not vibes
- Quiet days: minimal entry with DB snapshot only (~5 lines min, "No user sessions today. DB state: [numbers]")
- Active days: full template, target 10+ lines per SC3
- Keep existing flush path/destination — only improve prompt content, don't change infrastructure

### Maintenance & Currency
- Hybrid ownership: user owns static sections (infrastructure, agents, preferences), Bob appends "Recent Changes" section during flush
- Curation cadence: per milestone (after each milestone ships, review MEMORY.md as part of archive workflow)
- No staleness detection in this phase — Phase 54's health monitoring handles that
- Phase 36's 200-line budget and 160/190 warning/critical thresholds still apply

### Claude's Discretion
- Exact SQL queries to embed in flush prompt
- Which PROJECT.md Key Decisions are operationally relevant for Bob
- Category names and section heading order for MEMORY.md
- How to verify QMD re-indexing after MEMORY.md placement
- Specific DB paths to use in flush template queries

</decisions>

<specifics>
## Specific Ideas

- Start lean (80-100 lines) specifically to test whether the improved flush prompt builds memory organically — if daily entries don't grow MEMORY.md meaningfully, that signals a flush prompt issue before Phase 53
- One-liner format matches LEARNINGS.md pattern from Phase 35 — consistency across memory files
- "Per milestone curation" aligns with existing milestone archive workflow — no new process to maintain

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- openclaw.json: flush prompt at `agents.defaults.compaction.memoryFlush` (structured prompt, softThresholdTokens=8000)
- QMD CLI: v1.1.0 at ~/.bun/bin/qmd — `qmd update`, `qmd embed`, `qmd search`
- QMD collections: memory-root-main, memory-alt-main, memory-dir-main (all bootstrapped in Phase 51)
- 6 SQLite DBs to query: health.db, coordination.db, content.db, email.db, observability.db, yolo.db

### Established Patterns
- Config changes via SSH + jq or direct file edit on EC2
- SCP for file delivery from Mac to EC2
- QMD indexing: 15-minute update interval auto-indexes workspace files
- Bob's workspace: ~/clawd/agents/main/ (bind-mounted to /workspace/ in Docker)

### Integration Points
- MEMORY.md path: ~/clawd/agents/main/MEMORY.md (memory-root-main collection watches this)
- Flush prompt: agents.defaults.compaction.memoryFlush in openclaw.json
- Daily log path: check current memoryFlush config for existing destination
- QMD verification: `XDG_CONFIG_HOME=~/.openclaw/agents/main/qmd XDG_CACHE_HOME=~/.openclaw/agents/main/qmd qmd search "query"`

</code_context>

<deferred>
## Deferred Ideas

- LEARNINGS.md creation — Phase 53 (retrieval protocol work)
- Content agent BOOTSTRAP.md files — Phase 53 or future phase
- Multi-agent MEMORY.md seeding — out of scope per REQUIREMENTS.md
- Staleness detection in Bob — Phase 54 handles via health monitoring

</deferred>

---

*Phase: 52-memory-md-content-seeding*
*Context gathered: 2026-03-08*
