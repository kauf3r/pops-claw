# 04-01 Config Changes Applied

Applied 2026-02-08T19:04Z to EC2 (100.72.143.9)

## Changes to ~/.openclaw/openclaw.json

### 1. GITHUB_TOKEN injected to sandbox env
```
agents.defaults.sandbox.docker.env.GITHUB_TOKEN = "gho_***"
```

### 2. ~~setupCommand~~ → bind-mount host binaries (REVISED)
setupCommand failed: sandbox has read-only filesystem (`/var/lib/apt/lists/partial` missing).
Fix: removed setupCommand, bind-mounted statically-linked `gh` and dynamically-linked `sqlite3` (all deps already in image).
```
agents.defaults.sandbox.docker.binds += "/usr/bin/gh:/usr/bin/gh:ro"
agents.defaults.sandbox.docker.binds += "/usr/bin/sqlite3:/usr/bin/sqlite3:ro"
```

### 3. Elevated exec enabled (host-tool fallback)
```json
tools.elevated = {
  "enabled": true,
  "allowFrom": { "slack": ["U0CUJ5CAF"] }
}
```

### 4. gh config bind-mounted into sandbox
```
agents.defaults.sandbox.docker.binds += "/home/ubuntu/.config/gh:/home/node/.config/gh:ro"
```

## Changes to ~/.openclaw/.env

Added `GITHUB_TOKEN=gho_***` for gateway process env.

## Gateway Status

Restarted and verified active (running) at 19:04:02 UTC.
Re-restarted at 19:08:37 UTC after bind-mount fix (setupCommand removed).
