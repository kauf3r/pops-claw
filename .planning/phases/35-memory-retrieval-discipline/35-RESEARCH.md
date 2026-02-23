# Phase 35: Memory Retrieval Discipline - Research

**Researched:** 2026-02-23
**Domain:** Agent memory architecture (OpenClaw workspace files, AGENTS.md boot sequence, cron session context)
**Confidence:** HIGH

## Summary

This phase adds retrieval discipline to the OpenClaw agent memory system. Currently, agents have a *write* path (daily logs via memory flush, MEMORY.md for long-term), but no explicit *read* path -- there are no instructions telling agents to search their prior knowledge before starting tasks. Content agents (Quill, Sage, Ezra) have an even bigger gap: they run in isolated cron sessions with zero prior context, producing output disconnected from previous sessions.

The implementation surface is entirely workspace markdown files on EC2. There are no code changes, no database schema changes, no config file changes. Everything is SSH + file writes to `~/clawd/agents/` directories.

**Primary recommendation:** Add a Memory Protocol section to the global `~/clawd/AGENTS.md`, create and seed `~/clawd/agents/main/LEARNINGS.md` from existing operational knowledge in MEMORY.md and daily logs, and create per-agent `BOOTSTRAP.md` files for Quill, Sage, and Ezra with role/pipeline/state context.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Search triggers: session start + context keywords (references to past work, "follow up on", "what happened with", "last time")
- Cron jobs: only context-aware crons search memory (flagged in config); stateless crons skip
- Format: short "Memory Protocol" section in AGENTS.md -- 3-4 bullet points, not a full procedure doc
- Search order: prioritized cascade -- LEARNINGS.md first, daily logs (7 days), docs/ directory. Stop when context found.
- Not every session searches every source -- cascade stops early when relevant context found
- LEARNINGS.md format: categorized one-liners with topic sections (API Gotchas, Cron Patterns, User Preferences, etc.)
- Each entry: bullet with context + lesson, ~2-3 lines max
- Seed source: existing MEMORY.md "Lessons Learned" section + docs/ files from Phase 34
- Seed count: 15-25 entries across 4-5 categories
- Size budget: soft cap at 100 lines -- when exceeded, graduate stable entries to docs/ (same pattern as MEMORY.md curation)
- Content agent BOOTSTRAP.md content: role summary + key editorial/pipeline decisions + current work state. ~30-50 lines each
- Structure: shared template (Role, Editorial Decisions, Pipeline State, Working Preferences) with agent-specific content
- Location: agent workspace directory -- ~/clawd/agents/{agent}/BOOTSTRAP.md
- Content agents reference shared LEARNINGS.md for operational knowledge; editorial decisions stay in per-agent BOOTSTRAP.md
- Not found behavior: acknowledge gap + proceed with best judgment + log the miss to daily log
- Search depth: 3-level cascade, 7-day window
- Visibility: show when found (natural reference), silent when empty -- no narrating failed searches
- Validation: seed a MARKER test entry in LEARNINGS.md, manually test by asking Bob about it post-deploy

### Claude's Discretion
- Exact wording of Memory Protocol section in AGENTS.md
- Which categories to use in LEARNINGS.md (based on what knowledge exists)
- How to determine which cron jobs are "context-aware" vs stateless
- MARKER entry topic and phrasing

### Deferred Ideas (OUT OF SCOPE)
- Automated MARKER retrieval test as a cron job -- captured as MEM-F02 in REQUIREMENTS.md
- Per-agent LEARNINGS.md for editorial lessons -- revisit if shared model proves insufficient
- 30-day daily log window -- start with 7 days, expand if agents miss older context
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MEM-03 | AGENTS.md boot sequence includes explicit retrieval instructions (search daily logs and LEARNINGS.md before tasks) | Memory Protocol section added to global ~/clawd/AGENTS.md. Architecture findings show the global AGENTS.md (191 lines) is loaded by all agents; Bob's per-agent override (12 lines) adds Operator Mindset on top. |
| MEM-04 | LEARNINGS.md activated with seeded entries from existing operational knowledge (not empty framework) | 15-25 entries extracted from project MEMORY.md Lessons Learned, daily logs (Feb 2-22), and docs/ reference files. Categories derived from actual knowledge: API/Auth Gotchas, Cron Patterns, Content Pipeline, Infrastructure, User Preferences. |
| MEM-05 | Content agents (Quill, Sage, Ezra) have bootstrap memory files so they retain context across cron sessions | Per-agent BOOTSTRAP.md files at ~/clawd/agents/{quill,sage,ezra}/. Quill already has BOOTSTRAP.md (but it's the generic "Hello World" template -- needs replacement). Sage has no AGENTS.md or BOOTSTRAP.md. Ezra has no AGENTS.md or BOOTSTRAP.md. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Purpose | Why Standard |
|------|---------|--------------|
| SSH + file writes | All changes are markdown files on EC2 | No code, no packages -- pure workspace configuration |
| Global AGENTS.md | `~/clawd/AGENTS.md` -- boot instructions loaded by all agents | OpenClaw convention: global AGENTS.md + per-agent override |
| LEARNINGS.md | `~/clawd/agents/main/LEARNINGS.md` -- curated operational knowledge | New file, referenced in Memory Protocol cascade |
| Per-agent BOOTSTRAP.md | `~/clawd/agents/{agent}/BOOTSTRAP.md` -- cold-start context | OpenClaw convention: BOOTSTRAP.md provides session context |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| docs/ reference files | `~/clawd/docs/*.md` -- 8 reference docs from Phase 34 | Third tier in memory search cascade |
| Daily logs | `~/clawd/agents/main/memory/YYYY-MM-DD.md` | Second tier in cascade; 7-day window |
| DAILY_FLUSH.md | Reference doc for memory flush cron | Already exists; no changes needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| File-based cascade | SQLite FTS5 search | Overkill for current scale; deferred to MEM-F01 |
| Shared LEARNINGS.md | Per-agent LEARNINGS.md | More maintenance; shared is simpler for 7 agents |
| Memory Protocol in each agent's AGENTS.md | Memory Protocol in global AGENTS.md | Global = single edit, all agents inherit |

## Architecture Patterns

### File Layout (Current vs Target)

**Current state:**
```
~/clawd/
├── AGENTS.md                          # 191 lines (global, loaded by all agents)
├── docs/                              # 8 reference docs from Phase 34
│   ├── CA66_GENERATOR.md
│   ├── CANVA.md
│   ├── CLAUDE_LIFE_OS.md
│   ├── INSIGHT_UP.md
│   ├── NEGOTIATION.md
│   ├── READICCULUS.md
│   ├── SAFETY_DOC_GEN.md
│   └── VOICE_MEMORY_APP.md
├── agents/
│   ├── main/
│   │   ├── AGENTS.md                  # 12 lines (Operator Mindset override)
│   │   ├── MEMORY.md                  # DELETED (Phase 34 curated to project MEMORY.md)
│   │   ├── DAILY_FLUSH.md             # Memory flush reference doc
│   │   └── memory/                    # 9 daily logs (Feb 2-22)
│   ├── quill/
│   │   ├── AGENTS.md                  # 212 lines (full default copy)
│   │   ├── BOOTSTRAP.md               # Generic "Hello World" template (NOT useful)
│   │   ├── WRITING_SESSION.md         # Cron session instructions
│   │   └── PRODUCT_CONTEXT.md         # UAS domain rules
│   ├── sage/
│   │   ├── PRODUCT_CONTEXT.md         # UAS domain rules (same as Quill)
│   │   └── REVIEW_SESSION.md          # Cron session instructions
│   ├── ezra/
│   │   ├── PRODUCT_CONTEXT.md         # UAS domain rules (same as Quill)
│   │   └── PUBLISH_SESSION.md         # Cron session instructions
│   ├── rangeos/ (Vector)              # 191 lines AGENTS.md, TOPIC_RESEARCH.md
│   ├── ops/ (Sentinel)               # 191 lines AGENTS.md, MEMORY.md, STANDUP.md
│   └── landos/ (Scout)               # 191 lines AGENTS.md, IDENTITY.md
```

**Target state (changes only):**
```
~/clawd/
├── AGENTS.md                          # +10-15 lines: Memory Protocol section added
├── agents/
│   ├── main/
│   │   └── LEARNINGS.md               # NEW: 15-25 seeded entries (~80-100 lines)
│   ├── quill/
│   │   └── BOOTSTRAP.md               # REPLACED: pipeline-specific context (~30-50 lines)
│   ├── sage/
│   │   └── BOOTSTRAP.md               # NEW: editorial review context (~30-50 lines)
│   └── ezra/
│       └── BOOTSTRAP.md               # NEW: publishing context (~30-50 lines)
```

### Pattern 1: Memory Protocol in AGENTS.md

**What:** A short "Memory Protocol" section inserted into the global AGENTS.md, in the "Every Session" area, between the current boot sequence and the Memory section.

**When to use:** All agent sessions -- the cascade is cheap (check LEARNINGS.md first, stop if context found).

**Key design decision:** The global `~/clawd/AGENTS.md` is the right place, NOT per-agent AGENTS.md files. Reason: Bob's per-agent AGENTS.md (12 lines) is a minimal override. Quill/rangeos/ops/landos each have a full 191-212 line copy of the global template. Adding to global means all agents get it automatically without editing 5+ files.

**Placement:** After the "Every Session" numbered list (read SOUL.md, USER.md, memory, MEMORY.md), add a "Memory Protocol" subsection. This way it's part of the boot sequence, read before any task execution.

**Wording guidance (3-4 bullets):**
1. Before starting a task, check LEARNINGS.md for relevant operational knowledge
2. If task references past work ("follow up on", "what happened with", "last time"), search daily logs (last 7 days) for context
3. If not found in LEARNINGS or logs, check docs/ directory for reference docs
4. Stop searching when relevant context found -- cascade, don't exhaustively read everything

### Pattern 2: LEARNINGS.md Seeding

**What:** A categorized knowledge base of operational lessons, seeded from existing sources.

**Source material available on EC2:**
- Project MEMORY.md (local copy in this repo) -- "Lessons Learned" section has 12+ entries
- Daily logs: 9 files (Feb 2-22, ~250 lines total) with embedded lessons
- docs/ directory: 8 reference files with project-specific knowledge

**Category candidates (based on actual content):**
1. **API & Auth Gotchas** -- gog token corruption, OAuth test users, manual auth workaround, keyring issues
2. **Cron Patterns** -- isolated vs main session types, system-event vs message payloads, DM re-establish after restart
3. **Infrastructure** -- gateway tailnet bind + remote URL, sshd socket-activation, cloud-boothook timing, OOM recovery
4. **Content Pipeline** -- CP-05 locking protocol, content.db path, wp_post_id column, review requires actual body text
5. **User Preferences** -- Andy's communication style, verbal > visual, concise, externalize decisions

**Seed count target:** 15-25 entries across these 5 categories.

### Pattern 3: Content Agent BOOTSTRAP.md

**What:** Per-agent context files that give cron-triggered sessions enough background to produce coherent output without DM history.

**Template structure:**
```markdown
# {Agent Name} - Bootstrap Context

## Role
{1-2 sentences: what this agent does in the content pipeline}

## Editorial Decisions
{3-5 bullet points: standing decisions about content/style/process}

## Pipeline State
{Current status: what's in progress, what's blocked, recent activity}

## Working Preferences
{2-3 bullets: how this agent operates, what to prioritize}
```

**Agent-specific content:**

**Quill (writer):**
- Role: SEO content writer for AirSpace Integration UAS content
- Editorial: PRODUCT_CONTEXT.md compliance, 1500-2500 word target, keyword density rules
- State: Current topics in writing queue, recent articles produced
- Preferences: Check for in-progress topics before claiming new ones, avoid similar topics back-to-back

**Sage (editor):**
- Role: Editorial reviewer scoring SEO/readability/accuracy
- Editorial: Scores >= 7 threshold, PRODUCT_CONTEXT.md as the compliance baseline
- State: Articles awaiting review, recent approval/revision decisions
- Preferences: Verify claims via browser search when possible, document unverifiable claims

**Ezra (publisher):**
- Role: WordPress publisher + social media copy generator
- Editorial: Draft-only publishing (human approves in WP admin), social copy for LinkedIn/X/Instagram
- State: Articles approved and awaiting WP draft, recently published articles
- Preferences: Process up to 3 articles per session, check for human-published articles to confirm

**Critical finding:** Quill's current BOOTSTRAP.md is the generic "Hello World" onboarding template ("You just woke up. Time to figure out who you are."). This MUST be replaced entirely with pipeline-specific context. It's not useful for a cron-triggered writing session.

### Pattern 4: Context-Aware vs Stateless Cron Classification

**What:** Determining which cron jobs benefit from memory search and which should skip it.

**Current cron inventory (22 jobs):**

| Job | Agent | Session | Context-Aware? | Rationale |
|-----|-------|---------|----------------|-----------|
| morning-briefing | main | default | YES | References user's schedule, priorities, recent activity |
| evening-recap | main | default | YES | Summarizes day, references ongoing work |
| weekly-review | main | default | YES | Needs multi-day context |
| daily-memory-flush | main | isolated | NO | Writes memory, doesn't read prior context |
| daily-standup | ops | ops | YES | Reports on pipeline state, needs recent history |
| meeting-prep-scan | main | main | YES | Needs calendar context and recent decisions |
| airspace-email-monitor | main | isolated | NO | Stateless email check |
| email-catchup | main | isolated | NO | Stateless email poll |
| voice-notes-processor | main | isolated | NO | Stateless file processing |
| anomaly-check | main | main | NO | Stateless metric check |
| writing-check | quill | default | YES | Needs pipeline context, in-progress work |
| review-check | sage | default | YES | Needs pipeline context, review history |
| publish-check | ezra | default | YES | Needs pipeline context, approved articles |
| topic-research | rangeos | rangeos | YES | Needs backlog context, recent topics |
| stuck-check | ops | default | YES | Needs pipeline history to detect stuck items |
| pipeline-report | ops | default | YES | Needs full pipeline view |
| monthly-expense-summary | main | isolated | NO | Stateless data aggregation |
| heartbeat-* (5 jobs) | various | various | NO | Heartbeats have own protocol in AGENTS.md |

**Heuristic for classification:** A cron job is context-aware if its output quality improves by knowing what happened in prior sessions. Stateless jobs process inputs without needing history.

**Implementation note:** The Memory Protocol in AGENTS.md doesn't need per-cron configuration. The cascade is designed to be cheap (check LEARNINGS.md first ~100 lines). Context-aware crons benefit because they'll find relevant entries. Stateless crons will hit LEARNINGS.md, find nothing relevant, and stop -- minimal overhead.

### Anti-Patterns to Avoid
- **Overloading the boot sequence:** The Memory Protocol should be 3-4 bullets, not a detailed procedure. AGENTS.md is already ~200 lines; adding more than 15 lines defeats the Phase 34 token budget win.
- **Empty templates:** Quill's current BOOTSTRAP.md is a generic "Hello World" template. Creating BOOTSTRAP.md for Sage/Ezra with empty sections (```## Pipeline State\n[TODO]```) would be equally useless. Every field must have actual content.
- **Duplicating PRODUCT_CONTEXT.md:** BOOTSTRAP.md should reference PRODUCT_CONTEXT.md, not copy its content. The UAS domain rules are already 80+ lines in PRODUCT_CONTEXT.md.
- **Exhaustive memory searches:** The cascade design (LEARNINGS -> daily logs -> docs/) with early stop is critical. Without early stop, every session would read hundreds of lines of irrelevant context.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Memory search | Custom search script or database | Prioritized file cascade with early stop | Files are small (<100 lines each); full-text search is overkill at this scale |
| LEARNINGS.md categories | Complex taxonomy | 4-5 simple topic headers | Low entry count (15-25); complexity slows curation |
| Cron awareness flagging | Per-cron config field | Implicit via AGENTS.md cascade | The cascade is cheap enough that explicit flags add config complexity without meaningful savings |

**Key insight:** At the current scale (~25 learnings entries, ~10 daily logs, ~8 reference docs), a simple file cascade is the right architecture. Indexing or search infrastructure (MEM-F01) is premature until agents demonstrate they can't find what they need via cascade.

## Common Pitfalls

### Pitfall 1: Token Budget Regression
**What goes wrong:** Adding a Memory Protocol section and LEARNINGS.md auto-load bloats the boot sequence, negating Phase 34's token savings.
**Why it happens:** Phase 34 cut MEMORY.md from 304 to 91 lines (25% input token reduction). Adding 100+ lines of LEARNINGS.md at boot would erase that win.
**How to avoid:** LEARNINGS.md should be checked on-demand during the cascade, not auto-loaded at boot. Memory Protocol bullets instruct the agent to *search when relevant*, not to read everything every session.
**Warning signs:** If input tokens increase after this phase, the instructions are too eager.

### Pitfall 2: Stale BOOTSTRAP.md Content
**What goes wrong:** Pipeline state in BOOTSTRAP.md becomes outdated, causing agents to reference articles/topics that no longer exist.
**Why it happens:** BOOTSTRAP.md is a static file. Pipeline state changes daily (articles move through stages).
**How to avoid:** BOOTSTRAP.md should document *how to check* current state (SQL queries to run) rather than embedding specific article IDs/titles. Include the query patterns from WRITING_SESSION.md, REVIEW_SESSION.md, and PUBLISH_SESSION.md.
**Warning signs:** Agent references article by ID that no longer exists in that status.

### Pitfall 3: Cascade Never Stops
**What goes wrong:** Agent reads LEARNINGS.md, then all 7 daily logs, then all 8 docs/ files on every task.
**Why it happens:** "Search for context" without clear stop conditions.
**How to avoid:** Memory Protocol must say "stop when relevant context found." The cascade is: LEARNINGS.md (always fast, ~100 lines) -> daily logs (only if task references past work) -> docs/ (only if not found elsewhere).
**Warning signs:** Session token usage spikes, agent narrates "I checked X, Y, Z and found nothing."

### Pitfall 4: MARKER Entry Too Obvious
**What goes wrong:** MARKER entry is so distinctive that the agent retrieves it via pattern matching rather than genuine memory search, giving false confidence.
**Why it happens:** Test entries like "MARKER-TEST-12345: This is a test" are trivially unique.
**How to avoid:** MARKER should be a realistic-looking operational lesson. Example: a specific API behavior or configuration gotcha that would naturally be referenced if relevant.
**Warning signs:** Bob retrieves MARKER instantly but fails to find real operational knowledge from neighboring entries.

### Pitfall 5: Content Agent BOOTSTRAP.md Without Session Docs
**What goes wrong:** BOOTSTRAP.md provides context but not workflow. Agent knows its role but not what to do in a cron session.
**Why it happens:** BOOTSTRAP.md and *_SESSION.md serve different purposes but must work together.
**How to avoid:** BOOTSTRAP.md says "who you are and what you know." SESSION.md says "what to do right now." BOOTSTRAP.md should reference the session doc: "For your workflow, follow WRITING_SESSION.md."
**Warning signs:** Agent reads BOOTSTRAP.md but then improvises a workflow instead of following SESSION.md.

## Code Examples

### Example 1: Memory Protocol Section for AGENTS.md

```markdown
## Memory Protocol

Before starting a task:
- Check `LEARNINGS.md` for relevant operational knowledge (quick scan — it's short)
- If the task references past work ("follow up on", "what happened with", "last time"), scan recent daily logs (`memory/` last 7 days)
- If still missing context, check `docs/` directory for reference docs
- Stop when you find what you need — don't read everything every time
- If nothing found: proceed with best judgment and note the gap in today's daily log
```

### Example 2: LEARNINGS.md Structure

```markdown
# Operational Learnings

## API & Auth Gotchas
- **gog token corruption**: Tokens can corrupt during major version migration — remove and re-auth with `--manual`. If `--manual` hits "context deadline exceeded", construct OAuth URL manually and use `gog auth tokens import`.
- **GCP OAuth test users**: Must add email as test user in GCP Console AND may need to whitelist in Workspace Admin > Security > API Controls.
- **Gateway restart clears DM sessions**: After gateway restart, cron `sessions_send` to DM channels fails silently. User must DM Bob first to re-establish the session.

## Cron Patterns
- **Session type matters**: Jobs needing host access (gog, SSH, local files) must use `main` session with `--system-event`. Isolated sessions run in Docker sandbox without host config.
- **gateway.remote.url required**: Tailnet bind means CLI can't use default localhost. Without `gateway.remote: {url: "ws://100.72.143.9:18789"}`, all `openclaw cron/sessions/etc` commands fail with 1006 abnormal closure.

## Infrastructure
- **sshd is socket-activated**: Do NOT create socket override conf — it breaks startup. ListenAddress goes in sshd_config.
- **OOM recovery**: CloudShell -> SSM role -> open SG -> SSH via public IP. 2GB swap at /swapfile prevents recurrence.
- **cloud-boothook runs before services**: `systemctl restart ssh` in boothook fails silently. Config changes (sed) take effect when service starts later.

## Content Pipeline
- **CP-05 locking**: Always use BEGIN IMMEDIATE for topic/article claims. Check claimed_by IS NULL in both SELECT and UPDATE WHERE clause.
- **Review requires article body**: Articles with empty body/content fields cannot be reviewed for accuracy. Flag and skip.

## User Preferences
- **Communication style**: Andy prefers concise, verbal explanations over diagrams. Lead with possibilities, not constraints. Externalize all decisions to files.
```

### Example 3: Content Agent BOOTSTRAP.md Template

```markdown
# {Name} - Bootstrap Context

## Role
{1-2 sentence role description in the content pipeline}

## Editorial Decisions
- Content domain: UAS/commercial drones (see PRODUCT_CONTEXT.md for full rules)
- {3-4 agent-specific editorial standing decisions}

## Pipeline State
Check current state at session start:
```sql
{Primary query this agent runs to see what needs doing}
```

## Working Preferences
- {How this agent operates}
- {What to prioritize}
- For full workflow, follow {WRITING_SESSION.md | REVIEW_SESSION.md | PUBLISH_SESSION.md}
```

### Example 4: MARKER Test Entry

```markdown
## Infrastructure
- **Tailscale DNS on EC2**: If `tailscale status` shows "offline" but the instance is running, try `sudo systemctl restart tailscaled` first. If that fails, EC2 stop/start forces a fresh network stack (reboot alone is insufficient).
```

This is a real operational lesson (from existing MEMORY.md knowledge), phrased naturally. Testing: ask Bob "What should I try if Tailscale shows offline on the EC2?" and verify he references this LEARNINGS.md entry.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No retrieval instructions | Agents write memory but never explicitly read it back | v2.0-v2.5 | Memory exists but isn't systematically used |
| Generic BOOTSTRAP.md | "Hello World" template designed for first-time setup | v2.0 | Useless for cron-triggered sessions that already have identity |
| MEMORY.md as monolith | MEMORY.md curated to 91 lines, reference docs in docs/ | Phase 34 (v2.6) | Freed boot budget for retrieval instructions |

## Open Questions

1. **How does OpenClaw load AGENTS.md for cron sessions?**
   - What we know: The global `~/clawd/AGENTS.md` is loaded for all agents. Per-agent AGENTS.md overrides exist.
   - What's unclear: For isolated cron sessions (Docker sandbox), does the agent see the global AGENTS.md? The sandbox mounts `/home/ubuntu/clawd/agents/{agent}/` as `/workspace/` -- but the global AGENTS.md is at `/home/ubuntu/clawd/AGENTS.md`, one level up.
   - Recommendation: Verify via SSH that the sandbox can access the global AGENTS.md. If not, the Memory Protocol section needs to go in per-agent AGENTS.md files instead (more maintenance but guaranteed visibility). **This is the highest-priority open question.**

2. **Should LEARNINGS.md be in Bob's workspace or the global workspace?**
   - What we know: User decision says "shared with Bob -- content agents reference the same LEARNINGS.md." Bob's workspace is `~/clawd/agents/main/`. Global workspace is `~/clawd/`.
   - What's unclear: If content agents (quill/sage/ezra) run in sandboxed sessions, they see their own workspace, not Bob's. The shared LEARNINGS.md might need to be at `~/clawd/LEARNINGS.md` (global) for all agents to access it.
   - Recommendation: Place at `~/clawd/LEARNINGS.md` (global workspace root, alongside global AGENTS.md) so all agents inherit it. If sandbox isolation prevents this, bind-mount it.

3. **Do Sage and Ezra need their own AGENTS.md?**
   - What we know: Sage has no AGENTS.md (only PRODUCT_CONTEXT.md + REVIEW_SESSION.md). Ezra has no AGENTS.md (only PRODUCT_CONTEXT.md + PUBLISH_SESSION.md). Both presumably inherit the global AGENTS.md.
   - What's unclear: Without per-agent AGENTS.md, do they see the Memory Protocol and boot sequence from the global file?
   - Recommendation: Verify by checking if the cron sessions for sage/ezra load the global AGENTS.md. If yes, no per-agent file needed. If no, create minimal per-agent AGENTS.md with Memory Protocol.

## Sources

### Primary (HIGH confidence)
- EC2 live inspection via SSH -- verified all file paths, sizes, contents (2026-02-23)
- `openclaw cron list` -- verified all 22 cron jobs, agents, session types
- `openclaw.json` -- verified agent definitions, workspace paths, compaction config
- Global `~/clawd/AGENTS.md` (191 lines) -- verified content and boot sequence structure
- Per-agent AGENTS.md files -- verified line counts and content for main (12), quill (212), rangeos (191), ops (191), landos (191)

### Secondary (MEDIUM confidence)
- OpenClaw agent bootstrap behavior (AGENTS.md loading, BOOTSTRAP.md handling) -- inferred from file structure and AGENTS.md comments, not from official OpenClaw docs
- Sandbox file visibility -- inferred from bind-mount config in openclaw.json, not directly tested

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all files verified on EC2, architecture well understood
- Architecture: HIGH -- file layout, agent config, cron inventory all confirmed via SSH
- Pitfalls: HIGH -- token budget regression and stale content are real risks observed in prior phases
- Open questions: MEDIUM -- sandbox visibility for global AGENTS.md and LEARNINGS.md needs verification

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (stable -- workspace files, not fast-moving dependencies)
