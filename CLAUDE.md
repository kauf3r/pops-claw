# pops-claw — Operating Manual

Ops and planning repo for **Bob**, a proactive AI companion running on OpenClaw (v2026.4.1 as of the last documented upgrade — confirm current version in `progress.md`) on an AWS EC2 Ubuntu host, Tailscale-only (`100.72.143.9`), gateway on port 18789, agents in a Docker sandbox. Bob runs a 7-agent system (Andy/Scout/Vector/Sentinel + Quill/Sage/Ezra), ~25 cron jobs, 6 SQLite databases, an autonomous content pipeline, Resend email, and a Next.js Mission Control dashboard at `~/clawd/mission-control/` on EC2. **The deployment lives on EC2 — this repo holds the planning state (`.planning/`, GSD-managed), runbooks, solution docs, research briefs, and Mac-side sync scripts.** Milestone v2.11 "Knowledge Brain" (gbrain + PGLite) is executing; v2.12 "Research Pipeline Modernization" is planned. Read this file fully before your first change; when it conflicts with your defaults, this file wins.

## The Gates (non-negotiable)

1. **Read `.claude/napkin.md` before any other task action.** This is a napkin-logged correction (2026-05-25): a session started executing before reading it. Don't repeat it.
2. **There is no CI and no test suite.** Nothing here compiles or runs in CI — the only verification that exists is a real command you ran and whose output you actually read. For any claim about EC2 state ("cron fixed", "gateway healthy", "data syncing"), show the SSH command output. Never report done from memory or inference.
3. **Never push to `main`.** PR-only policy, active since 2026-05-14 (`docs/handoffs/2026-05-14.md`, Decisions). Branch off `origin/main` after `git fetch origin`, push the branch, open a PR.
4. **Never `git add -A` or `git add .`** The working tree routinely carries dozens of untracked iCloud-duplicate files (`name 2.md` pattern) and local state. Stage files by explicit path only.
5. **`.claude/` is gitignored** (as are `AGENTS.md`, `yolo-dev/`, `scripts/*.log`). New skills, commands, or napkin updates need `git add -f` to be committed. `.planning/` IS tracked in this repo — commit planning state normally.
6. **Back up before editing any config on EC2.** Pattern in use: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-$(date +%Y%m%d-%H%M%S)`. Never read and rewrite a file in the same expression (`open(p,'w')` truncates before the read runs). Read into a variable, then write. After any `openclaw.json` change: `systemctl --user restart openclaw-gateway` and verify in `journalctl --user -u openclaw-gateway`.
7. **State the plan and get confirmation before destructive or multi-service EC2 changes** (deployment configs, database operations, service disables, deletes). This is a long-standing rule in this repo.
8. **Document every EC2 intervention in `progress.md`** (session log) and, for solved failures, a solution doc under `docs/solutions/`. The next session has no memory of what you did on the server — the repo is the memory.

## Architecture Map

**This repo (Mac side):**

| Where | What |
|---|---|
| `.planning/` (STATE.md, ROADMAP.md, PROJECT.md, phases/) | GSD planning state — tracked in git here. STATE.md can lag reality; trust git log + phase SUMMARYs |
| `progress.md` | Session log, error tracking, EC2 intervention records — append after every phase or incident |
| `findings.md` | Research, root causes, technical decisions |
| `task_plan.md`, `REQUIREMENTS.md`, `USAGE.md`, `README.md` | v1-era docs — partially stale (see Mistake #4) |
| `docs/solutions/{runtime-errors,integration-issues}/` | Solved-failure forensics with frontmatter — check here BEFORE debugging anything |
| `docs/handoffs/` | Session handoffs |
| `research-briefs/` | Briefs synced from EC2 via `scripts/sync-research-briefs.sh` (rsync + YAML-frontmatter bridge to LLM-context KB) |
| `scripts/` | Mac/EC2 sync scripts: `sync-research-briefs.sh`, `sync-to-andyos.py` (growth/health → andyOS Postgres), `sync-voice-priorities.sh`, `process-voice-notes.py`, `com.claude.bob-healthcheck.plist` (launchd, 15-min) |
| `.claude/commands/ops.md` | `/ops` — full 10-check EC2 health report over one SSH connection |
| `LLM-context` (symlink) | Read-only knowledge base — see KB Access below |

**The deployment (EC2 + VPS):**

| Where | What |
|---|---|
| `ubuntu@100.72.143.9` via `~/.ssh/clawdbot-key.pem` | EC2 host (Tailscale-only). Non-interactive SSH needs full paths, e.g. `/home/ubuntu/.npm-global/bin/openclaw` |
| `~/.openclaw/openclaw.json` | Main config: agents, `agents.defaults.sandbox.docker.binds`, env, hooks, crons. Legacy `~/.clawdbot/` paths are symlinks to `~/.openclaw/` |
| `openclaw-gateway.service` (systemd **user** service) | The gateway. Binds the tailnet IP (not loopback) — CLI commands need `gateway.remote.url: ws://100.72.143.9:18789` in config or they fail with 1006 abnormal closure |
| `~/clawd/` | Bob's workspace: agent dirs, protocol docs (CONTENT_TRIGGERS.md, GROWTH_COMPANION.md, MEMORY.md), scripts |
| `~/clawd/db/` | **Canonical database directory** — health.db, coordination.db, content.db, email.db, observability.db, yolo.db, gbrain PGLite. Bind-mounted to `/workspace/db/` in the sandbox |
| `~/clawd/mission-control/` | Next.js 14 dashboard, port 3001 (Tailscale direct), WAL-mode read-only SQLite reads, SWR 30s polling |
| VPS 165.22.139.214 (Tailscale 100.105.251.99) | DigitalOcean: Caddy + n8n webhook relay for inbound Resend email |
| GCP project `pops-claw-oauth` | Current OAuth project. `rock-range-485422-h3` is stale, `vertical-ratio-485421-t4` retired — see Mistake #13 |

## Mistakes a Weaker Model Will Make Here (named, with the rule that prevents each)

1. **The wrong-database write.** A cron writes to `~/clawd/agents/main/*.db` (agent workspace, not sandbox-mounted) instead of canonical `~/clawd/db/*.db`. This bit twice: `oura-sync.py` ran "successfully" for 8 days while Bob saw stale health data, and the observability plugin hid 15,556 rows the same way (both fixed 2026-04-15, see `findings.md`). → Rule: all databases live in `~/clawd/db/`. When touching any DB path, verify it's the canonical one AND that the consumer actually sees new rows afterward.
2. **The config truncation.** Rewrites `openclaw.json` in the same expression that reads it, or edits with no backup, and bricks the gateway. → Rule: Gate #6 — timestamped backup, read-then-write (the repo's proven pattern is a small Python `json.load` → modify → `json.dump` script, see `docs/solutions/runtime-errors/docker-duplicate-mount-point-tmp.md`), restart, verify journal.
3. **The bind-mount assumption.** Assumes a bind-mount "just works": a `/tmp` bind conflicted with OpenClaw's auto-mounted tmpfs after an upgrade and killed EVERY isolated cron ("Duplicate mount point: /tmp"); content.db showed 0 bytes for one agent while others read it fine (mount shadowing, never fully resolved); isolated cron sessions use a virtual sandbox and need EXPLICIT binds in `openclaw.json`; nested bind-mounts are unreliable in cron sessions. → Rule: never bind reserved paths (`/tmp`, `/dev`, `/proc`, `/sys`); verify a new mount from ALL agents that need it, including an isolated cron session, not just the first one tested. Use the `sandbox-bind-mount` skill.
4. **The legacy-doc trust fall.** Quotes `USAGE.md`/`README.md` as current: they say `clawdbot-gateway`, `~/.clawdbot/` config, "gateway binds loopback" — all superseded (service is `openclaw-gateway`, config is `~/.openclaw/`, gateway binds the tailnet IP since Phase 20). `AGENTS.md` says to use beads (`bd`) — Andy migrated off beads; work tracking is GSD in `.planning/`. → Rule: `progress.md`, `.planning/`, and `docs/solutions/` are current; `USAGE.md`/`README.md`/`task_plan.md`/`AGENTS.md` are v1-era history.
5. **The local-verification illusion.** Declares an EC2 fix done after editing a doc in this repo, or "tests" something locally when the system under change runs on the server. → Rule: this repo deploys nothing. Every functional claim needs SSH evidence (Gate #2). Phase 48 established "verification backfill via live SSH evidence" as the standard.
6. **The stale-STATE trust.** Reads `.planning/STATE.md` ("Phase 58: 1/2 plans") and re-plans work that's already done — git has `feat(58-02)` commits completing the sandbox verification. → Rule: before any milestone/phase operation, `git fetch origin` and cross-check STATE.md against `git log --oneline` and the phase's SUMMARY files. Git wins.
7. **The free cron.** Adds or speeds up a cron without registering that every run is an LLM invocation against Claude Pro rate limits. The 2026-04-15 token pass cut $60–120/month by reducing frequencies (andyos-sync 30m→4h) and downgrading "is there work?" checks to Haiku. → Rule: new crons default to Haiku unless reasoning is required; justify the frequency; batch gateway restarts (Phase 51 pattern: one restart for all config changes).
8. **The plain-channel Slack payload.** Writes a cron payload with a bare channel name; the gateway validates channel IDs at the tool-call level and delivery silently fails. → Rule: `channel:ID` format everywhere in cron payloads and session instruction files (enforced repo-wide in Phase 33-04). Keep systemEvent messages concise — point to a reference doc in the workspace (MEETING_PREP.md pattern) instead of inlining instructions.
9. **The stdout-polluted pipeline.** Adds a `console.log`/print (or lets token-refresh output leak) inside a function whose stdout is parsed as JSON — sync scripts then silently return zero results. → Rule: in any script that returns parsed data, stdout is sacred; log to stderr or a log file.
10. **The GSD-tooling debug spiral.** A GSD CLI command fails with module-not-found (e.g., `lib/test.cjs`) and the model starts debugging the tooling. → Rule: fall back immediately to reading/writing the planning files directly (CONTEXT.md, PLAN.md, STATE.md). Workflow order stands: discuss-phase → plan-phase → execute-phase → audit → complete-milestone; plan-phase requires the CONTEXT.md that discuss-phase produces.
11. **The sandbox sqlite3 reflex.** Tells Bob to run `sqlite3` inside the Docker sandbox — the CLI isn't there, and neither is better-sqlite3. → Rule: sandbox DB access is Python `sqlite3` (stdlib). Also inherited from Phase 58: a Bun-compiled binary using PGLite fails inside the sandbox (`ENOENT: /$bunfs/root/pglite.data`, electric-sql/pglite#414) — gbrain runs via Bun runtime bind-mount (Path B), not a compiled binary.
12. **The helpful systemd drop-in.** Adds a systemd hardening flag without checking the service supports it. A `WatchdogSec=60` drop-in SIGABRTed tailscaled every ~66s (~1440 restarts/day) because Tailscale doesn't emit sd_notify pings, replaying a 3-month logtail backlog into a 1.2GB syslog (`docs/solutions/runtime-errors/tailscaled-watchdog-sigabrt-flood.md`). → Rule: check `systemctl show <svc>` and existing drop-ins (`/etc/systemd/system/<svc>.service.d/`) before and after touching unit config; never add `WatchdogSec` to a service that doesn't sd_notify.
13. **The wrong GCP project.** Wires a Google integration against whichever GCP project turns up first. `hooks.gmail.topic` pointing at stale project `rock-range-485422-h3` made gmail-watcher fail on every boot (fixed 2026-05-25 by disabling push — polling crons cover email). → Rule: the OAuth project is `pops-claw-oauth`; before touching Gmail/Calendar config, confirm topic/consumer project matches it. Ask which Google account before any OAuth flow.
14. **The ambiguous-entity guess.** Picks a booking owner, Vercel project, or company name when the reference is ambiguous. → Rule: ask for clarification instead of assuming — this is a standing communication rule in this repo.

## Quality Bar Per Deliverable (checkable, not adjectives)

**Any EC2 intervention:**
- [ ] Pre-change state captured (command output, config backup path noted)
- [ ] Change applied via backup → modify → restart → verify sequence; journal checked for errors
- [ ] Post-change verification shown (the thing that was broken now demonstrably works — next cron run, `gbrain doctor`, delivery in Slack, etc.)
- [ ] `progress.md` session entry appended; solution doc written under `docs/solutions/` if a failure was diagnosed (frontmatter: title, category, component, severity, date_solved, status, tags)

**Script change (this repo's `scripts/`):**
- [ ] `bash -n script.sh` (or `python3 -m py_compile script.py`) passes — output shown
- [ ] stdout stays parseable if any caller parses it (Mistake #9); logging goes to the script's `.log` file or stderr
- [ ] `set -euo pipefail` preserved in bash scripts; env vars validated with `${VAR:?missing}` (existing idiom in `sync-voice-priorities.sh`)
- [ ] If the script runs via launchd/cron, the schedule source (plist / crontab line) is named in the commit or doc

**Planning/GSD change:**
- [ ] STATE.md, ROADMAP.md checkboxes, and the phase dir agree with each other after the change
- [ ] Cross-checked against `git log` so completed work isn't re-planned (Mistake #6)

**Mission Control (dashboard on EC2) change:**
- [ ] TypeScript compiles (`tsc --noEmit` or the project's build) before committing — standing rule
- [ ] DB reads stay read-only WAL-mode; no writes from the dashboard

**PR:**
- [ ] Branch cut from `origin/main` after fetch; conventional-commit message
- [ ] Only intended files staged (explicit paths; `-f` for `.claude/` files); no iCloud `* 2.md` duplicates included
- [ ] PR body says what changed and how it was verified

## When Uncertain — Escalation Rules

**Resolve yourself, in this order (do not ask):**
1. `.claude/napkin.md` — corrections and preferences
2. `docs/solutions/` — is this failure already diagnosed? (partial matches count; the /tmp and content.db docs cross-reference each other)
3. `.planning/PROJECT.md` Key Decisions table + `.planning/STATE.md` Accumulated Context — decisions there are binding
4. `progress.md` and `findings.md` — the operational memory of every past intervention
5. `git log` + the relevant phase's PLAN/SUMMARY in `.planning/phases/`

**Stop and ask Andy (one concise question with your recommended default):**
- Any destructive EC2 operation: deleting data/backups, dropping DB tables, disabling services, `docker system prune` beyond dangling images, instance stop/resize
- Anything that changes spend or rate-limit pressure: new crons, frequency increases, model upgrades (Haiku→Sonnet/Opus)
- Security posture changes: opening ports, changing Tailscale/UFW rules, OAuth scopes, exposing anything publicly
- Email sending behavior (quota rules and the no-auto-reply policy are deliberate)
- Ambiguous entity references (Mistake #14)
- A conflict between the request and a PROJECT.md Key Decision — name the conflict, don't silently pick

**Failure protocol:** if SSH times out mid-investigation, remember tailscaled restarts kill your transport — wait and retry before assuming the instance is down (`/ops` has the escalation path). If a fix doesn't verify after 2 focused attempts, stop, write up what you saw in `progress.md`, and report the exact output.

## Knowledge Base Access

Andy's AI-maintained knowledge base (Karpathy second brain) is symlinked at `LLM-context` → `/Users/andykaufman/Desktop/Projects/claude-life-os/LLM-context/`.

1. Read `hot.md` for orientation, `_index.md` for structure
2. Grep `sources/`, `entities/`, `topics/` for specifics
3. **Read-only.** Never modify files under the wiki path. Citation format: `[[source:{page-name} §{Section Name}]]`

## Quick Reference

```bash
# SSH (Tailscale must be up on the Mac)
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9

# Health report (10 checks, one connection)
/ops   # command lives at .claude/commands/ops.md

# Gateway
systemctl --user status openclaw-gateway
systemctl --user restart openclaw-gateway
journalctl --user -u openclaw-gateway -n 50

# Ask Bob to do something (runs in his sandbox)
openclaw agent --agent main --message '...'
# full path for non-interactive SSH: /home/ubuntu/.npm-global/bin/openclaw
```
