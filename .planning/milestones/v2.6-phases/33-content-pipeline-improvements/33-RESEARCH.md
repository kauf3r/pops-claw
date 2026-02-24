# Phase 33: Content Pipeline Improvements - Research

**Researched:** 2026-02-23
**Domain:** OpenClaw content pipeline (agents, crons, SQLite, Mission Control)
**Confidence:** HIGH

## Summary

The content pipeline infrastructure is **mostly working** but has several concrete issues preventing it from being production-reliable. The live investigation reveals: (1) the content.db bind-mount is correctly configured at `~/clawd/content.db` and all agents access the same file via Docker overlay binds, (2) all five content cron jobs ARE firing and producing output, but Slack notifications consistently fail with "channel id" or "target" errors, (3) there are 21 topics and 14 articles in the pipeline with real data flowing, and (4) the Mission Control analytics pipeline chart uses status values (`researched`, `written`, `reviewed`, `published`) that do NOT match the actual DB statuses (`backlog`, `writing`, `review`, `approved`, `published`, `draft`, `revision`, `done`, `completed`).

The on-demand content triggers (CP-03, CP-04) require new capability -- either new skills that Bob delegates to content agents, or DM-based commands that insert topics/trigger agent sessions. The simplest approach is adding Bob DM commands that (a) insert high-priority topics into content.db and (b) use `openclaw cron run` to immediately trigger the relevant cron job.

**Primary recommendation:** Fix the analytics status mismatch, fix Slack delivery in cron jobs, add on-demand trigger instructions to Bob's workspace, and verify the full end-to-end pipeline by running each cron manually.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CP-01 | Verify Content DB Bind-Mount | RESOLVED: bind-mount at `~/clawd/content.db:/workspace/content.db:rw` in `agents.defaults.sandbox.docker.binds` correctly serves all agents. Live DB is 81920 bytes with real data. The 0-byte files at `~/clawd/agents/main/content.db`, `~/clawd/agents/quill/content.db`, `~/clawd/agents/ezra/content.db` are irrelevant -- explicit binds overlay workspace mounts. Mission Control db-paths.ts already points to correct path. |
| CP-02 | Verify Cron Pipeline Produces Output | PARTIALLY WORKING: All 5 crons fire successfully (status "ok"), agents do their work (topic research, article writing, reviews, publishing), but ALL crons have Slack notification failures. Agents try to post to `#content-pipeline` by channel name instead of channel ID `C0ADWCMU5F0`. Need to fix session instructions to use `channel:C0ADWCMU5F0` format. |
| CP-03 | On-Demand Content Trigger | NEW CAPABILITY: Requires Bob to accept "write about X" commands, insert topic into content.db, and trigger Quill's writing session. Research found `openclaw cron run --id <id>` command can trigger cron jobs on-demand. Recommend adding workspace instruction doc for Bob. |
| CP-04 | On-Demand Topic Research | NEW CAPABILITY: Same pattern as CP-03 but targeting Vector's topic-research cron. Bob inserts research directive and triggers `openclaw cron run --id 89fa40f7-...`. |
| CP-05 | Social Post Retrieval | PARTIALLY EXISTS: social_posts table has 3 posts (linkedin, twitter, instagram for article 2). Mission Control /content page already displays them. Need Bob to be able to retrieve and format social copy on demand via DM. |
| CP-06 | Fix Content Analytics | STATUS MISMATCH: PipelineChart expects `researched/written/reviewed/published` but DB has `backlog/writing/review/approved/published/draft/revision/done/completed`. Either fix the chart to use real statuses or fix the API query to map statuses. |
</phase_requirements>

## Standard Stack

### Core (Already Deployed)
| Component | Version/Path | Purpose | Status |
|-----------|-------------|---------|--------|
| OpenClaw | v2026.2.17 | Gateway, agents, crons | Running |
| content.db | `~/clawd/content.db` | SQLite DB for pipeline | 81920 bytes, 4 tables |
| Mission Control | Next.js 14.2.15 | Dashboard, analytics | Port 3001 |
| better-sqlite3 | (in MC) | Node SQLite driver | Working |
| Recharts | (in MC) | Analytics charts | Working |
| SWR | (in MC) | Data fetching | Working |

### Content Agents
| Agent | ID | Workspace | Cron | Slack Channel |
|-------|----|-----------|------|---------------|
| Vector | rangeos | ~/clawd/agents/rangeos | topic-research (Tue+Fri 10AM PT) | #range-ops (C0AC3HB82P5) |
| Quill | quill | ~/clawd/agents/quill | writing-check (daily 11AM PT) | #content-pipeline (C0ADWCMU5F0) |
| Sage | sage | ~/clawd/agents/sage | review-check (2x daily 10AM+3PM PT) | #content-pipeline (C0ADWCMU5F0) |
| Ezra | ezra | ~/clawd/agents/ezra | publish-check (daily 2PM PT) | #content-pipeline (C0ADWCMU5F0) |
| Sentinel | ops | ~/clawd/agents/ops | stuck-check (daily 5PM PT), pipeline-report (Sun 8AM PT) | #ops (C0AD485E50Q) |

### Content Skills
| Skill | Path | Used By |
|-------|------|---------|
| content-strategy | ~/.openclaw/skills/content-strategy | Vector |
| seo-writer | ~/.openclaw/skills/seo-writer | Quill |
| content-editor | ~/.openclaw/skills/content-editor | Sage |
| wordpress-publisher | ~/.openclaw/skills/wordpress-publisher | Ezra |
| social-promoter | ~/.openclaw/skills/social-promoter | Ezra |

## Architecture Patterns

### Content DB Schema (Live)
```sql
-- topics: 21 rows (7 backlog, 7 writing, 2 review, 2 published, 2 completed, 1 done)
CREATE TABLE topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL, slug TEXT NOT NULL UNIQUE, brief TEXT,
  keywords TEXT, content_type TEXT DEFAULT 'article',
  status TEXT DEFAULT 'backlog', priority INTEGER DEFAULT 2,
  source_url TEXT, category TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- articles: 14 rows (6 writing, 4 review, 1 approved, 1 draft, 2 published)
CREATE TABLE articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id INTEGER REFERENCES topics(id),
  title TEXT, slug TEXT UNIQUE, content TEXT, body TEXT,
  meta_description TEXT, word_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'draft', claimed_by TEXT, claimed_at DATETIME,
  seo_score REAL, readability_score REAL, accuracy_score REAL,
  reviewer_notes TEXT, wp_post_id INTEGER, wp_url TEXT, published_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- social_posts: 3 rows (all draft, for article 2)
CREATE TABLE social_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER REFERENCES articles(id),
  platform TEXT NOT NULL, content TEXT NOT NULL,
  image_prompt TEXT, status TEXT DEFAULT 'draft',
  post_url TEXT, posted_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- pipeline_activity: 28 rows
CREATE TABLE pipeline_activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
  agent_id TEXT, action TEXT NOT NULL,
  old_status TEXT, new_status TEXT, details TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Docker Bind-Mount Architecture
```
Host path                              -> Container path      Mode
/home/ubuntu/clawd/agents/{agent_id}/  -> /workspace/         rw    (agent workspace)
/home/ubuntu/clawd/content.db          -> /workspace/content.db  rw  (explicit overlay)
/home/ubuntu/clawd/coordination.db     -> /workspace/coordination.db  rw
/home/ubuntu/clawd/agents/main/email.db -> /workspace/email.db  rw
/home/ubuntu/clawd/sqlite3-compat     -> /usr/bin/sqlite3     ro
```
The explicit binds OVERLAY the workspace mount. So even though `/workspace/` points to
the agent's own directory, `/workspace/content.db` always points to the shared DB.

### Cron Job Pattern
```
Cron fires -> OpenClaw creates agent session -> agent reads SESSION.md from /workspace/
-> agent uses sqlite3 on /workspace/content.db -> agent tries to post to Slack
```

Each cron uses `kind: "agentTurn"` with a message pointing to a session instruction file
(e.g., `/workspace/WRITING_SESSION.md`). The `sessionTarget` field determines which agent
runs the session.

### On-Demand Trigger Pattern (Recommended)
```
User DMs Bob "write about X" -> Bob:
  1. INSERT INTO topics (title, slug, brief, keywords, status, priority)
     VALUES (..., 'backlog', 1)  -- high priority
  2. Optionally run: openclaw cron run --id writing-check
     (NOTE: this is a debug command, runs immediately)
  3. Reply with confirmation
```

The `openclaw cron run --id <job_id>` command triggers a cron job immediately.
This is the simplest way to support on-demand triggering without building new infrastructure.

### Slack Channel ID Reference
```
#popsclaw     -> C0AD48J8CQY  (Bob/main)
#range-ops    -> C0AC3HB82P5  (Vector/rangeos)
#ops          -> C0AD485E50Q  (Sentinel/ops)
#content-pipeline -> C0ADWCMU5F0  (Quill, Sage, Ezra)
#land-ops     -> C0AD4842LJC  (Scout/landos)
Andy's DM     -> D0AARQR0Y4V
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| On-demand content trigger | Custom webhook/API endpoint | Bob workspace protocol doc + `openclaw cron run` | Agents already understand workspace docs; cron run is built-in |
| Social post retrieval | New API route or skill | Bob workspace protocol doc with SQL query | Bob already has sqlite3 access; just needs instructions |
| Analytics status mapping | Change DB schema to match chart | Fix chart/API to use real DB statuses | DB statuses are used by all agents; changing schema would break everything |
| Slack notification fix | Custom Slack integration | Fix session instruction MDs to use `channel:C0ADWCMU5F0` format | OpenClaw already supports Slack; agents just use wrong channel reference |

## Common Pitfalls

### Pitfall 1: Slack Channel Name vs ID
**What goes wrong:** All content cron summaries fail with "Slack channels require a channel id (use channel:<id>)" or "Action send requires a target."
**Why it happens:** Session instruction files tell agents to "post to #content-pipeline" using the channel name. OpenClaw's send action requires `channel:C0ADWCMU5F0` format, not `#content-pipeline`.
**How to avoid:** Update ALL session instruction files (TOPIC_RESEARCH.md, WRITING_SESSION.md, REVIEW_SESSION.md, PUBLISH_SESSION.md) to reference channel IDs explicitly. Add the channel ID reference to each file.
**Warning signs:** Cron run summary contains "Message failed: Slack channels require a channel id"

### Pitfall 2: 0-Byte content.db Files in Agent Workspaces
**What goes wrong:** Some agents have 0-byte `content.db` files in their workspace dirs (`~/clawd/agents/quill/content.db`, `~/clawd/agents/ezra/content.db`).
**Why it happens:** These were likely created during testing. Docker bind-mount overlays them with the real DB at runtime.
**How to avoid:** Delete these 0-byte files to avoid confusion. They are masked by bind-mount at runtime but could confuse debugging.
**Warning signs:** `file content.db` shows "empty" instead of "SQLite 3.x database" when checking agent workspaces.

### Pitfall 3: Analytics Chart Status Mismatch
**What goes wrong:** PipelineChart renders empty because the API returns statuses like `writing`, `review`, `approved`, `published` but the chart's `STATUS_COLORS` map only has keys `researched`, `written`, `reviewed`, `published`.
**Why it happens:** The chart was designed with idealized status names that don't match the actual pipeline DB schema.
**How to avoid:** Update `pipeline-chart.tsx` STATUS_COLORS and `chartConfig` to match the real status values from `articles` table: `draft`, `writing`, `review`, `revision`, `approved`, `published`.
**Warning signs:** "No content pipeline data yet" message on analytics page despite having 14 articles.

### Pitfall 4: `openclaw cron run` Needs Gateway URL
**What goes wrong:** CLI commands fail with "1006 abnormal closure" when run over SSH.
**Why it happens:** Gateway binds to tailnet (100.72.143.9:18789), but CLI defaults to localhost.
**How to avoid:** Set env var or use `gateway.remote.url` in openclaw.json (already configured). For SSH commands, ensure gateway remote URL is used.
**Warning signs:** "no close frame" errors in CLI output.

### Pitfall 5: content.db Has Both `content` and `body` Columns in articles
**What goes wrong:** Article body could be stored in wrong column.
**Why it happens:** Schema has both `content TEXT` and `body TEXT` in articles table (likely from migration).
**How to avoid:** All session instructions use `body` column. Verify both columns; if `content` is unused, ignore it.
**Warning signs:** Articles appear to have no body text.

### Pitfall 6: Cron Agent Assignment
**What goes wrong:** Crons show as running on wrong agent (e.g., writing-check shows `agent=main` in cron list but `sessionTarget=quill`).
**Why it happens:** The `cron list` output `Agent` column shows the legacy `agentId` field, while `sessionTarget` is the actual agent that runs the session. Some crons have `agentId: null` (shown as "default" in list) but correct `sessionTarget`.
**How to avoid:** Always check `sessionTarget` in jobs.json, not the `Agent` column in `cron list`.

## Code Examples

### Fix Analytics Pipeline Chart Status Colors
```typescript
// Current (BROKEN - statuses don't match DB):
const STATUS_COLORS: Record<string, string> = {
  researched: "hsl(217, 91%, 60%)",
  written: "hsl(38, 92%, 50%)",
  reviewed: "hsl(262, 83%, 58%)",
  published: "hsl(142, 71%, 45%)",
};

// Fixed (matches actual DB statuses):
const STATUS_COLORS: Record<string, string> = {
  draft: "hsl(220, 14%, 46%)",
  writing: "hsl(217, 91%, 60%)",
  review: "hsl(38, 92%, 50%)",
  revision: "hsl(25, 95%, 53%)",
  approved: "hsl(262, 83%, 58%)",
  published: "hsl(142, 71%, 45%)",
};

const chartConfig: ChartConfig = {
  draft: { label: "Draft", color: STATUS_COLORS.draft },
  writing: { label: "Writing", color: STATUS_COLORS.writing },
  review: { label: "In Review", color: STATUS_COLORS.review },
  revision: { label: "Revision", color: STATUS_COLORS.revision },
  approved: { label: "Approved", color: STATUS_COLORS.approved },
  published: { label: "Published", color: STATUS_COLORS.published },
};
```

### On-Demand Content Trigger Protocol (Bob Workspace Doc)
```markdown
# On-Demand Content Triggers

## "Write about X" Command
When user says "write about X" or "create an article about X":

1. Insert topic with high priority:
   ```sql
   BEGIN IMMEDIATE;
   INSERT INTO topics (title, slug, brief, keywords, status, priority)
   VALUES ('<title from user request>', '<slug>', '<brief based on request>',
           '<relevant keywords>', 'backlog', 1);
   INSERT INTO pipeline_activity (entity_type, entity_id, agent_id, action,
     old_status, new_status, details)
   VALUES ('topics', last_insert_rowid(), 'main', 'created', NULL, 'backlog',
           'On-demand request from user');
   COMMIT;
   ```

2. Confirm topic created and inform user it will be picked up by Quill.

3. Optionally: user can say "trigger writing now" to run immediately.

## "Research topics about X" Command
When user says "research topics about X":

1. Insert a research directive into /workspace/memory/ as a note for Vector.
2. Inform user that Vector will research on next cron cycle (Tue/Fri 10AM PT).
3. If user wants immediate research: they can ask to trigger the cron.
```

### Slack Channel ID Fix for Session Files
```markdown
## Posting Results
Post your summary to #content-pipeline using channel ID:
- Channel: channel:C0ADWCMU5F0
- Format: Brief summary of what was accomplished this session
```

### Social Post Retrieval Query (for Bob)
```sql
-- Get all social copy for a specific article
SELECT sp.platform, sp.content, sp.image_prompt, sp.status
FROM social_posts sp
JOIN articles a ON sp.article_id = a.id
WHERE a.title LIKE '%keyword%'
ORDER BY sp.platform;

-- Get all pending social posts
SELECT a.title, sp.platform, sp.content
FROM social_posts sp
JOIN articles a ON sp.article_id = a.id
WHERE sp.status = 'draft'
ORDER BY a.title, sp.platform;
```

## State of the Art

| Old State | Current State | When Changed | Impact |
|-----------|--------------|--------------|--------|
| content.db at agents/main/ | content.db at ~/clawd/ | 2026-02-22 (quick task 3) | DB path fixed, MC db-paths.ts updated |
| No Mission Control content page | /content page with 4 components | 2026-02-22 | Topics, articles, social posts, activity visible |
| No analytics pipeline chart | PipelineChart component exists | 2026-02-22 | Chart renders but empty due to status mismatch |
| Cron Slack messages worked | All cron Slack messages failing | ~2026-02-20+ | Agents can't post summaries; work still happens silently |

## Open Questions

1. **Why do some crons show different agents than expected?**
   - What we know: `cron list` shows topic-research as `rangeos`, writing-check as `quill`, but cron runs show session keys like `agent:main:cron:writing-check:*`
   - What's unclear: Whether the `sessionTarget` actually creates the session under the correct agent, or if all sessions run under `main` with a reference to the target agent
   - Recommendation: Run a manual cron test and check which agent workspace is mounted. The cron run output suggests some may be running under `main` agent context.

2. **Should `openclaw cron run` be exposed to Bob?**
   - What we know: `openclaw cron run --id <id>` exists as a debug command
   - What's unclear: Whether this is safe for production use (e.g., can it cause overlapping sessions if a cron is already mid-run?)
   - Recommendation: Test manually first. If safe, add as an elevated command for Bob. Otherwise, use simpler approach of just inserting topics and letting scheduled crons pick them up.

3. **Topics/articles status inconsistency**
   - What we know: Topics have statuses `backlog/writing/review/published/completed/done`. Articles have `draft/writing/review/revision/approved/published`.
   - What's unclear: Whether `completed` and `done` are intentional distinct statuses or artifacts
   - Recommendation: During verification, audit and clean up orphan statuses. For analytics, only chart article statuses (more meaningful).

## Sources

### Primary (HIGH confidence)
- Live EC2 inspection via SSH (2026-02-23) -- openclaw.json, content.db, cron runs, file system
- Mission Control source code -- analytics page, pipeline chart, API routes, content queries
- OpenClaw cron jobs.json -- full job configurations
- Agent workspace files -- TOPIC_RESEARCH.md, WRITING_SESSION.md, REVIEW_SESSION.md, PUBLISH_SESSION.md

### Secondary (MEDIUM confidence)
- Cron run history via `openclaw cron runs` -- actual execution logs with timestamps and summaries
- Docker container inspection -- confirmed bind-mount overlay behavior

## Metadata

**Confidence breakdown:**
- DB bind-mount (CP-01): HIGH -- verified via file system, Docker inspect, and openclaw.json
- Cron pipeline (CP-02): HIGH -- verified via cron runs command, identified specific failure pattern
- On-demand triggers (CP-03/04): MEDIUM -- approach is sound but `openclaw cron run` needs testing for safety
- Social retrieval (CP-05): HIGH -- schema verified, data exists, queries straightforward
- Analytics fix (CP-06): HIGH -- exact status mismatch identified with code fix ready

**Research date:** 2026-02-23
**Valid until:** 2026-03-07 (30 days for stable infrastructure)
