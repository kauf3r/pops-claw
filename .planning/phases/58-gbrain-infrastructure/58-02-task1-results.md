# Task 1: Configure openclaw.json bind-mounts and env vars for gbrain sandbox access

## Results

**Path:** B (Bun runtime bind-mount -- Path A compiled binary failed per Plan 01)

### Bind-mounts added to `agents.defaults.sandbox.docker.binds`:
1. `/home/ubuntu/.bun/bin/bun:/usr/local/bin/bun:ro` -- Bun runtime
2. `/home/ubuntu/gbrain:/opt/gbrain:ro` -- gbrain repo (source code)
3. `/home/ubuntu/scripts/gbrain-wrapper.sh:/usr/local/bin/gbrain:ro` -- wrapper script
4. `/home/ubuntu/.gbrain:/home/node/.gbrain:rw` -- gbrain config directory

### Environment variables added to `agents.defaults.sandbox.docker.env`:
- `OPENAI_API_KEY`: Reused existing key from `skills.entries.openai-image-gen.apiKey`

### Config changes:
- `~/.gbrain/config.json` updated: `database_path` changed from host path (`/home/ubuntu/clawd/db/gbrain/brain.pglite`) to sandbox-compatible path (`/workspace/db/gbrain/brain.pglite`)
- NOTE: Host-side `gbrain` will need `--path ~/clawd/db/gbrain/brain.pglite` override since config now points to sandbox path

### Files created:
- `~/scripts/gbrain-wrapper.sh` -- 2-line wrapper: `#!/bin/sh` + `exec /usr/local/bin/bun /opt/gbrain/src/cli.ts "$@"`

### Gateway restart:
- `systemctl --user restart openclaw-gateway.service` -- active (running)
- Memory: 419.3M (peak), 11 tasks, all plugins loaded

## Verification
- [x] openclaw.json contains gbrain bind entries (3 matches)
- [x] OPENAI_API_KEY in env section (1 match)
- [x] `.gbrain:/home/node/.gbrain:rw` mount configured
- [x] config.json has `/workspace/db/gbrain/brain.pglite`
- [x] Gateway active after restart
- [x] Wrapper script exists and is executable
