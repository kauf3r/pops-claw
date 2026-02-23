# Phase 35: Memory Retrieval Discipline - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Agents actively search their memory before starting tasks, and content agents retain context across cron-triggered sessions. AGENTS.md gets retrieval instructions, LEARNINGS.md gets seeded with real operational knowledge, and Quill/Sage/Ezra each get bootstrap memory files.

</domain>

<decisions>
## Implementation Decisions

### Retrieval Instructions
- Search triggers: session start + context keywords (references to past work, "follow up on", "what happened with", "last time")
- Cron jobs: only context-aware crons search memory (flagged in config); stateless crons skip
- Format: short "Memory Protocol" section in AGENTS.md — 3-4 bullet points, not a full procedure doc
- Search order: prioritized cascade — LEARNINGS.md first, daily logs (7 days), docs/ directory. Stop when context found.
- Not every session searches every source — cascade stops early when relevant context found

### LEARNINGS.md Seeding
- Format: categorized one-liners with topic sections (API Gotchas, Cron Patterns, User Preferences, etc.)
- Each entry: bullet with context + lesson, ~2-3 lines max
- Seed source: existing MEMORY.md "Lessons Learned" section + docs/ files from Phase 34
- Seed count: 15-25 entries across 4-5 categories
- Size budget: soft cap at 100 lines — when exceeded, graduate stable entries to docs/ (same pattern as MEMORY.md curation)

### Content Agent Bootstrap
- Content: role summary + key editorial/pipeline decisions + current work state. ~30-50 lines each
- Structure: shared template (Role, Editorial Decisions, Pipeline State, Working Preferences) with agent-specific content
- Location: agent workspace directory — ~/clawd/agents/{agent}/BOOTSTRAP.md
- LEARNINGS.md: shared with Bob — content agents reference the same LEARNINGS.md for operational knowledge; editorial decisions stay in per-agent BOOTSTRAP.md

### Memory Search Fallback
- Not found behavior: acknowledge gap + proceed with best judgment + log the miss to daily log
- Search depth: 3-level cascade, 7-day window (LEARNINGS.md → daily logs → docs/). After 3 levels, it's a genuine knowledge gap.
- Visibility: show when found (natural reference like "Based on our Feb 18 discussion..."), silent when empty — no narrating failed searches
- Validation: seed a MARKER test entry in LEARNINGS.md, manually test by asking Bob about it post-deploy

### Claude's Discretion
- Exact wording of Memory Protocol section in AGENTS.md
- Which categories to use in LEARNINGS.md (based on what knowledge exists)
- How to determine which cron jobs are "context-aware" vs stateless
- MARKER entry topic and phrasing

</decisions>

<specifics>
## Specific Ideas

- Memory Protocol should fit within the freed-up boot budget from Phase 34's MEMORY.md curation
- LEARNINGS.md entries should be actionable ("gateway restart clears DM sessions — user must DM first to re-establish") not vague ("be careful with restarts")
- Content agent BOOTSTRAP.md should be enough for a cold-start cron session to produce coherent output without DM history

</specifics>

<deferred>
## Deferred Ideas

- Automated MARKER retrieval test as a cron job — captured as MEM-F02 in REQUIREMENTS.md
- Per-agent LEARNINGS.md for editorial lessons — revisit if shared model proves insufficient
- 30-day daily log window — start with 7 days, expand if agents miss older context

</deferred>

---

*Phase: 35-memory-retrieval-discipline*
*Context gathered: 2026-02-23*
