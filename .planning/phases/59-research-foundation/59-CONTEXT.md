# Phase 59: Research Foundation — EC2 Schema Fix + Auto-Brief + GitHub Repo

## Goal
Fix the stalled research brief pipeline on EC2 and establish GitHub as the canonical store for research briefs. After this phase, new findings in research.db automatically generate briefs and push them to a GitHub repo.

## Current State
- research.db has 12 findings, 9 without auto-generated briefs (pipeline stalled since Mar 22)
- No `brief_generated` flag in schema — no way to track which findings have briefs
- Briefs exist in 3 places: EC2 filesystem, Mac local dir, LLM-context (fragile rsync chain)
- Manual backfill of 7 briefs done 2026-04-16 (this session)
- EC2 brief format: `# Title\n> Source · Type · track · date\n---\n## TL;DR\n## Key Insights\n## Action Plan\n## The One Thing`

## Target State
- research.db has `brief_generated` column (boolean + timestamp)
- Auto-brief skill on EC2 generates briefs when new findings land (cron or standing order)
- All briefs committed to pops-claw GitHub repo under `research-briefs/`
- EC2 pushes new briefs to GitHub (git remote configured in ~/clawd/research-briefs/)

## Requirements
- R59-01: Add `brief_generated` (INTEGER DEFAULT 0) and `brief_generated_at` (TEXT) columns to research_findings table
- R59-02: Backfill flag for all 12 existing findings (all now have briefs)
- R59-03: Create auto-brief skill (SKILL.md) that reads un-briefed findings, generates standard-format briefs, writes to ~/clawd/research-briefs/, marks as briefed
- R59-04: Add cron job to run auto-brief after research-scan completes (Tue/Fri, ~30 min after scan)
- R59-05: Configure git remote on EC2 ~/clawd/research-briefs/ pointing to pops-claw repo (or dedicated repo)
- R59-06: Auto-brief skill commits + pushes briefs to GitHub after generation
- R59-07: Update INDEX.md auto-generation to include all briefs with track/date metadata

## Dependencies
- SSH access to EC2 (100.72.143.9)
- GitHub repo write access (pops-claw or new dedicated repo)
- research.db schema migration (non-destructive ALTER TABLE)

## Risks
- EC2 sandbox can't push to GitHub (may need host-level git, not sandbox)
- research.db schema migration while gateway is running (SQLite ALTER TABLE is safe for adding columns)

## Track-to-Domain Mapping (reference)
- uas → uas
- land → land-investing
- ai_coding → productivity
- business → productivity
- content → productivity
