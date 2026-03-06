# Phase 50: Thursday Optimization — PLAN

## Wave 1: Disk Cleanup (safe, no restarts)

### 1.1 Clear NPM cache
- `npm cache clean --force` (~915MB)
- Verify: `du -sh ~/.npm`

### 1.2 Vacuum journal logs
- `sudo journalctl --vacuum-size=200M` (~1.6GB)
- Verify: `journalctl --disk-usage`

### 1.3 Remove unused Docker images
- `docker rmi node:20-slim clawdbot-sandbox:bookworm-slim` (~410MB)
- Verify: `docker images`

### 1.4 Clean old OpenClaw logs
- `rm -rf /tmp/openclaw/ /tmp/openclaw-1000/` (~28MB)
- Verify: `ls /tmp/openclaw*`

### 1.5 Prune plugin node_modules (INVESTIGATED)
Both plugins ship full `openclaw` + `node-llama-cpp` + `@node-llama-cpp` inside their own node_modules:
- secureclaw: 1.4GB (677MB @node-llama-cpp, 91MB openclaw, 62MB @napi-rs, 38MB pdfjs-dist...)
- observability-hooks: 1.3GB (677MB @node-llama-cpp, 85MB koffi, 78MB openclaw...)
The @node-llama-cpp binaries (677MB each = 1.35GB total) are duplicates of what QMD already has.
- `cd ~/.openclaw/plugins/secureclaw && npm prune --production 2>/dev/null; rm -rf node_modules/@node-llama-cpp`
- `cd ~/.openclaw/plugins/observability-hooks && npm prune --production 2>/dev/null; rm -rf node_modules/@node-llama-cpp`
- Verify plugins still load: `openclaw skills list | grep secureclaw`
- Expected savings: ~1.4GB (the llama-cpp binaries are unused by these plugins)

### 1.6 Verify disk after cleanup
- Target: below 65% usage (reclaim ~4GB minimum)
- `df -h /`

---

## Wave 2: OpenClaw Update (requires gateway restart)

### 2.1 Pre-update snapshot
- `openclaw --version` (expect 2026.2.17)
- `openclaw cron list` (save state)
- `openclaw skills list | grep ready | wc -l`

### 2.2 Install update
- `npm install -g openclaw@latest`
- `openclaw doctor --fix`
- Verify: `openclaw --version` (expect 2026.3.2)

### 2.3 Restart gateway
- `systemctl --user restart openclaw-gateway.service`
- Wait 5s, verify: `systemctl --user status openclaw-gateway.service`
- NOTE: DM sessions will be cleared — user must DM Bob to re-establish

### 2.4 Post-update verification
- `openclaw skills list | grep ready | wc -l` (should be >= 32)
- `openclaw cron list` (all 24 jobs still ok)
- Verify QMD backend still active (search test)
- Verify AgentMail config survived update

---

## Wave 3: Cron Pruning

### 3.1 Remove redundant memory reindex crontab
- QMD now handles indexing every 5m
- Remove: `0 */6 * * * ... openclaw memory index --force`
- Edit crontab: `crontab -e` (or `crontab -l | grep -v "memory reindex" | crontab -`)

### 3.2 Reduce sync-voice-priorities.sh frequency (RECOMMENDATION: keep, reduce to 15min)
Pulls tasks + recent voice note analyses from voice-memory-v2 Supabase into ~/clawd/agents/main/PRIORITIES.md.
This is NOT redundant with voice-notes-processor (which handles Drive -> Whisper -> coordination.db).
sync-voice-priorities feeds Bob's context with user priorities from the Supabase app.
However, every 5min is excessive — priorities don't change that fast.
- Change crontab from `*/5 * * * *` to `*/15 * * * *`
- Verify: `crontab -l | grep sync-voice`

### 3.3 Keep both health checks, reduce tools-health-check to 15min (RECOMMENDATION)
They serve different purposes:
- health-check.sh (~/clawd/scripts/) — lightweight: gateway up? disk? memory? Writes to health.log.
- tools-health-check.sh (~/scripts/) — heavier: checks CLI versions, plugin dirs, script mtimes.
  Writes JSON to mission-control/public/tools-health.json for dashboard display.
Both every 5min is overkill. tools-health-check rarely changes (versions, paths).
- Change tools-health-check from `*/5 * * * *` to `*/15 * * * *`
- Keep health-check.sh at 5min (lightweight, monitors real-time issues)
- Verify: `crontab -l | grep health`

### 3.4 Verify crontab after changes
- `crontab -l` — confirm only active, non-redundant jobs remain

---

## Wave 4: Memory Pressure Reduction

### 4.1 Increase QMD update interval
- Change `memory.qmd.update.interval` from "5m" to "15m"
- Fewer QMD processes spawned, less RAM churn

### 4.2 Keep QMD for main/landos/rangeos/ops only (INVESTIGATED)
Memory file counts: main=20, landos=20, rangeos=16, ops=15, quill=0, sage=0, ezra=0.
Quill, sage, ezra have zero memory files — QMD indexes are empty (1.1MB each, negligible).
The real cost is QMD spawning embed/update processes for 7 agents vs 4.
- No config change needed now — empty indexes are harmless and tiny
- If memory pressure persists after other changes, revisit per-agent QMD disable

### 4.3 Add PATH for bun
- Add `export PATH="$HOME/.bun/bin:$PATH"` to ~/.bashrc
- Prevents wrapper issues and CUDA build error retries

### 4.4 Final health check
- `free -h` — verify swap usage reduced
- `df -h /` — verify disk target met
- `systemctl --user status openclaw-gateway.service` — running
- All 24 cron jobs ok
- Memory search working

---

## Verification Checklist
- [ ] Disk below 65% usage
- [ ] OpenClaw on v2026.3.2
- [ ] All 24 cron jobs status ok
- [ ] Skills count >= 32 ready
- [ ] QMD search returns results
- [ ] AgentMail config intact
- [ ] Gateway running, no errors in logs
- [ ] Swap usage reduced from baseline
- [ ] No redundant crontab entries
- [ ] Bun on PATH system-wide

## Resolved Questions
1. Plugin bloat: both bundle full @node-llama-cpp binaries (677MB each) they don't use. Safe to delete.
2. sync-voice-priorities.sh: NOT redundant — it syncs Supabase priorities, not voice files. Keep at 15min.
3. Both health checks serve different roles. Keep both, reduce tools-health-check to 15min.
4. QMD for all 7 agents: 3 have empty indexes (harmless). No change needed now.
