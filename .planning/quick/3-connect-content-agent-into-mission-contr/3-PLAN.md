---
phase: quick
plan: 3
type: execute
wave: 1
depends_on: []
files_modified:
  - ~/clawd/agents/main/content.db (EC2 - schema init)
  - ~/clawd/mission-control/src/lib/queries/content.ts (EC2)
  - ~/clawd/mission-control/src/app/api/content/topics/route.ts (EC2)
  - ~/clawd/mission-control/src/app/api/content/articles/route.ts (EC2)
  - ~/clawd/mission-control/src/app/api/content/activity/route.ts (EC2)
  - ~/clawd/mission-control/src/app/content/page.tsx (EC2)
  - ~/clawd/mission-control/src/components/content/TopicBacklog.tsx (EC2)
  - ~/clawd/mission-control/src/components/content/ArticlePipeline.tsx (EC2)
  - ~/clawd/mission-control/src/components/content/PipelineActivity.tsx (EC2)
  - ~/clawd/mission-control/src/components/NavBar.tsx (EC2)
autonomous: true
requirements: [CONTENT-PAGE]

must_haves:
  truths:
    - "content.db has topics, articles, and pipeline_activity tables with correct schema"
    - "Mission Control /content page shows topic backlog with priority, status, keywords"
    - "Mission Control /content page shows article pipeline with status and scores"
    - "Mission Control /content page shows recent pipeline activity feed"
    - "NavBar includes Content link that navigates to /content"
    - "Existing dashboard PipelineMetrics component still works (reads same db)"
  artifacts:
    - path: "~/clawd/agents/main/content.db"
      provides: "Initialized SQLite database with 3 tables"
      contains: "topics, articles, pipeline_activity tables"
    - path: "~/clawd/mission-control/src/lib/queries/content.ts"
      provides: "Query functions for topics, articles, activity"
      exports: ["getTopicBacklog", "getArticlePipeline", "getPipelineActivityFeed"]
    - path: "~/clawd/mission-control/src/app/content/page.tsx"
      provides: "Content pipeline page with 3 sections"
      min_lines: 50
    - path: "~/clawd/mission-control/src/components/NavBar.tsx"
      provides: "Navigation with Content link"
      contains: "/content"
  key_links:
    - from: "src/app/content/page.tsx"
      to: "/api/content/topics, /api/content/articles, /api/content/activity"
      via: "SWR fetching"
      pattern: "useSWR.*api/content"
    - from: "src/app/api/content/*/route.ts"
      to: "src/lib/queries/content.ts"
      via: "query function imports"
      pattern: "import.*from.*queries/content"
    - from: "src/lib/queries/content.ts"
      to: "getDb('content')"
      via: "better-sqlite3 readonly connection"
      pattern: "getDb\\(\"content\"\\)"
---

<objective>
Initialize content.db schema on EC2 and add a /content page to Mission Control showing the full content marketing pipeline: topic backlog, article pipeline, and activity feed.

Purpose: The content-strategy and content-editor skills INSERT into content.db but the schema was never created (file is 0 bytes). The existing dashboard shows a PipelineMetrics badge card but there's no dedicated page to see the full pipeline. This connects the content agent's work into the Mission Control single-pane-of-glass.

Output: Working content.db with tables + /content page in Mission Control accessible from navbar.
</objective>

<execution_context>
@/Users/andykaufman/.claude/get-shit-done/workflows/execute-plan.md
@/Users/andykaufman/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

EC2 access: ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9
Mission Control code: ~/clawd/mission-control/ on EC2
content.db: ~/clawd/agents/main/content.db (currently 0 bytes)

Existing patterns to follow:
- db.ts: getDb("content") returns Database | null, opens readonly with fileMustExist
- db-paths.ts: content path is /home/ubuntu/clawd/agents/main/content.db
- queries/analytics.ts: query pattern (getDb, table existence check, try/catch)
- API routes: NextResponse.json, export const dynamic = "force-dynamic"
- Pages: "use client", SWR for data fetching, Card/CardHeader/CardTitle/CardContent from @/components/ui/card
- NavBar.tsx: links array with { href, label, icon }
- UI components available: badge, button, card, chart, input, scroll-area, separator, table
</context>

<tasks>

<task type="auto">
  <name>Task 1: Initialize content.db schema and create query layer</name>
  <files>
    ~/clawd/agents/main/content.db (EC2)
    ~/clawd/mission-control/src/lib/queries/content.ts (EC2)
    ~/clawd/mission-control/src/app/api/content/topics/route.ts (EC2)
    ~/clawd/mission-control/src/app/api/content/articles/route.ts (EC2)
    ~/clawd/mission-control/src/app/api/content/activity/route.ts (EC2)
  </files>
  <action>
    **Step 1: Initialize content.db on EC2 via SSH.**

    Run sqlite3 to create the schema. The file is owned by root (from Docker bind-mount), so use sudo. After creating tables, set WAL mode so the readonly Mission Control connection works alongside the agent's write connection.

    ```sql
    CREATE TABLE IF NOT EXISTS topics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      slug TEXT NOT NULL UNIQUE,
      brief TEXT,
      keywords TEXT,
      content_type TEXT DEFAULT 'article',
      status TEXT DEFAULT 'backlog',
      priority INTEGER DEFAULT 2,
      source_url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      topic_id INTEGER REFERENCES topics(id),
      title TEXT,
      slug TEXT UNIQUE,
      content TEXT,
      meta_description TEXT,
      word_count INTEGER DEFAULT 0,
      status TEXT DEFAULT 'draft',
      claimed_by TEXT,
      claimed_at DATETIME,
      seo_score REAL,
      readability_score REAL,
      accuracy_score REAL,
      reviewer_notes TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pipeline_activity (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entity_type TEXT NOT NULL,
      entity_id INTEGER NOT NULL,
      agent_id TEXT,
      action TEXT NOT NULL,
      old_status TEXT,
      new_status TEXT,
      details TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    PRAGMA journal_mode=WAL;
    ```

    Verify tables exist with: `sqlite3 ~/clawd/agents/main/content.db ".tables"`
    Expected output: `articles  pipeline_activity  topics`

    **Step 2: Create `src/lib/queries/content.ts` on EC2.**

    Follow the pattern from `queries/analytics.ts` and `queries/metrics.ts`. Use `getDb("content")` with table existence checks. Export three functions:

    - `getTopicBacklog()`: Returns topics ordered by priority ASC, created_at DESC. Include id, title, slug, brief, keywords, content_type, status, priority, created_at. Return type: `TopicRow[]`.

    - `getArticlePipeline()`: Returns articles joined with topics (for topic title/keywords). Include article id, title, status, word_count, seo_score, readability_score, accuracy_score, claimed_by, created_at, and topic title as topic_title. Order by created_at DESC. Return type: `ArticleRow[]`.

    - `getPipelineActivityFeed(limit = 20)`: Returns recent pipeline_activity rows ordered by created_at DESC with the given limit. Include all columns. Return type: `ActivityRow[]`.

    Each function: get db via `getDb("content")`, return empty array if null, check table existence via sqlite_master before querying, wrap in try/catch returning empty array on error.

    **Step 3: Create 3 API routes on EC2.**

    All follow the same pattern as `src/app/api/analytics/pipeline/route.ts`:
    - `export const dynamic = "force-dynamic"`
    - GET handler, try/catch, NextResponse.json

    `src/app/api/content/topics/route.ts`: calls `getTopicBacklog()`, returns `{ topics: [...] }`
    `src/app/api/content/articles/route.ts`: calls `getArticlePipeline()`, returns `{ articles: [...] }`
    `src/app/api/content/activity/route.ts`: calls `getPipelineActivityFeed()`, returns `{ activity: [...] }`
  </action>
  <verify>
    SSH to EC2 and run:
    1. `sqlite3 ~/clawd/agents/main/content.db ".tables"` -- should show all 3 tables
    2. `sqlite3 ~/clawd/agents/main/content.db "PRAGMA journal_mode;"` -- should show "wal"
    3. `curl -s http://127.0.0.1:3001/api/content/topics | head` -- should return `{"topics":[]}`
    4. `curl -s http://127.0.0.1:3001/api/content/articles | head` -- should return `{"articles":[]}`
    5. `curl -s http://127.0.0.1:3001/api/content/activity | head` -- should return `{"activity":[]}`

    If Mission Control is running, the API calls should work immediately (getDb caches connections, but content.db was previously 0 bytes so it returned null -- restart the service if needed: `sudo systemctl restart mission-control`).
  </verify>
  <done>content.db has 3 tables with WAL mode. All 3 API routes return valid JSON (empty arrays since no data yet). Query layer follows existing codebase patterns.</done>
</task>

<task type="auto">
  <name>Task 2: Build /content page with topic backlog, article pipeline, and activity feed</name>
  <files>
    ~/clawd/mission-control/src/components/content/TopicBacklog.tsx (EC2)
    ~/clawd/mission-control/src/components/content/ArticlePipeline.tsx (EC2)
    ~/clawd/mission-control/src/components/content/PipelineActivity.tsx (EC2)
    ~/clawd/mission-control/src/app/content/page.tsx (EC2)
    ~/clawd/mission-control/src/components/NavBar.tsx (EC2)
  </files>
  <action>
    **Step 1: Create `src/components/content/TopicBacklog.tsx`.**

    "use client" component. Receives `topics` array as prop (from parent page SWR fetch). Renders a Card with:
    - CardHeader: "Topic Backlog" title with count badge
    - CardContent: table using the `table.tsx` UI component (Table, TableHeader, TableRow, TableHead, TableBody, TableCell)
    - Columns: Priority (badge: 1=red, 2=yellow, 3=gray), Title, Status (badge with color by status), Keywords (truncated, muted text), Created
    - If empty: "No topics in backlog" muted text
    - Priority badge colors: use variant="destructive" for 1, variant="secondary" for 2, variant="outline" for 3
    - Status badge: "backlog"=outline, "assigned"/"in_progress"=secondary, "review"=default, "done"=green text

    **Step 2: Create `src/components/content/ArticlePipeline.tsx`.**

    "use client" component. Receives `articles` array as prop. Renders a Card with:
    - CardHeader: "Article Pipeline" title with count badge
    - CardContent: table with columns: Title (with topic_title as muted subtitle), Status (badge), Word Count, Scores (SEO/Read/Acc as 3 small numbers or dashes if null), Claimed By, Created
    - If empty: "No articles in pipeline" muted text
    - Status badges: "draft"=outline, "writing"/"review"=secondary, "revision"=yellow, "approved"=green, "published"=blue
    - Scores: display as "8.5 / 7.0 / 9.0" format, or "--" if all null

    **Step 3: Create `src/components/content/PipelineActivity.tsx`.**

    "use client" component. Receives `activity` array as prop. Renders a Card with:
    - CardHeader: "Recent Activity" title
    - CardContent: simple list (not table) of activity items, each showing:
      - Action text: "{agent_id} {action} {entity_type} #{entity_id}" (e.g., "rangeos created topics #3")
      - Status change: "{old_status} -> {new_status}" if both exist, muted text
      - Details: if present, truncated to 100 chars, muted text
      - Timestamp: relative or formatted date, far right, muted
    - If empty: "No pipeline activity yet" muted text
    - Use a simple div list with border-b separators, not a table

    **Step 4: Create `src/app/content/page.tsx`.**

    "use client" page. Follow the calendar page pattern:
    - 3 SWR fetches: `/api/content/topics`, `/api/content/articles`, `/api/content/activity`
    - Use `useSWR` from "swr" (already a project dependency)
    - Layout: max-w-7xl container with px-6 py-6 (matches other pages)
    - Header: "Content Pipeline" h1 with "AirSpace Integration content marketing" subtitle in muted text
    - Grid layout: 2 columns on lg (topics left, articles right), full width on mobile
    - Activity feed spans full width below the grid
    - Show "Loading..." placeholder while SWR fetches (matches calendar pattern)
    - Refresh interval: 30000ms (30s) for activity feed, 60000ms for topics/articles

    ```tsx
    import useSWR from "swr";
    const fetcher = (url: string) => fetch(url).then(r => r.json());

    // In component:
    const { data: topicData } = useSWR("/api/content/topics", fetcher, { refreshInterval: 60000 });
    const { data: articleData } = useSWR("/api/content/articles", fetcher, { refreshInterval: 60000 });
    const { data: activityData } = useSWR("/api/content/activity", fetcher, { refreshInterval: 30000 });
    ```

    **Step 5: Add Content link to NavBar.tsx.**

    Add to the `links` array in NavBar.tsx, between "Office" and "Analytics":
    ```ts
    { href: "/content", label: "Content", icon: null },
    ```

    This keeps the nav logically grouped (operational pages together).
  </action>
  <verify>
    1. SSH to EC2, restart Mission Control if needed: `sudo systemctl restart mission-control`
    2. Wait 5 seconds, then: `curl -s http://127.0.0.1:3001/content | grep -c "Content Pipeline"` -- should be >= 1
    3. `curl -s http://127.0.0.1:3001/content | grep -c "Topic Backlog"` -- should be >= 1
    4. `curl -s http://127.0.0.1:3001/content | grep -c "Article Pipeline"` -- should be >= 1
    5. `curl -s http://127.0.0.1:3001/content | grep -c "Recent Activity"` -- should be >= 1
    6. Verify NavBar: `curl -s http://127.0.0.1:3001/ | grep -c "/content"` -- should be >= 1
    7. Verify build: `cd ~/clawd/mission-control && npx next build 2>&1 | tail -5` -- should complete without errors

    Optional smoke test with real data:
    ```sql
    sqlite3 ~/clawd/agents/main/content.db "INSERT INTO topics (title, slug, brief, keywords, priority) VALUES ('Test Topic', 'test-topic', 'Test brief', 'test,keyword', 1);"
    sqlite3 ~/clawd/agents/main/content.db "INSERT INTO pipeline_activity (entity_type, entity_id, agent_id, action, new_status, details) VALUES ('topics', 1, 'rangeos', 'created', 'backlog', 'Test activity');"
    ```
    Then curl the API routes to confirm data appears. Clean up test data after:
    ```sql
    sqlite3 ~/clawd/agents/main/content.db "DELETE FROM pipeline_activity; DELETE FROM topics;"
    ```
  </verify>
  <done>
    /content page renders in Mission Control with 3 sections (topic backlog, article pipeline, activity feed). NavBar shows "Content" link. Page fetches from 3 API routes via SWR. Empty state shows appropriate messages. Build succeeds with no TypeScript errors.
  </done>
</task>

</tasks>

<verification>
1. content.db has 3 tables (topics, articles, pipeline_activity) with WAL mode
2. All 3 API routes return valid JSON
3. /content page renders with all 3 sections
4. NavBar includes Content link
5. `npx next build` succeeds
6. Existing dashboard PipelineMetrics still works (same getDb("content") path, same articles table)
</verification>

<success_criteria>
- content.db initialized with correct schema matching content-strategy and content-editor skill expectations
- Mission Control /content page accessible from navbar, showing topic backlog, article pipeline, and activity feed
- All data flows: db -> queries -> API routes -> SWR -> components
- Next.js build passes with no errors
- topic-research cron (Tue/Fri 10am) will populate the page automatically on next run
</success_criteria>

<output>
After completion, create `.planning/quick/3-connect-content-agent-into-mission-contr/3-SUMMARY.md`
</output>
