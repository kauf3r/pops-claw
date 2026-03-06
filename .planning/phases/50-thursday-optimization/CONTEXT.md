# Phase 50: Thursday Optimization — EC2 Cleanup & Update

## Resume Instructions
Read PLAN.md in this directory. Execute waves 1-4 sequentially via SSH to EC2 (100.72.143.9).
All questions are resolved. No blockers. Start at Wave 1, step 1.1.

## What
Full optimization pass on the pops-claw EC2 instance: reclaim disk, update OpenClaw, prune redundant cron, reduce memory pressure.

## Why
- Disk at 75% (9.6GB free) — several GB reclaimable from caches, old logs, unused Docker images
- OpenClaw 3 versions behind (v2026.2.17 -> v2026.3.2)
- Swap at 50% usage (1GB/2GB) — memory pressure from gateway + 6 containers + QMD
- Redundant cron jobs still running (memory reindex now handled by QMD)
- Plugin dirs unexpectedly large (2.7GB for 2 plugins — @node-llama-cpp duplicates)

## Already Done (Previous Session)
- Installed AgentMail skill + configured API key + tested send/receive
  - inbox: bob-kauf3r@agentmail.to
  - API key in openclaw.json skills.entries.agentmail + Docker env + ~/.openclaw/.env
- Installed QMD memory backend + indexed 19 files + verified search
  - memory.backend = "qmd" in openclaw.json
  - Bun 1.3.10 + QMD 1.1.0 installed, wrapper at ~/.bun/bin/qmd
  - embeddinggemma + query-expansion models downloaded (~2.8GB in ~/.cache/qmd/)
  - searchMode = "search" (BM25+vectors, avoids slow LLM reranker on t3.small)
- Installed agent-browser skill from GitHub into ~/.openclaw/skills/agent-browser/
- Evaluated Google Workspace CLI (skipped — too much overlap with gog)
- Created worktree: .claude/worktrees/thursday-upgrades
- Ran full diagnostic, created this plan, resolved all 4 open questions
- Gateway was restarted during QMD/AgentMail setup — already running with new config

## Execution Status
- Wave 1 (Disk Cleanup): COMPLETE — 3.4GB reclaimed (75% → 66%), plugin llama-cpp pruned
- Wave 2 (OpenClaw Update): COMPLETE — v2026.3.2, gateway bind changed to loopback (v3.2 security enforcement)
- Wave 3 (Cron Pruning): COMPLETE — memory reindex removed, sync-voice + tools-health → 15min
- Wave 4 (Memory Pressure): COMPLETE — QMD interval → 15m, bun on PATH

## Post-Optimization State (2026-03-06)
- Disk: 26GB/38GB (68%) — was 75%
- RAM: 1.3GB/1.9GB, Swap: 844MB/2GB — swap improved from 1GB baseline
- OpenClaw: v2026.3.2 (updated from v2026.2.17)
- 24 cron jobs (all ok), 33 skills ready
- QMD: working, searchMode=search, 15m update interval (was 5m)
- Gateway: loopback bind (changed from tailnet — v3.2 security enforcement)

## Key Risks
- OpenClaw update (Wave 2) requires gateway restart — clears DM sessions, user must DM Bob after
- Plugin node_modules pruning (Wave 1.5) — verify plugins still load after removing @node-llama-cpp
- Cron frequency changes (Wave 3) — sync-voice-priorities from 5m->15m, tools-health-check from 5m->15m

## EC2 Access
- SSH: `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9`
- OpenClaw binary: `/home/ubuntu/.npm-global/bin/openclaw`
- Config: `~/.openclaw/openclaw.json`
