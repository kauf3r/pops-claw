# 04-01 Config Changes Applied

Applied 2026-02-08T19:04Z to EC2 (100.72.143.9)

## Changes to ~/.openclaw/openclaw.json

### 1. GITHUB_TOKEN injected to sandbox env
```
agents.defaults.sandbox.docker.env.GITHUB_TOKEN = "gho_***"
```

### 2. setupCommand installs gh + sqlite3 in sandbox containers
```
agents.defaults.sandbox.docker.setupCommand = "apt-get update && apt-get install -y --no-install-recommends sqlite3 curl && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && apt-get update && apt-get install -y --no-install-recommends gh && rm -rf /var/lib/apt/lists/*"
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
