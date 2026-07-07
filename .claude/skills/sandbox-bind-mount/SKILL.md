---
name: sandbox-bind-mount
description: Give Bob's Docker sandbox access to a new database, binary, directory, or env var on the pops-claw EC2 host. Use when asked to "bind-mount X into the sandbox", "Bob can't see a file", "add a database to the sandbox", "file shows 0 bytes in the sandbox", or when a new tool (like gbrain) must be invokable from inside agent sessions.
---

# Sandbox Bind-Mount — pops-claw

Bind-mounts are the #1 recurring failure domain in this deployment: the duplicate-`/tmp` outage, the content.db 0-byte shadowing, the health.db/observability.db wrong-path sagas, the yolo-dev explicit-bind fix, and the gbrain compiled-binary dead end were ALL mount problems. This skill encodes what those incidents taught.

## Placement rules (decide before touching config)

1. **Databases go in `~/clawd/db/` on the host** — the canonical DB directory, mounted to `/workspace/db/` in the sandbox. NEVER place a DB in an agent workspace (`~/clawd/agents/<agent>/`) — agent dirs are not mounted into other sandboxes, and crons writing there run "successfully" while every consumer sees stale data (health.db: 8 days silent; observability.db: 15,556 hidden rows).
2. **Never bind reserved container paths** (`/tmp`, `/dev`, `/proc`, `/sys`). OpenClaw auto-mounts `/tmp` as tmpfs; an explicit bind produces `Duplicate mount point: /tmp` and kills every isolated cron simultaneously.
3. **Avoid nested bind-mounts** — unreliable in isolated cron sessions (Phase decision: "Docker workspace subdirs over nested bind-mounts"). Mount a parent directory and use subpaths inside it.
4. **Isolated cron sessions need EXPLICIT binds.** They use a virtual sandbox that does not inherit everything interactive sessions see — add the bind to `agents.defaults.sandbox.docker.binds` in `openclaw.json` (yolo-dev precedent: "Explicit bind-mount for yolo-dev in openclaw.json").
5. **Binaries with runtime data:** a Bun-compiled binary embedding PGLite fails inside the sandbox (`ENOENT: /$bunfs/root/pglite.data` — electric-sql/pglite#414). The working pattern (Phase 58, gbrain) is Path B: bind-mount the Bun binary + the tool's repo + a wrapper script, e.g. binds matching `gbrain.*:/usr/local/bin/gbrain` and `.gbrain:/home/node/.gbrain`, with any required key in `agents.defaults.sandbox.docker.env` (Phase 58 reused the existing `OPENAI_API_KEY` from openclaw.json).

## Procedure

1. **Edit `openclaw.json` via the `openclaw-config-edit` skill** (backup → Python read-then-write → validate → single gateway restart → journal check). Binds live at `cfg["agents"]["defaults"]["sandbox"]["docker"]["binds"]` as `"host_path:container_path:rw"` strings.
2. **Verify from INSIDE the sandbox, not the host.** Ask Bob to check it:

```bash
ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 \
  '/home/ubuntu/.npm-global/bin/openclaw agent --agent main --message "Run: ls -la /workspace/db/ and report the exact output"'
```

3. **Verify from EVERY agent that needs it — and from an isolated cron session.** The content.db incident proved a mount can work for Quill and Sage while showing 0 bytes for Ezra in the same session. Do not sign off after testing one agent.
4. **Check for 0-byte shadows.** If the file is empty inside the sandbox but healthy on the host, you've hit the mount-shadowing bug (`docs/solutions/integration-issues/content-db-zero-bytes-in-docker-sandbox.md` — root cause suspected, not confirmed). Compare `docker inspect` mounts between a working and failing agent container; the sanctioned workaround is host-side access (Bob queries the host path directly).
5. **For DB access inside the sandbox, use Python `sqlite3`** — the `sqlite3` CLI and better-sqlite3 are not available in the container.
6. **Document:** append the change to `progress.md` (bind string, why, verification output). If you diagnosed a new failure mode, add a solution doc under `docs/solutions/`.

## Sign-off checklist

- [ ] Host path follows placement rules (canonical `~/clawd/db/` for DBs; no reserved paths; no nesting)
- [ ] Bind added to `openclaw.json` with timestamped backup taken
- [ ] Gateway restarted once; journal clean
- [ ] Verified from inside the sandbox via at least one real agent session AND one isolated cron path
- [ ] File is non-zero-size and readable/writable as intended from every consumer
- [ ] `progress.md` updated
