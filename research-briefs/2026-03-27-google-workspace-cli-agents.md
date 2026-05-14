# Google Workspace CLI for AI Agents — gog as Agent Infrastructure

> **gog CLI / Google Workspace** · Technical Brief · `ai_coding` · 2026-03-27

---

## TL;DR

gog CLI v0.9.0 provides production-grade scriptable access to Gmail, Calendar, Drive, Docs, Sheets, Chat, Contacts, Tasks, People, and Keep. Already deployed in Andy's morning briefing. Multi-account support works but 7-day OAuth token expiry in GCP testing mode is an ongoing operational burden.

## Key Insights

- **Comprehensive API coverage.** 10 Google services accessible via CLI with --json, --plain, and --no-input modes for machine-readable, agent-friendly output.
- **Already deployed and working.** Powering morning briefing (Gmail + Calendar), email handler, and airspace email monitor crons on EC2.
- **Multi-account management.** Two Google accounts configured (theandykaufman@gmail.com, kaufman@airspaceintegration.com), switchable via identity flag.
- **Token expiry is the main pain point.** GCP testing-mode OAuth tokens expire every 7 days, requiring manual re-auth flow. Moving to production OAuth would eliminate this.
- **Expansion opportunities.** Sheets-as-database for visible datasets, Chat notifications as Slack alternative, Drive file management, automated document generation.

## Action Plan

- [ ] Evaluate GCP OAuth app production mode vs. maintaining 7-day re-auth cycle
- [ ] Prototype Sheets-as-database for one workflow (e.g., flight log, content calendar)
- [ ] Add Google Chat notification channel for agent alerts

## The One Thing

**gog CLI is already the backbone of agent-Google integration. The only bottleneck is the 7-day OAuth reauth — solving that (GCP production mode) unlocks fully autonomous Google Workspace operations.**

---
*Sources: gog CLI docs, Andy's agent configuration, GCP OAuth documentation*
