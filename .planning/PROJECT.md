# Pops-Claw: Proactive Daily Companion

## What This Is

A proactive AI companion (Bob) running on OpenClaw v2026.2.17, deployed on AWS EC2 with Tailscale-only access. Bob delivers daily briefings with health/calendar/email/weather/tasks/devices/GitHub data, controls smart home devices, reviews PRs, tracks expenses, coordinates a 7-agent multi-agent system, runs an autonomous content marketing pipeline, sends/receives email autonomously via Resend API, and builds working prototypes overnight via YOLO Dev — all proactively, before being asked. Mission Control Dashboard provides a web-based single pane of glass for monitoring the entire system — live database status, agent health with token usage and cache metrics, content pipeline, email metrics, YOLO build history with detail pages and trend charts, CLI tool health, memory browsing, office visualization, and analytics charts, all accessible directly via Tailscale.

## Core Value

Bob delivers a genuinely useful morning briefing, knows your health data, manages home devices, reviews code, coordinates a 7-agent multi-agent system, runs an autonomous content marketing pipeline, communicates via email with a verified domain, builds working prototypes overnight with detailed dashboards and trend analytics, and is monitored via Mission Control Dashboard — all for ~$0 incremental cost on existing Claude Pro 200.

## Requirements

### Validated

- ✓ OpenClaw v2026.2.6-3 deployed with security hardening — v2.0
- ✓ SQLite hybrid memory (builtin sqlite-vec+FTS5, 12 chunks) — v2.0
- ✓ Oura Ring health data integration (sleep, readiness, HRV, HR) — v2.0
- ✓ 7-section morning briefing (calendar, email, health, weather, tasks, Govee, GitHub) — v2.0
- ✓ Evening recap + weekly review automation — v2.0
- ✓ Model routing (Haiku/Sonnet/Opus) with session capping — v2.0
- ✓ GitHub CLI + SQLite CLI in Docker sandbox via bind-mounts — v2.0
- ✓ Govee smart home control (11 lights, room grouping) — v2.0
- ✓ Wyze scale data via Gmail parsing — v2.0
- ✓ 4-agent system (Andy, Scout, Vector, Sentinel) with coordination DB — v2.0
- ✓ Domain Slack channels (#land-ops, #range-ops, #ops) with routing — v2.0
- ✓ Heartbeat crons (4 agents, staggered) + daily standup — v2.0
- ✓ Proactive patterns (pre-meeting prep, anomaly alerts, reminders) — v2.0
- ✓ Agentic coding workflow (PR review, GitHub activity in briefing) — v2.0
- ✓ Receipt scanning + monthly expense summaries — v2.0
- ✓ Slack Socket Mode integration — v1.0
- ✓ Gmail/Calendar via gog CLI — v1.0
- ✓ Browser automation with Chromium — v1.0
- ✓ Cron/scheduled tasks operational — v1.0
- ✓ Tailscale-only secure access — v1.0

- ✓ Content pipeline infrastructure — content.db, 3 agents (Quill, Sage, Ezra), #content-pipeline channel, PRODUCT_CONTEXT.md — v2.1
- ✓ Topic research — Vector content-strategy skill, 2x/week cron, UAS/drone domain — v2.1
- ✓ Writing pipeline — Quill seo-writer skill, daily cron, SEO-optimized articles — v2.1
- ✓ Review pipeline — Sage content-editor skill, scoring rubric, 2x/day cron — v2.1
- ✓ WordPress publishing — Ezra wordpress-publisher skill, human approval gate, REST API drafts — v2.1
- ✓ Social promotion — Copy generation for LinkedIn, X/Twitter, Instagram (human-posted) — v2.1
- ✓ Pipeline monitoring — Sentinel weekly report + daily stuck detection with silent-skip — v2.1

- ✓ Outbound email via Resend API — verified subdomain (bob@mail.andykaufman.net), SPF/DKIM/DMARC, HTML template — v2.2
- ✓ Dual-delivery briefing — Slack then email with health metrics section — v2.2
- ✓ Inbound email pipeline — Resend webhook → n8n (Svix verified) → VPS Caddy → OpenClaw hooks → Bob — v2.2
- ✓ Email processing — email.db (SQLite), sender allowlist, 8-check auto-reply filter (RFC 3834), rate limiting — v2.2
- ✓ Reply threading — In-Reply-To/References headers, delivery status tracking, conversation history — v2.2
- ✓ Domain warmup & hardening — WARMUP.md checklist, quota enforcement (daily 80/95, monthly 2700), catch-up cron — v2.2
- ✓ Email health monitoring — bounce/complaint rates, volume stats, threshold alerts in morning briefing — v2.2

- ✓ OpenClaw updated to v2026.2.17 (CVE-2026-25253 patched), SecureClaw v2.1.0 plugin (51-check audit, 15 behavioral rules) — v2.4
- ✓ Post-update audit — 20 crons, 13 skills, 7 agents confirmed intact; prompt injection protections verified — v2.4
- ✓ Agent observability — observability-hooks plugin (llm_output + agent_end), observability.db, briefing Section 10 — v2.4
- ✓ DMARC escalated to p=quarantine, warmup checklist executed, email health thresholds (WARNING/CRITICAL) — v2.4
- ✓ Platform cleanup — deprecated auth profile removed, config migrated to dmPolicy/allowFrom, gateway.remote.url documented — v2.4

- ✓ WAL-mode database layer (5 SQLite DBs read-only), Convex removed, shadcn/ui, systemd service, Tailscale direct access — v2.5
- ✓ Dashboard status cards (agents, crons, pipeline, email), activity feed from coordination.db, 30s SWR auto-refresh — v2.5
- ✓ Agent board with 7-agent cards: heartbeat status, token usage, model distribution, error counts — v2.5
- ✓ Memory browser with FTS5 search, office view with SVG agent avatars, 4 Recharts analytics charts — v2.5

- ✓ Content pipeline infrastructure verified — bind-mount correct, 0-byte stubs cleaned, all agents on same content.db — v2.6
- ✓ Channel:ID format enforced across all cron payloads and session instruction files — two-level delivery pattern — v2.6
- ✓ On-demand content triggers via Bob DM — write, research, social post retrieval via CONTENT_TRIGGERS.md protocol — v2.6
- ✓ Mission Control analytics pipeline chart rendering real data with stage-ordered SQL — v2.6

- ✓ YOLO Dev build pipeline — nightly cron, idea generation, autonomous prototype building (Python/HTML), yolo.db logging, self-evaluation with guardrails — v2.7
- ✓ Mission Control /yolo page — build history cards with status badges, self-scores, tech stack tags, status filtering, SWR auto-refresh — v2.7
- ✓ Briefing & notification integration — morning briefing Section 11 (YOLO build), weekly YOLO digest, Slack DM build notifications — v2.7
- ✓ CLI tools observability — /tools page tracking 5 CLI tools, 2 plugins, 3 scripts, 24 cron jobs with health indicators and clipboard actions — v2.7

- ✓ Content pipeline bug fix — ghost content.db deleted, bind-mount fixed, SQL query patched for NULL/empty-string wp_post_id — v2.8
- ✓ YOLO detail page — /yolo/{slug} with syntax highlighting, prev/next nav, ScoreRing, status timeline, iframe preview, copy-to-clipboard (12 features beyond MVP) — v2.8
- ✓ Build trend charts — success rate BarChart + avg score LineChart on /yolo page with SWR auto-refresh — v2.8
- ✓ Agent board polish — token usage bars, cache hit rate %, 24h cost display, uniform card height — v2.8
- ✓ Build artifact cleanup — 30-day retention with score >= 4 protection, daily crontab — v2.8
- ✓ Iframe preview for HTML YOLO builds — sandboxed, with "Open in new tab" — v2.8

### Active

## Current Milestone: v2.9 Memory System Overhaul

**Goal:** Fix Bob's broken memory system — compaction config, QMD bootstrapping, retrieval discipline, daily logs, and memory health monitoring.

**Target features:**
- Tune compaction config (reserveTokensFloor, softThresholdTokens, contextTokens)
- Bootstrap QMD collections and verify indexing
- Seed MEMORY.md with curated long-term knowledge
- Add retrieval protocol to AGENTS.md ("search memory before acting")
- Fix memory flush so daily logs actually get written
- Add memory health monitoring to verify the system works

### Out of Scope

- Voice input (evaluate at day 60)
- Public API exposure
- EC2 instance upgrade
- Offline mode — real-time connectivity is core
- Gmail OAuth scope reduction — gog CLI hardcodes gmail.settings.basic + gmail.settings.sharing, cannot be removed without switching tools
- Content distribution (subscriber digest, pitch copy) — deferred from v2.4 Phase 29

## Context

**Shipped v2.0** (10 days) + **v2.1** (1 day) + **v2.2** (2 days) + **v2.4** (4 days) + **v2.5** (2 days) + **v2.6** (2 days) + **v2.7** (3 days) + **v2.8** (5 days) = full proactive companion + content pipeline + email + security + Mission Control Dashboard + content pipeline hardening + YOLO Dev + CLI tools + bug fixes + dashboard polish.

**Tech stack:** OpenClaw v2026.2.17, AWS EC2 Ubuntu, Tailscale, Docker sandbox, SQLite (health.db + coordination.db + content.db + email.db + observability.db + yolo.db), Slack Socket Mode, Gmail/Calendar via gog CLI, Chromium browser automation, WordPress REST API, Resend API, n8n on VPS (DigitalOcean). Mission Control: Next.js 14 + Tailwind + better-sqlite3 at ~/clawd/mission-control/.

**Infrastructure:**
- AWS EC2 Ubuntu, Tailscale IP: 100.72.143.9
- Gateway port: 18789 (tailnet bind)
- VPS (165.22.139.214): Tailscale IP 100.105.251.99, Caddy + n8n in Docker
- Workspace: ~/clawd/ on EC2
- Config: ~/.openclaw/openclaw.json
- Service: openclaw-gateway.service (systemd user)
- Gateway remote URL: `gateway.remote.url: ws://100.72.143.9:18789` in openclaw.json — required because gateway binds to tailnet IP (not loopback), so CLI commands fail with 1006 abnormal closure without it. Added Phase 20 when inbound email required tailnet bind.

**Skills deployed (13):** oura, govee, coding-assistant, receipt-scanner, content-strategy, seo-writer, content-editor, wordpress-publisher, social-promoter, resend-email, clawdstrike, secureclaw, save-voice-notes

**Cron jobs (24 total):** morning-briefing, evening-recap, weekly-review, meeting-prep-scan, anomaly-check (2x), daily-standup, monthly-expense-summary, 4 heartbeats, topic-research, writing-check, review-check, publish-check, pipeline-report, stuck-check, airspace-email-monitor, email-catchup, yolo-dev-overnight, voice-notes-processor, tools-health-check, session-prune

**Databases (6):** health.db, coordination.db, content.db, email.db, observability.db, yolo.db

**Agent Roster:**
| Agent ID | Name | Domain | Heartbeat Offset |
|----------|------|--------|------------------|
| main | Andy | Coordinator | :00 |
| landos | Scout | Land Investing | :02 |
| rangeos | Vector | UAS Operations + Content Strategy | :04 |
| ops | Sentinel | Infra + Coding | :06 |
| quill | Quill | SEO Writer | None (cron only) |
| sage | Sage | Editor/QA | None (cron only) |
| ezra | Ezra | Publisher/Promoter | None (cron only) |

**Cost Model:** Claude Pro 200 ($200/mo flat) — no per-token API costs. Model routing for rate limits, not cost.

## Constraints

- **Platform**: OpenClaw on existing AWS EC2
- **Database**: SQLite (coordination + health + receipts + content + email)
- **Security**: Tailscale-only, no public exposure (except VPS webhook endpoint)
- **Budget**: $0 incremental (except optional Superwhisper $8/mo)
- **Rate Limits**: Haiku for heartbeats to avoid hitting Sonnet/Opus limits
- **Email**: Resend free tier (100/day, 3000/month)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 agents (Andy, Scout, Vector, Sentinel) | Match actual domains | ✓ Good — all 4 heartbeating |
| SQLite over Convex | Already exists, simpler | ✓ Good — health.db + coordination.db |
| Wyze via Gmail parsing (not SDK) | No official API | ✓ Good — works reliably |
| Haiku for heartbeats | Rate limit management | ✓ Good — reduces Sonnet/Opus usage |
| Sentinel covers infra + coding | Natural fit | ✓ Good — standup aggregation |
| Bind-mount over setupCommand | Sandbox FS is read-only | ✓ Good — gh+sqlite3 working |
| "builtin" memory backend | "sqlite-hybrid" not valid config value | ✓ Good — same sqlite-vec+FTS5 |
| Reference doc pattern for crons | Keep systemEvent messages concise | ✓ Good — MEETING_PREP.md, STANDUP.md, etc. |
| Vision-native receipt extraction | No external OCR API needed | ✓ Good — Claude vision handles it |
| Gmail OAuth scopes accepted as-is | gog CLI hardcodes gmail.settings.basic + gmail.settings.sharing into --services gmail — cannot be removed without switching tools. Unused, no security risk behind Tailscale | Done — documented as gog limitation |
| Gateway remote URL for tailnet bind | CLI needs explicit gateway URL when not on loopback | Done — ws://100.72.143.9:18789 |
| SQLite for content pipeline (not Notion) | Real transactions, no race conditions | ✓ Good — content.db working |
| 1 shared #content-pipeline channel | Simpler than 3 separate channels | ✓ Good — C0ADWCMU5F0 |
| No heartbeats for content agents | Cron-only workers, reduce rate limit pressure | ✓ Good — 6 crons sufficient |
| Human approval gate before publish | Safety over full automation | ✓ Good — path to automation later |
| content.db all-agent bind-mount | Same pattern as coordination.db | ✓ Good — all agents access |
| Copy-only social promotion | No API auth needed, human posts | ✓ Good — reduces complexity |
| Ops reporting via reference docs | Same pattern as cron instructions | ✓ Good — PIPELINE_REPORT.md + STUCK_DETECTION.md |
| Silent-skip stuck detection | No noise when pipeline healthy | ✓ Good — alerts only when needed |
| Resend API for email (not SES/Mailgun) | Free tier, simple API, webhook support | ✓ Good — 100/day sufficient |
| Subdomain isolation (mail.andykaufman.net) | Protect parent domain reputation | ✓ Good — SPF/DKIM/DMARC clean |
| Gateway tailnet bind (not loopback) | Enable VPS webhook delivery over Tailscale | ✓ Good — inbound pipeline works |
| n8n on VPS as webhook relay | Caddy TLS + IP restriction + Svix verification | ✓ Good — E2E verified |
| email.db for conversation tracking | Same SQLite pattern as other DBs | ✓ Good — threading + rate limits |
| No auto-reply policy | Human approval for all email replies | ✓ Good — prevents runaway replies |
| Dual-delivery briefing (Slack + email) | Email as backup channel | ✓ Good — Section 8 in briefing |
| Catch-up cron as webhook fallback | Resend list API + dedup via email.db | ✓ Good — secondary safety net |
| SQLite direct reads (not gateway WS) | Dashboard reads DBs directly, no gateway dependency | ✓ Good — simpler, faster |
| WAL-mode read-only connections | Concurrent reads without blocking gateway writes | ✓ Good — no contention |
| SWR 30s polling (not WebSocket) | Single user, polling sufficient | ✓ Good — minimal infrastructure |
| Tailscale direct bind at :3001 | No SSH tunnel needed, simpler access | ✓ Good — one-click access |
| Per-subsystem query modules | Independent error handling, not one mega route | ✓ Good — clean boundaries |
| FTS5 with LIKE fallback | Robust search even with syntax errors | ✓ Good — resilient UX |
| Recharts for visualization | React-native, no D3 complexity | ✓ Good — charts working |
| Channel:ID format everywhere | Gateway validates channel IDs at tool call level | ✓ Good — reliable Slack delivery |
| SQL CASE ordering for pipeline stages | Keep stage sequence in query layer, not app | ✓ Good — clean separation |
| Workspace protocol doc for Bob triggers | Standing instructions over skill triggers | ✓ Good — CONTENT_TRIGGERS.md working |
| Python sqlite3 for sandbox DB access | CLI sqlite3 and better-sqlite3 unavailable in Docker sandbox | ✓ Good — reliable reads/writes |
| Docker workspace subdirs over nested bind-mounts | Nested bind-mounts unreliable in isolated cron sessions | ✓ Good — fixed cron build execution |
| Explicit bind-mount for yolo-dev in openclaw.json | Isolated cron sessions use virtual sandbox, need explicit binds | ✓ Good — pattern for future sandbox mounts |
| Client-side filtering for YOLO builds | <100 builds, simpler than server-side query params | ✓ Good — clean implementation |
| Health dots over Badge pills | Compact table density for CLI tools dashboard | ✓ Good — readable at a glance |
| 5-minute health check cron | Balance between freshness and resource usage | ✓ Good — tools-health.json always current |
| Inline 837-line detail page (no component split) | Single-use page, avoid file proliferation | ✓ Good — pragmatic for single detail view |
| Regex tokenizer for syntax highlighting (zero deps) | Avoid adding Prism/highlight.js bundle | ✓ Good — lightweight, sufficient for Python/JS/HTML/CSS |
| Defensive SQL: NULL OR empty-string | SQLite text columns can have either state | ✓ Good — prevents silent data miss |
| Score >= 4 retention threshold for YOLO cleanup | 4=solid, 5=impressive per YOLO_BUILD.md | ✓ Good — preserves quality builds |
| Delete disk dirs, keep DB rows for cleanup | Trend charts need DB rows intact | ✓ Good — charts unaffected by cleanup |
| Verification backfill via live SSH evidence | More reliable than inferring from plan docs | ✓ Good — audit-quality evidence |

---
*Last updated: 2026-03-08 after v2.9 milestone start*
