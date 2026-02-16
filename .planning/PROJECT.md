# Pops-Claw: Proactive Daily Companion

## What This Is

A proactive AI companion (Bob) running on OpenClaw v2026.2.6-3, deployed on AWS EC2 with Tailscale-only access. Bob delivers daily briefings with health/calendar/email/weather/tasks/devices/GitHub data, controls smart home devices, reviews PRs, tracks expenses, and coordinates a 7-agent multi-agent system — all proactively, before being asked. An autonomous content marketing pipeline (v2.1) researches UAS/drone topics, writes SEO articles, reviews quality, publishes to WordPress, generates social copy, and monitors pipeline health — all with human approval gates.

## Core Value

Bob delivers a genuinely useful morning briefing, knows your health data, manages home devices, reviews code, coordinates a 7-agent multi-agent system, and runs an autonomous content marketing pipeline with self-monitoring — all for ~$0 incremental cost on existing Claude Pro 200.

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

### Active

#### Current Milestone: v2.2 Resend Email Integration

**Goal:** Give Bob a dedicated email API via Resend — send, receive, and reply to email autonomously with a verified subdomain.

**Target features:**
- Resend account + API key + DNS verification on subdomain of existing domain
- Resend MCP server installed on OpenClaw
- Resend skills installed on OpenClaw
- Outbound email (briefings, alerts, notifications)
- Inbound email via Resend webhook → n8n on VPS → forwarded to Bob over Tailscale
- Email reply capability
- API key securely in sandbox env, webhook signing verification

### Out of Scope

- Voice input (evaluate at day 60)
- Public API exposure
- EC2 instance upgrade
- Offline mode — real-time connectivity is core

## Context

**Shipped v2.0** (10 days) + **v2.1** (1 day) = full proactive companion + autonomous content pipeline.

**Tech stack:** OpenClaw v2026.2.6-3, AWS EC2 Ubuntu, Tailscale, Docker sandbox, SQLite (health.db + coordination.db + content.db), Slack Socket Mode, Gmail/Calendar via gog CLI, Chromium browser automation, WordPress REST API.

**Infrastructure:**
- AWS EC2 Ubuntu, Tailscale IP: 100.72.143.9
- Gateway port: 18789 (loopback only)
- Workspace: ~/clawd/ on EC2
- Config: ~/.openclaw/openclaw.json
- Service: openclaw-gateway.service (systemd user)

**Skills deployed:** oura, govee (includes Wyze), coding-assistant, receipt-scanner, content-strategy, seo-writer, content-editor, wordpress-publisher, social-promoter

**Cron jobs (18 total):** morning-briefing (7 AM PT), evening-recap (7 PM PT), weekly-review (Sun 8 AM PT), meeting-prep-scan (*/15), anomaly-check (2x daily), daily-standup (8 AM EST), monthly-expense-summary (1st of month), 4 heartbeats (15min), topic-research (Tue+Fri 10 AM PT), writing-check (daily 11 AM PT), review-check (2x/day 10 AM + 3 PM PT), publish-check (daily 2 PM PT), pipeline-report (Sun 8 AM PT), stuck-check (daily 9 AM PT)

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
- **Database**: SQLite (coordination + health + receipts)
- **Security**: Tailscale-only, no public exposure
- **Budget**: $0 incremental (except optional Superwhisper $8/mo)
- **Rate Limits**: Haiku for heartbeats to avoid hitting Sonnet/Opus limits

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
| Gmail scope reduction deferred | Re-auth disruption not worth it | ⚠️ Revisit — 2 excess scopes remain |
| SQLite for content pipeline (not Notion) | Real transactions, no race conditions | ✓ Good — content.db working |
| 1 shared #content-pipeline channel | Simpler than 3 separate channels | ✓ Good — C0ADWCMU5F0 |
| No heartbeats for content agents | Cron-only workers, reduce rate limit pressure | ✓ Good — 6 crons sufficient |
| Human approval gate before publish | Safety over full automation | ✓ Good — path to automation later |
| content.db all-agent bind-mount | Same pattern as coordination.db | ✓ Good — all agents access |
| Copy-only social promotion | No API auth needed, human posts | ✓ Good — reduces complexity |
| Ops reporting via reference docs | Same pattern as cron instructions | ✓ Good — PIPELINE_REPORT.md + STUCK_DETECTION.md |
| Silent-skip stuck detection | No noise when pipeline healthy | ✓ Good — alerts only when needed |

---
*Last updated: 2026-02-16 after v2.2 milestone start*
