# v2.1 Content Marketing Pipeline — Requirements

## Content Pipeline (CP)

- **CP-01**: content.db with 4 tables (topics, articles, social_posts, pipeline_activity) + indexes, bind-mounted to all agents
- **CP-02**: 3 new agents (Quill, Sage, Ezra) in openclaw.json with workspaces + Slack binding
- **CP-03**: #content-pipeline Slack channel bound to all 3 content agents
- **CP-04**: PRODUCT_CONTEXT.md in all content agent workspaces (UAS domain DO/DON'T)
- **CP-05**: content.db claim locking protocol (SQLite transactions, no optimistic locking)
- **CP-06**: Pipeline activity logging in pipeline_activity table
- **CP-07**: Sentinel standup includes content pipeline health metrics

## Topic Research (TR)

- **TR-01**: content-strategy skill for Vector with research methodology
- **TR-02**: Vector searches web for UAS keyword opportunities + industry trends
- **TR-03**: topic-research cron 2x/week (Mon+Thu 10 AM PT = 17:00 UTC)
- **TR-04**: Topics written to content.db with briefs, keyword data, content type

## Writing (WR)

- **WR-01**: seo-writer skill for Quill (article structure, SEO rules, UAS voice)
- **WR-02**: Quill claims + writes 1500-2500 word drafts with H2/H3 structure
- **WR-03**: writing-check cron daily at 11 AM PT (18:00 UTC)
- **WR-04**: Drafts stored in content.db articles table, status → "review"

## Review (RV)

- **RV-01**: content-editor skill for Sage (SEO/readability/accuracy scoring rubric)
- **RV-02**: Sage scores 3 axes; avg < 70 → revision with notes; avg >= 70 → approved
- **RV-03**: review-check cron 2x/day (9 AM + 2 PM PT = 16:00 + 21:00 UTC)
- **RV-04**: On approval, human notified in #content-pipeline with summary

## WordPress Publishing (WP)

- **WP-01**: WordPress REST API credentials (Application Password) configured
- **WP-02**: wordpress-publisher skill for Ezra (WP REST API, markdown→HTML)
- **WP-03**: Ezra creates WP draft, human approves in Slack, Ezra publishes
- **WP-04**: Categories/tags/meta mapped to UAS content pillars
- **WP-05**: content.db updated with wp_post_id + wp_url on publish

## Social Media (SM)

- **SM-01**: LinkedIn API credentials (OAuth 2.0 w/ `w_member_social` scope)
- **SM-02**: social-promoter skill for Ezra (LinkedIn + Instagram formats)
- **SM-03**: LinkedIn posts: professional tone, key stats, article URL, 3-5 hashtags
- **SM-04**: Instagram: generate caption + image prompt (manual post if no API access)

## Monitoring (MN)

- **MN-01**: Weekly pipeline status report in #content-pipeline
- **MN-02**: Stuck article detection (>3 days in any non-terminal status)
- **MN-03**: Content metrics in Sentinel's weekly review

---

**Total: 31 requirements across 7 categories**

## Human Checkpoints

- **Phase 12:** Create #content-pipeline Slack channel, invite bot, provide channel ID
- **Phase 16:** Generate WordPress Application Password, provide credentials
- **Phase 17:** Create LinkedIn developer app, complete OAuth flow, provide tokens. Decide Instagram approach.

## Unresolved Questions

1. LinkedIn Company Page vs personal posting (different API scopes)
2. Instagram: Facebook Business account linked? If not → caption generation only
3. WordPress: existing UAS categories or create new?
4. content.db scope: all-agent bind-mount (like coordination.db) — flag if scoping needed
