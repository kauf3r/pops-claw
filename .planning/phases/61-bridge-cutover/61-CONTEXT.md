# Phase 61: Bridge + Cutover — EC2→Routine Bridge, Sync Migration, Architecture Doc

## Goal
Wire EC2 to the Claude Code Routine via API trigger, replace the Mac launchd file-based sync with a git-based flow, retire the old research-dive cron on EC2, and document the final hybrid architecture.

## Current State (after Phases 59-60)
- EC2 auto-generates briefs for new findings and pushes to GitHub
- Claude Code Routine analyzes topics and generates briefs on Anthropic cloud
- Mac launchd syncs via rsync EC2→local + file copy to LLM-context
- Old research-dive cron still running on EC2 (redundant with Routine)

## Target State
- EC2 detects new un-briefed findings → fires Routine API trigger with topic payload
- Routine does the deep research (on Anthropic cloud, not EC2 tokens)
- Mac sync: `git pull` from pops-claw repo → bridge script copies to LLM-context
- Old research-dive cron disabled on EC2
- Architecture documented for future sessions

## Requirements
- R61-01: Create EC2 bridge script that queries research.db for un-briefed findings, formats topic payload, POSTs to Routine API trigger endpoint
- R61-02: Add EC2 cron for bridge script (Tue/Fri after research-scan, or daily check)
- R61-03: Store Routine API endpoint URL + bearer token securely on EC2 (env var or file with 600 perms)
- R61-04: Update Mac sync script to use `git pull` from pops-claw repo instead of rsync from EC2
- R61-05: Keep LLM-context bridge step (YAML frontmatter transform) — just change the source from rsync to git
- R61-06: Disable old research-dive cron on EC2 (comment out, don't delete — easy rollback)
- R61-07: Test full pipeline: new finding in research.db → EC2 bridge fires → Routine runs → brief committed → Mac pulls → LLM-context updated → Slack notified
- R61-08: Write ARCHITECTURE.md documenting the hybrid flow for future sessions
- R61-09: Monitor for 1 week: verify Routine runs complete successfully, briefs are correct, daily run budget holds

## Dependencies
- Phase 59 complete (GitHub repo + auto-brief)
- Phase 60 complete (Routine created with API trigger)
- Routine API endpoint URL and bearer token available

## Final Architecture
```
EC2 (kept — ingestion layer)           Anthropic Cloud (new — analysis layer)
═══════════════════════════             ═══════════════════════════════════════
x_search, Readwise, RSS, YouTube       Claude Code Routine "Research Analyst"
        ↓                                      ↑              ↓
research.db (topics + findings)         API trigger     Brief generation
        ↓                                      ↑              ↓
Bridge script: detect new findings ──POST──────┘       Commit to GitHub
                                                              ↓
                                                    pops-claw repo
Mac (kept — KB layer)                               (research-briefs/)
═══════════════════                                       ↓
git pull pops-claw ←──────────────────────────────────────┘
        ↓
Bridge script: add YAML frontmatter
        ↓
claude-life-os/LLM-context/sources/
        ↓
Available to all claude-life-os sessions

Slack (new — visibility)
═══════════════════════
← TL;DR posted by Routine connector on each new brief
```

## Rollback Plan
- If Routines are unreliable: re-enable research-dive cron on EC2 (1 config change)
- If git sync is flaky: revert Mac sync to rsync (old script preserved)
- If daily run budget insufficient: reduce to Tue/Fri only (matches current schedule), or upgrade to Max

## Cost Impact
- EC2 token savings: research-dive was Opus-class work on extra usage (~$2-5/run)
- Routine runs: included in Pro plan subscription (no incremental cost up to daily limit)
- Net: reduces extra usage bill by ~$10-20/mo if research runs 3-5x/week
