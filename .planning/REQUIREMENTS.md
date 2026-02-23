# Requirements: v2.6 Content Pipeline Hardening

## CP-01: Verify Content DB Bind-Mount
Confirm `content.db` Docker bind-mount in `openclaw.json` points to the correct live DB path. After the Ezra E2E test, the live DB may be at `~/clawd/agents/main/content.db` while the original mount was `~/clawd/content.db`. All content agents (Quill, Sage, Ezra, Vector) must read/write the same DB file.

## CP-02: Verify Cron Pipeline Produces Output
Run each content cron job manually and confirm it produces expected output:
- `topic-research` (Vector): inserts topics into content.db
- `writing-check` (Quill): claims topic, writes article
- `review-check` (Sage): reviews article, scores it
- `publish-check` (Ezra): creates WP draft for approved articles
- `stuck-check` + `pipeline-report` (Sentinel): monitoring fires correctly

## CP-03: On-Demand Content Trigger
Add ability to tell Bob "write an article about X" and have it:
1. Insert topic into content.db with high priority
2. Trigger Quill's writing session immediately (not waiting for cron)
3. Route through normal review/publish pipeline after writing

## CP-04: On-Demand Topic Research
Add ability to tell Bob "research topics about X" and have Vector research and insert topics immediately rather than waiting for the Tuesday/Friday cron.

## CP-05: Social Post Retrieval
Make social posts from `social_posts` table retrievable on demand. Bob should be able to surface LinkedIn/Twitter/Instagram copy for a published article when asked, formatted and ready to paste.

## CP-06: Fix Content Analytics
Verify Mission Control `/analytics` page content pipeline charts work with real data from content.db. Fix any rendering issues with the pipeline status bar chart.
