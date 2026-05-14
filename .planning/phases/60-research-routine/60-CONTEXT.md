# Phase 60: Claude Code Routine — Research Analyst

## Goal
Create a Claude Code Routine that takes a research topic via API trigger, performs deep web research, generates a standardized brief, commits it to the GitHub repo, and posts a TL;DR to Slack. This offloads the most token-expensive work (deep research dives) from EC2 to Anthropic-managed cloud infrastructure.

## Current State
- research-dive cron runs weekdays 2pm on EC2, using Anthropic extra usage tokens via OpenClaw
- Deep research uses x_search + web browsing + multi-source synthesis — expensive (Opus-class)
- No Slack visibility — findings are invisible until you SSH into EC2

## Target State
- Claude Code Routine at claude.ai/code/routines with:
  - API trigger (EC2 fires it when new topics arrive)
  - Weekday schedule trigger (daily research check as backup)
  - Slack connector (post TL;DR on completion)
- Routine clones pops-claw repo, generates brief in standard format, commits to `claude/research-*` branch or directly to `research-briefs/`
- Environment configured with web search access

## Requirements
- R60-01: Create Routine at claude.ai/code/routines named "Research Analyst"
- R60-02: Configure API trigger — store endpoint URL and bearer token securely
- R60-03: Configure scheduled trigger — weekdays (backup to API trigger)
- R60-04: Write routine prompt: accept topic + context in API text payload, research via web search, generate brief in standard format (TL;DR, Key Insights, Action Plan, The One Thing), commit to repo
- R60-05: Connect Slack connector — post brief TL;DR + link to #research or appropriate channel
- R60-06: Configure environment — web search access enabled, any needed env vars
- R60-07: Test end-to-end with sample topic: API trigger → research → brief → commit → Slack notification
- R60-08: Verify daily run budget fits within Pro plan (5/day) or assess Max plan need

## Dependencies
- Phase 59 complete (GitHub repo as brief store)
- Claude Code on the web enabled (claude.ai/code)
- Slack workspace connected as connector
- GitHub connected for repo access

## Routine Architecture
```
API trigger (from EC2)          Schedule trigger (weekday backup)
        │                                │
        └────────────┬───────────────────┘
                     ↓
         Claude Code Routine
         ┌─────────────────────┐
         │ 1. Parse topic from  │
         │    API text payload  │
         │ 2. Web search deep   │
         │    dive (3-5 sources)│
         │ 3. Generate brief in │
         │    standard format   │
         │ 4. Commit to repo    │
         │ 5. Post to Slack     │
         └─────────────────────┘
```

## Limitations (Research Preview)
- 5 runs/day on Pro, 15 on Max — research crons fire ~3x/week, fits Pro
- No custom MCP servers — web search + Slack connector only
- No x_search (xAI) — Routine uses general web search instead
- Fresh repo clone each run — no persistent state
- No retry on failure
- `claude/` branch prefix by default (can be overridden)

## Brief Format (for routine prompt)
```markdown
# {Title}

> **{Source}** · Research Brief · `{track}` · {YYYY-MM-DD}

---

## TL;DR
{2-3 sentences}

## Key Insights
- **{Insight 1 title}.** {Details}
- **{Insight 2 title}.** {Details}
- ...

## Action Plan
- [ ] {Action item 1}
- [ ] {Action item 2}
- ...

## The One Thing
**{Single bold sentence — the key takeaway}**

---
*Sources: {source1}, {source2}, ...*
```
