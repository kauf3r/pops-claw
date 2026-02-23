# Pitfalls Research

**Domain:** Agent memory system improvements + dashboard polish for existing OpenClaw multi-agent deployment (pops-claw)
**Researched:** 2026-02-23
**Confidence:** HIGH (pitfalls derived from OpenClaw official docs, project history in MEMORY.md, v2.5 milestone audit, and direct knowledge of production system constraints)

> This file supersedes the v2.5-era PITFALLS.md which covered Mission Control Dashboard foundation pitfalls
> (SQLite BUSY, WAL starvation, OOM, hydration, schema validation, Convex removal, etc). Those pitfalls
> remain valid and are not repeated here. This file covers the NEXT milestone: memory system reliability,
> retrieval discipline, memory health monitoring, and dashboard polish for the existing deployed system.

---

## Critical Pitfalls

### Pitfall 1: MEMORY.md Curation Deletes Critical Operational Context, Breaking Agent Behavior

**What goes wrong:**
The 304-line MEMORY.md is curated down to <150 lines to reduce system prompt token usage. During curation, "old" entries like EC2 access details, sandbox architecture facts, or cron configuration gotchas are removed because they look stale. But these entries exist because Bob (or other agents) hit those problems in production and the fix was recorded to prevent recurrence. After curation, Bob forgets the `gateway.remote.url` workaround, tries to use localhost for CLI commands, and every `openclaw cron/sessions/etc` command fails with 1006 abnormal closure. Or someone removes the "gog auth add --manual is broken" entry and the next OAuth re-auth wastes 2 hours rediscovering the workaround.

**Why it happens:**
MEMORY.md serves two conflicting purposes: (1) reducing system prompt size to save tokens, and (2) preserving hard-won operational knowledge. A person curating sees 304 lines and thinks "half of this is old stuff" without understanding WHY each entry exists. The entries don't explain their own criticality -- "gateway.remote.url: ws://100.72.143.9:18789" looks like a routine config note, not a "remove this and 20 cron jobs break" fact.

**How to avoid:**
- Before removing ANY entry from MEMORY.md, verify it is truly obsolete -- not just old. Ask: "If this fact were unknown, what would break?"
- Create a classification system: tag entries as `[CRITICAL]` (removing breaks production), `[REFERENCE]` (useful but recoverable from docs), `[STALE]` (genuinely outdated)
- Curate by CONDENSING, not DELETING. "gog auth add --manual is broken (v0.9.0): context deadline exceeded. Workaround: construct OAuth URL manually..." can become "gog auth --manual broken, use manual OAuth URL + token import"
- Keep a MEMORY-ARCHIVE.md in the workspace (NOT auto-loaded) with full-text versions of condensed entries, retrievable via memory_search
- Test curation in a non-destructive way: back up current MEMORY.md, deploy curated version, monitor for 24 hours, then remove the backup

**Warning signs:**
- Agent starts asking for information that was previously in MEMORY.md
- CLI commands that were working start failing with cryptic errors
- Agent re-discovers workarounds that were already documented
- Cron jobs or briefings fail after a "routine" MEMORY.md cleanup

**Phase to address:** Phase 1 (Memory Curation) -- this is the first and highest-risk operation

---

### Pitfall 2: Memory Flush Threshold Tuning Triggers Premature Compaction, Losing Active Session Context

**What goes wrong:**
The `agents.defaults.compaction.memoryFlush` configuration controls when the agent flushes memories before context compaction. Tuning `softThresholdTokens` too aggressively (e.g., from default 4000 to 20000) causes the flush to trigger earlier in the conversation. The agent writes a memory summary to disk, then compaction truncates the conversation history. If the agent was mid-task (e.g., in the middle of a multi-step briefing), it loses the context of what it was doing. The briefing comes out incomplete or repeats sections. Worse: the memory flush uses a system prompt that instructs the agent to "store important memories," but mid-task the agent doesn't know what's important yet -- it stores partial, low-quality memories that pollute the memory index.

**Why it happens:**
The flush threshold math is: `trigger = contextWindow - reserveTokensFloor - softThresholdTokens`. For a 200K window with 20K reserve, default 4K soft threshold triggers at ~176K. Raising soft threshold to 20K triggers at 160K -- 16K tokens earlier. For long morning briefings that gather data from 7+ sources, 16K tokens is the difference between completing the briefing and getting compacted mid-way. The temptation to "flush earlier to save more memories" backfires because you're trading task completion for memory quality.

**How to avoid:**
- Do NOT change `softThresholdTokens` without first profiling actual session token usage. Run `openclaw sessions` and check token counts for the most token-intensive cron jobs (morning briefing, weekly review)
- If the morning briefing typically uses 150K tokens, a soft threshold triggering at 160K will cause premature compaction. The default 176K is safer
- If you must tune, change by small increments (2K-4K) and monitor cron job completion rates for 48 hours before adjusting further
- Use `memory.flushThreshold.enabled: false` for specific agents or cron contexts where task completion matters more than memory preservation
- Remember: only one flush per compaction cycle -- the system is designed to flush once, not continuously

**Warning signs:**
- Morning briefing or weekly review suddenly produces shorter/incomplete output
- Agent starts saying "I was in the middle of..." after compaction
- Memory index fills with partial, context-free snippets ("Section 3: Weather" with no actual weather data)
- Session token counts show compaction triggering at a lower threshold than before

**Phase to address:** Phase 2 (Flush Threshold Tuning) -- only after memory curation is stable

---

### Pitfall 3: Gateway Restart During Config Changes Kills 20 Active Cron Jobs and DM Sessions

**What goes wrong:**
Modifying `openclaw.json` for memory settings (flush thresholds, retrieval parameters, agent boot sequence changes) requires a gateway restart to take effect. The restart clears ALL active DM sessions. After restart, cron jobs that use `sessions_send` to deliver results to DM channels fail silently because the DM session no longer exists. The user must DM Bob first to re-establish the session. Meanwhile, any cron job that fires during the restart window (or in the minutes after, before DM re-establishment) produces output that goes nowhere. If the restart happens near a scheduled cron time (e.g., 6 AM morning briefing), the briefing is lost entirely.

This is a KNOWN issue documented in MEMORY.md: "Gateway restart clears DM sessions: After restart, cron `sessions_send` to DM channels fails. User must DM Bob first to re-establish."

**Why it happens:**
OpenClaw's gateway holds DM sessions in memory. Config changes require `systemctl --user restart openclaw-gateway.service` which creates a new process with no session state. The session file (`sessions.json`) is loaded on startup but DM sessions require the user to initiate first. Cron jobs don't check whether their target session exists before trying to deliver.

**How to avoid:**
- BATCH all config changes into a single restart. Do not restart for each individual change
- Schedule config-change restarts for low-activity windows (e.g., 3-4 AM UTC when no crons are scheduled)
- Check the cron schedule BEFORE restarting: `openclaw cron list` and verify no job fires in the next 15 minutes
- After restart, immediately DM Bob from Slack to re-establish the DM session
- Create a post-restart checklist: (1) verify gateway running, (2) DM Bob, (3) check `openclaw sessions` shows active session, (4) verify next cron fires successfully
- Consider implementing changes that DON'T require restart first (e.g., workspace file changes like MEMORY.md, LEARNINGS.md, boot docs) before changes that DO require restart (openclaw.json settings)

**Warning signs:**
- Morning briefing doesn't arrive after a config change the night before
- `openclaw sessions` shows empty or stale sessions after restart
- Cron run logs show "ok" status but no Slack message was delivered
- Multiple cron jobs fail in the same time window (all affected by the same restart)

**Phase to address:** ALL phases that modify openclaw.json -- but the restart strategy should be defined in Phase 1

---

### Pitfall 4: Adding Retrieval Instructions to Boot Sequence Bloats System Prompt Beyond bootstrapMaxChars

**What goes wrong:**
To improve memory retrieval discipline, instructions are added to agent workspace files (AGENTS.md, SOUL.md, or a custom boot doc) telling the agent when and how to search memory. These files are auto-loaded into the system prompt on every turn via OpenClaw's bootstrap mechanism. If the total bootstrap content exceeds `bootstrapTotalMaxChars` (default: 150,000) or individual files exceed `bootstrapMaxChars` (default: 20,000), OpenClaw truncates them using a 70/20/10 split (70% head, 20% tail, 10% truncation marker). The retrieval instructions, added at the end of an existing file, end up in the truncated 20% tail section or are cut entirely. The agent never sees them.

Even if within limits, every additional character in boot files consumes context window tokens on EVERY turn. A 2000-character retrieval instruction block costs ~500 tokens per turn. Over a 40-turn morning briefing, that's 20,000 tokens devoted to instructions the agent may not even need on most turns.

**Why it happens:**
OpenClaw auto-loads: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md. All of these together can easily exceed 100K characters for a mature deployment with 7 agents, 13 skills, and detailed memory. Adding retrieval instructions tips the balance, and the truncation is SILENT -- no error, no warning, the instructions just disappear. The agent appears to work fine but never uses the retrieval patterns because it never saw them.

**How to avoid:**
- Check current bootstrap size BEFORE adding anything: `openclaw context list` (or `/context list` in a session) to see per-file and total sizes
- MEMORY.md curation (Pitfall 1) should happen FIRST to free up bootstrap budget for retrieval instructions
- Keep retrieval instructions under 500 characters. Be terse: "Before answering questions about infrastructure, search memory for the topic. Before referencing past decisions, search memory." Not a paragraph-long instruction set
- Put retrieval instructions in AGENTS.md (which is loaded first and is the agent's primary behavior guide), not a new file. OpenClaw only auto-loads the 7 listed files -- a file called RETRIEVAL.md or BOOT.md will NOT be auto-loaded
- Verify with `openclaw context detail` that your additions survived truncation
- Consider whether retrieval instructions belong in a SKILL file instead -- skills are loaded on-demand, not on every turn

**Warning signs:**
- `openclaw context list` shows total bootstrap size near or at the cap
- Agent ignores memory retrieval instructions that you know are in a workspace file
- Adding a new boot instruction doesn't change agent behavior at all
- `/context detail` shows a file with a truncation marker

**Phase to address:** Phase 2 or 3 (Retrieval Instructions) -- but check bootstrap budget in Phase 1 during MEMORY.md curation

---

### Pitfall 5: Activating LEARNINGS.md Creates a Noise Feedback Loop That Pollutes Memory Index

**What goes wrong:**
LEARNINGS.md (or equivalent pattern where the agent writes learned patterns to a persistent file) is activated to capture operational insights. The agent starts writing to it on every session -- not just genuine learnings, but restating things it already knows, recording obvious facts ("User prefers morning briefings at 6 AM PT" -- already in MEMORY.md), and duplicating information from skill files. The file grows rapidly. Because memory files in `memory/*.md` are indexed by the builtin memory backend (sqlite-vec + FTS5), these low-quality entries pollute the semantic search results. When the agent searches memory for "briefing schedule," it gets 15 redundant hits from LEARNINGS.md instead of the one authoritative entry in MEMORY.md. Signal-to-noise ratio collapses.

**Why it happens:**
The agent doesn't have a clear definition of what constitutes a "learning" vs. a "known fact." Without explicit criteria, Claude tends to be thorough and writes everything it encounters as a potential learning. The memory flush system (which triggers before compaction) also writes memories to disk, and these can duplicate LEARNINGS.md entries. There's no deduplication in the memory index -- semantically similar chunks from different files all appear in search results.

**How to avoid:**
- Define EXPLICIT criteria for what belongs in LEARNINGS.md in the activation instructions: "Write to LEARNINGS.md ONLY when you discover something that contradicts your current understanding or that is not documented anywhere else in workspace files"
- Set a MAXIMUM size for LEARNINGS.md (e.g., 50 lines / 2000 characters) and include a curation instruction: "Before adding a new entry, check if it already exists in MEMORY.md or skill files. If it does, do not add it"
- Do NOT index LEARNINGS.md in the memory search path initially. Add it to `memory.qmd.paths` only after verifying the quality of entries over a 1-week trial period
- Review LEARNINGS.md manually after 48 hours of activation. If more than 30% of entries are duplicates or obvious facts, tighten the criteria
- Consider a "write-then-curate" pattern: agent writes freely to LEARNINGS.md, but a weekly cron curates it by removing duplicates and promoting genuine insights to MEMORY.md

**Warning signs:**
- LEARNINGS.md grows by more than 20 lines per day
- Memory search results contain multiple near-identical entries from different files
- Agent references LEARNINGS.md entries that are word-for-word copies of MEMORY.md entries
- Memory search becomes less useful (relevant results buried under noise)

**Phase to address:** Phase 3 (LEARNINGS.md Activation) -- only after memory curation and retrieval instructions are stable

---

## Moderate Pitfalls

### Pitfall 6: Memory Health Dashboard Panel Queries Memory Databases That Don't Exist for Most Agents

**What goes wrong:**
A "Memory Health" panel is added to Mission Control showing memory statistics per agent (chunk count, last indexed, search quality metrics). The panel assumes all 7 agents have memory databases. In reality, only 4 of 7 agents have memory databases with data (from MEMORY.md context). The other 3 (likely the content pipeline agents: Quill, Sage, Ezra) have no memory data because they're cron-only workers that don't maintain persistent memory. The dashboard query for these agents either errors (if the memory DB path doesn't exist) or shows misleading zeros (making it look like memory is broken when it was never configured).

**Why it happens:**
The dashboard developer assumes uniform agent configuration. But OpenClaw's multi-agent setup allows per-agent configuration -- content pipeline agents (Quill, Sage, Ezra) are stateless cron workers that receive instructions via skill files and don't accumulate memories. Their workspace directories exist but may not have memory subdirectories or SQLite memory databases.

**How to avoid:**
- Before building the panel, enumerate which agents have memory databases: SSH to EC2 and check `ls ~/clawd/agents/*/memory/` for each agent
- Design the panel to gracefully handle "no memory configured" as a valid state, not an error. Show "N/A" or "Cron-only agent (no memory)" instead of zeros or error badges
- Only query memory databases for agents that have them. Use the agent roster from MEMORY.md to categorize: heartbeat agents (have memory) vs. cron-only agents (no memory)
- If the panel needs to be uniform, show memory stats for agents WITH memory and activity stats (cron runs, last execution) for cron-only agents

**Warning signs:**
- Memory health panel shows 3 agents with "0 chunks" or "Never indexed" that aren't actually broken
- better-sqlite3 errors in Next.js logs when trying to open non-existent memory database paths
- Confusing dashboard where some agents show memory data and others show error states

**Phase to address:** Dashboard Memory Health phase -- the one that adds the panel to Mission Control

---

### Pitfall 7: Context Usage Indicators Show Misleading Percentages Due to Token Counting Ambiguity

**What goes wrong:**
The deferred Phase 31.1 (Context Usage Indicators) is implemented for the agent board. It shows "context window utilization %" per agent. But as documented in the 31.1-RESEARCH.md, `input_tokens` alone is NOT the context window usage -- actual context is `input_tokens + cache_read_tokens + cache_write_tokens`. If implemented using just `input_tokens`, every agent shows 0-1% context utilization (because `input_tokens` for cached sessions is typically 24-304 tokens while the actual context is 60K-1M). Conversely, if implemented correctly using all three token types, some agents show >100% (Haiku sessions reaching 298K on a 200K model limit). Both cases produce confusing or alarmist displays.

**Why it happens:**
Anthropic's API splits input into three fields: `input_tokens` (uncached new tokens), `cache_read_tokens` (cached prompt), and `cache_write_tokens` (newly cached). The field named "input_tokens" is counterintuitively NOT the total input. This is thoroughly documented in the 31.1 research but can be missed if that research is not consulted during implementation.

**How to avoid:**
- USE the existing 31.1-RESEARCH.md -- it has verified production data, correct formulas, and tested SQL queries
- Formula: `context_pct = (input_tokens + cache_read_tokens + cache_write_tokens) / MODEL_CONTEXT_LIMITS[model] * 100`
- Use the MODEL_CONTEXT_LIMITS map from the research: Sonnet 4.5 = 1,000,000 (1M beta), Haiku 4.5 = 200,000
- Cap the progress bar width at 100% but show the actual percentage as text (>100% is informative, not broken)
- The research explicitly warns: "Using `input_tokens` alone for context % shows near-0% for all agents"

**Warning signs:**
- All agents showing 0-1% context utilization (using input_tokens only)
- Agents showing >100% and the UI breaking (no Math.min cap)
- Context % not correlating with observable agent behavior (busy agent shows low %, idle agent shows high %)

**Phase to address:** Context Usage Indicators phase

---

### Pitfall 8: Agent Board Polish Changes Break Existing Working Components

**What goes wrong:**
Phase 31.2 (Agent Board Polish) modifies the agent card component, styling, or layout that was verified working in Phase 31. A CSS change to improve the card border radius or spacing inadvertently breaks the responsive grid layout. A refactor of the AgentCard to add new sections shifts the existing token usage or error badge placement. The existing SWR polling configuration or API route contract changes during "polish" and breaks the data flow. Because polish feels low-risk ("we're just changing CSS"), these regressions aren't caught until the next time someone loads the dashboard.

**Why it happens:**
"Polish" phases feel safe because they're cosmetic. But in a Next.js component tree, changing a parent component's layout affects all children. Tailwind classes interact in non-obvious ways (e.g., changing `space-y-3` to `space-y-4` on a card can push content below the fold on smaller viewports). The v2.5 milestone audit noted that "Human verification pending: colored left borders, hover tooltips, SWR polling, error badge colors" -- these were NEVER visually verified, so the baseline itself might have issues that polish reveals.

**How to avoid:**
- Before ANY polish changes, load the current dashboard and screenshot each page as a visual baseline
- Make polish changes one at a time, not in batches. Verify each change renders correctly before moving to the next
- Do NOT change the API route contract or SWR hook configuration during a polish phase -- if the data layer needs changes, that's a separate phase
- Test responsive behavior after CSS changes: resize the browser from desktop to mobile width
- The v2.5 audit identified specific pending verifications -- complete those FIRST before adding more changes on top

**Warning signs:**
- Agent cards suddenly different heights (broken grid layout)
- Token usage numbers or error badges not appearing where expected
- SWR polling stops working (manifests as data going stale without updating)
- Console errors about missing props or type mismatches after component refactoring

**Phase to address:** Agent Board Polish phase -- but visual baseline verification should happen in Phase 1

---

### Pitfall 9: MEMORY.md Grows Back Past Truncation Threshold After Curation

**What goes wrong:**
MEMORY.md is curated down to 148 lines (under the 150-line target). Over the following weeks, the agent or automated processes add new entries (voice note summaries, new learnings, infrastructure changes). The file grows back past 200 lines. OpenClaw's bootstrap mechanism truncates it using the 70/20/10 split (70% head, 20% tail, 10% marker). Critical entries in the middle -- between line 100 and line 160 -- are silently dropped. These might include the most recently added entries (newest context that the agent needs most). The agent's behavior degrades without any visible error or warning.

**Why it happens:**
The 200-line truncation (or `bootstrapMaxChars` truncation) happens silently at load time. There's no alert when MEMORY.md exceeds the threshold. The 70/20/10 split preserves the beginning and end of the file but cuts the middle -- which is exactly where medium-age entries (recent but not brand-new) live. These are often the most operationally relevant entries.

**How to avoid:**
- Add a monitoring check: a cron job or dashboard indicator that warns when MEMORY.md exceeds 180 lines (90% of the 200-line threshold)
- Structure MEMORY.md with the MOST CRITICAL entries at the top (within the 70% head section) and LEAST CRITICAL at the bottom
- Establish a curation cadence: review MEMORY.md weekly and prune or condense before it hits the threshold
- Move verbose entries to MEMORY-ARCHIVE.md or daily memory logs where they're accessible via memory_search but don't consume bootstrap budget
- Use `openclaw context list` periodically to verify MEMORY.md isn't being truncated

**Warning signs:**
- `openclaw context list` shows MEMORY.md with a truncation marker
- Agent behavior changes without any obvious configuration change
- New entries added to MEMORY.md "disappear" (they're in the truncated middle section)
- Agent doesn't know about recent infrastructure changes that were documented in MEMORY.md

**Phase to address:** Phase 1 (Memory Curation) for initial organization; ongoing monitoring in the Memory Health dashboard phase

---

### Pitfall 10: Extending Mission Control With New Panels While better-sqlite3 Connection Singletons Have Fixed Schema

**What goes wrong:**
A new "Memory Health" panel is added to Mission Control that needs to query memory-related SQLite databases (the builtin memory backend uses sqlite-vec + FTS5). The dashboard's `db.ts` singleton factory was built for the original 5 databases (coordination.db, observability.db, content.db, email.db, health.db). Adding memory database connections requires either modifying the singleton factory or creating a parallel connection mechanism. If the singleton is modified carelessly, existing connections may be disrupted. If the memory databases use different paths per agent (4 separate databases in `~/clawd/agents/*/memory/`), the single-database-per-name pattern doesn't fit.

**Why it happens:**
The v2.5 database layer was designed for exactly 5 known databases. The `getDb()` factory uses a `DbName` type with a fixed set of valid names and a `DB_PATHS` map with hardcoded paths. Memory databases are per-agent (not system-wide), live in different directories, and may use different SQLite extensions (sqlite-vec). The abstraction wasn't designed for this use case.

**How to avoid:**
- Extend the `DB_PATHS` map and `DbName` type to include memory databases, rather than creating a parallel system
- Use a naming convention that includes the agent ID: `memory-main`, `memory-landos`, etc.
- Memory databases might use sqlite-vec extension -- verify better-sqlite3 can open them without the extension loaded (it can read the regular tables, just can't query the vector columns)
- Do NOT try to load sqlite-vec into the dashboard's better-sqlite3 -- it's not needed for health monitoring (chunk count, last indexed date, file sizes). Avoid vector queries entirely
- Test that opening a memory database from the dashboard doesn't interfere with the agent's memory writes (same WAL + readonly pattern from v2.5)

**Warning signs:**
- TypeScript errors when adding new database names to the existing type system
- Existing dashboard panels break after modifying `db.ts`
- Memory database queries fail with "no such module: vec0" (trying to use sqlite-vec extension)
- Agent memory operations slow down after dashboard starts reading the same databases

**Phase to address:** Dashboard Memory Health phase

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip MEMORY.md backup before curation | Faster curation cycle | Deleted entries are unrecoverable; agent behavior may degrade without explanation | Never -- always `cp MEMORY.md MEMORY.md.bak` before editing |
| Change flush thresholds without profiling session tokens first | Quick "optimization" | Premature compaction breaks morning briefings and weekly reviews; degraded output quality without visible error | Never -- profile first, tune incrementally |
| Modify openclaw.json and restart during business hours | Immediate deployment | DM sessions lost, cron jobs miss delivery, morning briefing potentially lost | Only for critical security fixes; all other changes at 3-4 AM UTC |
| Add retrieval instructions as a new auto-loaded file | Clean separation of concerns | OpenClaw only auto-loads 7 specific files; a new file is ignored silently | Never -- put instructions in AGENTS.md or an existing auto-loaded file |
| Let LEARNINGS.md grow unbounded | More data captured | Memory search noise, duplicate entries, wasted bootstrap budget (if auto-loaded) | First 48 hours only as a trial; must curate after |
| Add dashboard panels that query per-agent memory DBs without caching | Simpler implementation | 4 additional DB connections per request on a 2GB RAM system; memory overhead compounds with existing 5 connections | Only if query frequency is < 1/minute; otherwise cache results |

---

## Integration Gotchas

Common mistakes when connecting these features to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| MEMORY.md curation | Curating based on age ("remove old entries") | Curate based on criticality -- old entries may be the most important (e.g., workarounds for known bugs) |
| Memory flush thresholds | Changing `softThresholdTokens` without understanding the math | Calculate: `trigger = contextWindow - reserveTokensFloor - softThresholdTokens`. Profile actual session token usage first |
| Retrieval instructions | Creating a new RETRIEVAL.md or BOOT.md file | These are NOT auto-loaded. Put instructions in AGENTS.md or SOUL.md |
| LEARNINGS.md activation | Indexing LEARNINGS.md in memory search immediately | Trial for 48 hours WITHOUT indexing. Review quality. Index only after confirming signal-to-noise ratio |
| Memory health dashboard panel | Querying memory DBs for all 7 agents | Only 4 agents have memory data. Quill/Sage/Ezra are cron-only workers with no memory |
| Context usage indicators | Using `input_tokens` column for context % | Must use `input_tokens + cache_read_tokens + cache_write_tokens`. The `input_tokens` column alone shows near-zero for all agents |
| openclaw.json changes | Restarting gateway for each individual change | Batch ALL changes, restart once, at a low-activity window (3-4 AM UTC), then DM Bob to re-establish session |
| Agent board polish | Changing CSS without visual baseline | Screenshot current state first. Make one change at a time. Verify responsive layout after each change |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| MEMORY.md growing past truncation threshold | Agent silently loses middle-section entries | Monitor line count; curate weekly; structure critical entries at top of file | When MEMORY.md exceeds ~180 lines (bootstrapMaxChars dependent) |
| LEARNINGS.md indexed without deduplication | Memory search returns 10+ near-identical results | Curate LEARNINGS.md before indexing; establish explicit criteria for what qualifies as a "learning" | After 2-3 weeks of uncurated growth (~200+ entries) |
| Memory health panel querying 4 agent memory DBs on every dashboard load | Page load time increases 200-400ms; 4 additional file handles on 2GB RAM system | Cache memory health data for 5 minutes (memory changes slowly); use route-based connection selection | When dashboard is loaded more than once per minute during active debugging |
| Flush threshold set too low, causing frequent compaction | Agent tasks interrupted mid-execution; low-quality memory snippets pollute index | Profile session token usage; set threshold with 20K+ buffer above typical session peak | During morning briefing or any cron job that uses >70% of context window |

---

## Security Mistakes

Domain-specific security issues beyond general concerns.

| Mistake | Risk | Prevention |
|---------|------|------------|
| MEMORY.md backup left in agent workspace directory | Backup file contains all operational secrets (tokens, IPs, passwords) and is accessible to the agent | Store backups outside the workspace (e.g., `~/backups/`) not in `~/clawd/agents/main/` |
| LEARNINGS.md captures sensitive information from conversations | Agent writes API keys, tokens, or passwords it encounters as "learnings" | Add explicit instruction in LEARNINGS.md criteria: "NEVER write API keys, tokens, passwords, or credentials" |
| Memory health panel exposes internal paths in API responses | Dashboard API returns absolute filesystem paths to memory databases | Return only metadata (chunk count, last indexed, file size), never paths. Keep paths server-side only |

---

## UX Pitfalls

Common user experience mistakes for memory health monitoring.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Memory health panel shows raw chunk counts without context | "247 chunks" means nothing -- is that good or bad? | Show relative health: "247 chunks (healthy)" with threshold coloring, or trend arrows showing growth/decline |
| Context usage indicator shows >100% without explanation | User thinks the system is broken or overloaded | Cap progress bar at 100%; show actual percentage as text with a tooltip: "298K / 200K -- session exceeds standard window using extended context" |
| MEMORY.md line count not visible anywhere | User doesn't know they're approaching the truncation threshold until agent behavior degrades | Add a "MEMORY.md: 148/200 lines" indicator to the memory health panel |
| Memory search quality not observable | No way to tell if memory search is returning relevant results or noise | Include a "last 5 memory searches" log with query and result count in the memory health panel |
| Agent board polish removes information density | "Prettier" cards with more whitespace show less data per screen | Prioritize information density over aesthetics for a single-user operational dashboard. Every pixel should earn its space |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **MEMORY.md curation:** File is under 150 lines AND backup exists AND critical entries verified present AND file structure has most-critical entries at top AND MEMORY-ARCHIVE.md created for full-text versions
- [ ] **Flush threshold tuning:** Setting changed AND actual session token profiles gathered AND morning briefing runs to completion AND weekly review runs to completion AND no quality degradation for 48 hours
- [ ] **Retrieval instructions:** Instructions added AND `openclaw context list` confirms they're not truncated AND agent actually uses memory search when prompted AND instructions are in an auto-loaded file (not a custom filename)
- [ ] **LEARNINGS.md activation:** Criteria defined AND file size limit established AND 48-hour trial period completed AND entry quality reviewed AND duplicates identified AND decision made on whether to index in memory search
- [ ] **Memory health dashboard:** Shows correct data for agents WITH memory AND shows appropriate "N/A" for cron-only agents AND doesn't create empty DB files AND cached appropriately AND MEMORY.md line count visible
- [ ] **Context usage indicators:** Uses all three token fields (not just input_tokens) AND model context limits correct (Sonnet 1M, Haiku 200K) AND progress bar capped at 100% width AND text shows actual percentage AND handles zero-data agents
- [ ] **Agent board polish:** Visual baseline screenshots taken BEFORE changes AND responsive layout verified AND SWR polling still working AND existing API route contract unchanged AND all 7 agents rendering correctly
- [ ] **Gateway restart management:** All openclaw.json changes batched AND restart scheduled for low-activity window AND DM session re-established after restart AND next cron job verified to fire and deliver

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| MEMORY.md curation deleted critical entries | LOW (if backup exists) / HIGH (if no backup) | Restore from `MEMORY.md.bak`. If no backup, reconstruct from MEMORY-ARCHIVE.md or git history of this planning repo. Check `findings.md` and `progress.md` for historical decisions |
| Flush threshold causes premature compaction | LOW | Reset `softThresholdTokens` to default (4000). Restart gateway during low-activity window. Re-run any affected cron jobs manually |
| Gateway restart killed DM sessions mid-briefing | MEDIUM | Restart gateway. DM Bob from Slack. Wait for next scheduled cron to verify delivery. Manually trigger missed briefing: `openclaw agent --agent main --message "Run morning briefing"` |
| Retrieval instructions silently truncated | LOW | Check `openclaw context list`. Condense instructions to fit within bootstrap budget. Move verbose instructions to a skill file instead of boot files |
| LEARNINGS.md noise pollutes memory search | MEDIUM | Clear LEARNINGS.md. Re-index memory: `openclaw memory index --agent main --force`. Review and curate before re-enabling |
| Memory health panel breaks existing dashboard | LOW | Revert the new panel component changes. The existing dashboard panels are independent; removing the new panel restores prior state |
| Agent board polish breaks card layout | LOW | Revert CSS changes (git stash/checkout). Take visual baseline screenshots before attempting polish again |
| Context indicators show wrong percentages | LOW | Check the SQL query: verify it sums `input_tokens + cache_read_tokens + cache_write_tokens`. Verify MODEL_CONTEXT_LIMITS has correct values. Fix formula, redeploy |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| MEMORY.md curation deletes critical context (Pitfall 1) | Memory Curation phase | Backup exists; critical entries verified present after curation; agent behavior unchanged for 24 hours |
| Flush threshold triggers premature compaction (Pitfall 2) | Flush Threshold Tuning phase | Morning briefing and weekly review complete successfully; session token profiles documented |
| Gateway restart kills sessions/crons (Pitfall 3) | All phases with openclaw.json changes | Restart checklist followed; DM session re-established; next cron fires successfully |
| Retrieval instructions truncated by bootstrap (Pitfall 4) | Retrieval Instructions phase | `openclaw context list` shows no truncation; agent uses memory search when expected |
| LEARNINGS.md noise feedback loop (Pitfall 5) | LEARNINGS.md Activation phase | Entry count reviewed after 48 hours; <30% duplicates; explicit criteria documented |
| Memory health panel queries non-existent DBs (Pitfall 6) | Dashboard Memory Health phase | Panel shows "N/A" for cron-only agents; no better-sqlite3 errors in logs |
| Context indicators show wrong percentages (Pitfall 7) | Context Usage Indicators phase | Query uses all 3 token fields; MODEL_CONTEXT_LIMITS correct; progress bar caps at 100% |
| Agent board polish breaks working components (Pitfall 8) | Agent Board Polish phase | Visual baseline taken before changes; responsive layout verified; SWR polling confirmed working |
| MEMORY.md grows past truncation threshold (Pitfall 9) | Memory Curation + Dashboard phases | MEMORY.md line count indicator in dashboard; weekly curation cadence established |
| New dashboard panels break db.ts singletons (Pitfall 10) | Dashboard Memory Health phase | Existing panels still working; new DbName types added correctly; memory DB opened readonly |

---

## Sources

- [OpenClaw Memory Documentation](https://docs.openclaw.ai/concepts/memory) -- memory architecture, daily logs, MEMORY.md curation, memory search (HIGH confidence)
- [OpenClaw System Prompt Documentation](https://docs.openclaw.ai/concepts/system-prompt) -- bootstrap files, auto-loaded files, bootstrapMaxChars, truncation behavior (HIGH confidence)
- [OpenClaw Agent Workspace Documentation](https://docs.openclaw.ai/concepts/agent-workspace) -- workspace structure, writable paths, sandbox constraints (HIGH confidence)
- [OpenClaw Troubleshooting](https://docs.openclaw.ai/gateway/troubleshooting) -- gateway restart behavior, session management (HIGH confidence)
- [OpenClaw Memory Configuration Guide](https://moltfounders.com/openclaw-runbook/memory-configuration) -- flush thresholds, compaction settings, softThresholdTokens math (MEDIUM confidence)
- [OpenClaw Memory Explained](https://lumadock.com/tutorials/openclaw-memory-explained) -- bootstrapMaxChars 70/20/10 split, daily log vs MEMORY.md distinction (MEDIUM confidence)
- [OpenClaw Production Gotchas](https://kaxo.io/insights/openclaw-production-gotchas/) -- config drift, cron stale models, gateway restart issues (MEDIUM confidence)
- [OpenClaw Memory Is Broken](https://blog.dailydoseofds.com/p/openclaws-memory-is-broken-heres) -- MEMORY.md bloat, curation strategies (MEDIUM confidence)
- [Pre-compaction memory flush bug #5457](https://github.com/openclaw/openclaw/issues/5457) -- flush uses stale token counts, can be bypassed (MEDIUM confidence)
- [Context overflow error #5771](https://github.com/openclaw/openclaw/issues/5771) -- bootstrap size management (MEDIUM confidence)
- [Gateway config wiped on restart #12857](https://github.com/openclaw/openclaw/issues/12857) -- config persistence concerns (MEDIUM confidence)
- [LLM Context Window Overflow](https://redis.io/blog/context-window-overflow/) -- silent information loss, model reliability degradation (MEDIUM confidence)
- [Memory Blocks for Context Management](https://www.letta.com/blog/memory-blocks) -- structured memory abstraction patterns (MEDIUM confidence)
- Phase 31.1 RESEARCH.md (project internal) -- context usage indicator formulas, token field semantics, MODEL_CONTEXT_LIMITS, production data profiles (HIGH confidence)
- Phase 31 RESEARCH.md (project internal) -- agent board architecture, query patterns, agent ID inconsistency (HIGH confidence)
- v2.5 MILESTONE-AUDIT.md (project internal) -- deferred phases 31.1/31.2, tech debt items, pending human verification (HIGH confidence)
- Project MEMORY.md (project internal) -- EC2 constraints, gateway restart behavior, DM session loss, known workarounds (HIGH confidence)

---
*Pitfalls research for: pops-claw agent memory improvements + dashboard polish*
*Researched: 2026-02-23*
