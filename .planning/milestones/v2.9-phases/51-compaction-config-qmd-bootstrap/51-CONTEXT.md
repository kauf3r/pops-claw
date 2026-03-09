# Phase 51: Compaction Config & QMD Bootstrap - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Tune compaction thresholds (softThresholdTokens=8K, reserveTokensFloor=40K), configure hybrid search weights (vectorWeight=0.7, textWeight=0.3), bootstrap all QMD collections, restart gateway once, and verify everything works including a triggered compaction test. This is config-change-and-verify work on a live system.

</domain>

<decisions>
## Implementation Decisions

### Restart Procedure
- Batch all config changes (compaction thresholds + search weights) into openclaw.json, then run QMD bootstrap (qmd update && qmd embed), then single gateway restart
- Backup openclaw.json to openclaw.json.bak before any edits — 5-second revert if needed
- Restart during active session — pick a gap between heartbeat offsets (:08-:12 mark), user DMs Bob immediately after to re-establish session
- Avoid 5:50-6:10 AM PT and heartbeat windows (:00/:02/:04/:06)

### QMD Collection Scope
- Bootstrap all 3 auto-created collections (memory-root, memory-alt, memory-dir), not just memory-dir-main
- Even if root/alt are sparse now, they'll be ready for Phase 52 content seeding
- Keep searchMode as 'search' (BM25+vectors) — LLM reranker too slow for t3.small 2GB
- Keep update interval at 15 minutes — already tuned down from 5m in Phase 50

### Rollback Strategy
- Compaction loop regression (v2026.3.1 #32106): revert full config from .bak, restart gateway. QMD bootstrap persists independently.
- QMD bootstrap OOM: free memory first (stop mission-control service, kill Docker containers temporarily), retry QMD bootstrap, then restart everything
- Version risk (v2026.3.2 compaction loop status): unknown — check via journalctl during execution, revert if loop appears
- Document rollback procedure explicitly in the plan for executor clarity

### Verification Depth
- 6 verification checks total (5 success criteria + 1 compaction test):
  1. Config values verified via SSH read (softThresholdTokens=8K, reserveTokensFloor=40K)
  2. `qmd search "Andy"` returns non-empty results from memory-dir-main
  3. Gateway restart completes, Bob responds to Slack DM within 2 minutes
  4. Hybrid search weights (vectorWeight=0.7, textWeight=0.3) set in memorySearch config
  5. No compaction loop errors in journalctl for 30+ minutes post-restart
  6. Triggered test compaction: send Bob a long enough conversation to cross 8K tokens, watch journalctl for flush event
- QMD search tested with 3-5 queries: mix of system knowledge ("Andy", "content pipeline", "Govee") + recent events ("v2.8", "mission control")
- 30-minute soak test runs in background — proceed with QMD verification and compaction test in parallel
- Post-restart verification sequence: gateway status → Bob DM → QMD search queries → compaction trigger test → check background soak log

### Claude's Discretion
- Exact SSH command sequences and ordering
- journalctl grep patterns for compaction loop detection
- Test conversation content for triggering 8K token threshold
- Which services to stop for memory freeing if QMD OOMs
- Specific query terms for QMD verification beyond the decided mix

</decisions>

<specifics>
## Specific Ideas

- The compaction test is the proof that matters — config values being set is necessary but not sufficient
- Background soak + parallel QMD verification is the efficient approach — don't sit idle for 30 minutes
- If QMD bootstrap needs memory freeing, restart order: stop mission-control first (least critical), then Docker containers if needed

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- openclaw.json: central config file at ~/.openclaw/openclaw.json on EC2
- QMD CLI: v1.1.0 at ~/.bun/bin/qmd, models in ~/.cache/qmd/models/ (~1.5GB)
- QMD home per agent: ~/.openclaw/agents/<agentId>/qmd/
- Swap: 2GB at /swapfile — provides OOM headroom

### Established Patterns
- Config changes via SSH + jq or direct file edit
- Service management via systemctl --user (openclaw-gateway.service, mission-control.service)
- journalctl --user for service monitoring
- Post-restart: user DMs Bob to re-establish session

### Integration Points
- openclaw.json: compaction config at agents.defaults.compaction, memory search at agents.defaults.memorySearch
- QMD collections: auto-created at ~/.openclaw/agents/main/qmd/
- Gateway service: ~/.config/systemd/user/openclaw-gateway.service
- Mission Control service: mission-control.service (may need stopping for memory)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 51-compaction-config-qmd-bootstrap*
*Context gathered: 2026-03-08*
