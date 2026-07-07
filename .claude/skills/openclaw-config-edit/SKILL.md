---
name: openclaw-config-edit
description: Safely change ~/.openclaw/openclaw.json on the pops-claw EC2 host — bind-mounts, sandbox env vars, hooks, cron payloads, agent settings, gateway options. Use when asked to "edit openclaw.json", "change Bob's config", "add an env var to the sandbox", "disable a hook", "update a cron", or any change that requires a gateway restart.
---

# OpenClaw Config Edit — pops-claw EC2

`~/.openclaw/openclaw.json` on `ubuntu@100.72.143.9` is the single config for the gateway, all 7 agents, the Docker sandbox (binds/env), hooks, and crons. A bad write bricks Bob. This procedure is derived from changes that worked (gmail push disable 2026-05-25, /tmp bind removal 2026-03-22, gbrain env vars Phase 58) — follow it exactly.

## Procedure

```bash
SSH="ssh -i ~/.ssh/clawdbot-key.pem -o ConnectTimeout=10 ubuntu@100.72.143.9"
```

**1. Read the current state first.** Never edit from memory of what the config "should" contain:

```bash
$SSH 'python3 -c "import json; cfg=json.load(open(\"/home/ubuntu/.openclaw/openclaw.json\")); print(json.dumps(list(cfg.keys()), indent=2))"'
```

Drill into the section you're changing (e.g. `cfg["agents"]["defaults"]["sandbox"]["docker"]["binds"]`) and print it before deciding the edit.

**2. Timestamped backup (mandatory):**

```bash
$SSH 'cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-$(date +%Y%m%d-%H%M%S) && ls ~/.openclaw/openclaw.json.bak-*'
```

**3. Edit via Python, read-then-write** — the repo's proven pattern (see `docs/solutions/runtime-errors/docker-duplicate-mount-point-tmp.md`). NEVER `open(p,'w')` in the same expression that reads `p` — write mode truncates before the read runs:

```python
import json
with open("/home/ubuntu/.openclaw/openclaw.json") as f:
    cfg = json.load(f)
# ... modify cfg (e.g. filter binds, set env var, remove hooks block) ...
with open("/home/ubuntu/.openclaw/openclaw.json", "w") as f:
    json.dump(cfg, f, indent=2)
```

**4. Validate the result parses** before restarting:

```bash
$SSH 'python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null && echo VALID'
```

**5. Restart the gateway — once per batch.** Batch all related config changes into a single restart (Phase 51 decision: minimize disruption):

```bash
$SSH 'systemctl --user restart openclaw-gateway && sleep 5 && systemctl --user is-active openclaw-gateway'
```

**6. Verify in the journal** — look for the absence of the old error AND no new errors:

```bash
$SSH 'journalctl --user -u openclaw-gateway -n 60 --no-pager'
```

After OpenClaw upgrades specifically, watch for Docker mount errors in the first hour — new versions have changed container mount behavior before.

**7. Document in `progress.md`:** what changed, why, backup filename, verification evidence. The gmail-push entry (Session 2026-05-25) is the model — it even records the re-enable path.

## Known traps in this config

- **Reserved Docker paths:** never bind `/tmp`, `/dev`, `/proc`, `/sys` — OpenClaw auto-mounts `/tmp` as tmpfs and Docker rejects duplicates, killing ALL isolated crons at once. `dangerouslyAllow*` flags are a smell, not a fix.
- **Bind-mount changes:** use the `sandbox-bind-mount` skill — verification from all agents is required, not optional.
- **`gateway.remote.url` must stay `ws://100.72.143.9:18789`** — the gateway binds the tailnet IP, and CLI commands fail with 1006 abnormal closure without it.
- **Cron payloads:** Slack targets must be `channel:ID` format (gateway validates IDs at tool-call level; bare names fail silently). New crons default to Haiku; frequency changes alter real spend — ask Andy before increasing.
- **Hooks/GCP:** the OAuth project is `pops-claw-oauth`. Gmail push is deliberately disabled (stale-topic incident); polling crons handle email. Don't restore `hooks.gmail` without the documented re-enable path in `progress.md`.
- **Rollback:** restore the backup file and restart — that's the whole rollback plan, which is why step 2 is mandatory.
