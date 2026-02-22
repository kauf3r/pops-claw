# Pops-Claw: Proactive Daily Companion

## What This Is

A proactive AI companion (Bob) running on OpenClaw v2026.2.17, deployed on AWS EC2 with Tailscale-only access. Bob delivers daily briefings with health/calendar/email/weather/tasks/devices/GitHub data, controls smart home devices, reviews PRs, tracks expenses, coordinates a 7-agent multi-agent system, runs an autonomous content marketing pipeline, and sends/receives email autonomously via Resend API — all proactively, before being asked. Mission Control Dashboard (shipped v2.5) provides a web-based single pane of glass for monitoring the entire system — live database status, agent health, content pipeline, email metrics, memory browsing, office visualization, and analytics charts, all accessible directly via Tailscale.

## Core Value

Bob delivers a genuinely useful morning briefing, knows your health data, manages home devices, reviews code, coordinates a 7-agent multi-agent system, runs an autonomous content marketing pipeline, communicates via email with a verified domain, and is monitored via Mission Control Dashboard — all for ~$0 incremental cost on existing Claude Pro 200.

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

### Active

(No active milestone — run `/gsd:new-milestone` to start next)

### Out of Scope

- Voice input (evaluate at day 60)
- Public API exposure
- EC2 instance upgrade
- Offline mode — real-time connectivity is core
- Gmail OAuth scope reduction — gog CLI hardcodes gmail.settings.basic + gmail.settings.sharing, cannot be removed without switching tools
- Content distribution (subscriber digest, pitch copy) — deferred from v2.4 Phase 29
- Context usage indicators on agent cards — deferred from v2.5 Phase 31.1
- Agent board visual polish — deferred from v2.5 Phase 31.2

## Context

**Shipped v2.0** (10 days) + **v2.1** (1 day) + **v2.2** (2 days) + **v2.4** (4 days) + **v2.5** (2 days) = full proactive companion + content pipeline + email + security + Mission Control Dashboard.

**Tech stack:** OpenClaw v2026.2.17, AWS EC2 Ubuntu, Tailscale, Docker sandbox, SQLite (health.db + coordination.db + content.db + email.db + observability.db), Slack Socket Mode, Gmail/Calendar via gog CLI, Chromium browser automation, WordPress REST API, Resend API, n8n on VPS (DigitalOcean). Mission Control: Next.js 14 + Tailwind + better-sqlite3 at ~/clawd/mission-control/.

**Infrastructure:**
- AWS EC2 Ubuntu, Tailscale IP: 100.72.143.9
- Gateway port: 18789 (tailnet bind)
- VPS (165.22.139.214): Tailscale IP 100.105.251.99, Caddy + n8n in Docker
- Workspace: ~/clawd/ on EC2
- Config: ~/.openclaw/openclaw.json
- Service: openclaw-gateway.service (systemd user)
- Gateway remote URL: `gateway.remote.url: ws://100.72.143.9:18789` in openclaw.json — required because gateway binds to tailnet IP (not loopback), so CLI commands fail with 1006 abnormal closure without it. Added Phase 20 when inbound email required tailnet bind.

**Skills deployed (13):** oura, govee, coding-assistant, receipt-scanner, content-strategy, seo-writer, content-editor, wordpress-publisher, social-promoter, resend-email, clawdstrike, secureclaw, save-voice-notes

**Cron jobs (20 total):** morning-briefing, evening-recap, weekly-review, meeting-prep-scan, anomaly-check (2x), daily-standup, monthly-expense-summary, 4 heartbeats, topic-research, writing-check, review-check, publish-check, pipeline-report, stuck-check, airspace-email-monitor, email-catchup

**Databases (5):** health.db, coordination.db, content.db, email.db, observability.db

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

---
*Last updated: 2026-02-22 after v2.5 milestone completion*
