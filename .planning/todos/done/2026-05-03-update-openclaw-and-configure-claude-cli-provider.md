---
created: 2026-05-03T18:06:13.586Z
title: Update OpenClaw and configure claude-cli provider
area: tooling
files:
  - ~/.openclaw/openclaw.json
---

## Problem

OpenClaw v2026.4.1 doesn't support `agentRuntime.id` config key, which is required for proper Claude CLI backend routing. The legacy `claude-cli/model-name` format fails with `model_not_found` in the gateway model resolver. Current version is 24 releases behind (v2026.4.1 vs v2026.4.25+ stable).

Goal: Route interactive Sonnet/Opus sessions through Claude Max $200 subscription (already paying) instead of API extra usage billing. Saves ~$100/mo.

## Solution

1. **Update OpenClaw**: `npm update -g openclaw` (v2026.4.1 -> v2026.4.25+)
2. **Fix model config**: Revert primary from `claude-cli/claude-sonnet-4-6` back to `anthropic/claude-sonnet-4-6`
3. **Add agentRuntime**: `openclaw config set agents.defaults.agentRuntime.id "claude-cli"`
4. **Restart gateway**: `systemctl --user restart openclaw-gateway`
5. **Test**: `openclaw agent --agent main --message "test" --json`

### Already completed:
- Claude Code CLI installed on EC2 (`/home/ubuntu/.npm-global/bin/claude` v2.1.119)
- CLI authenticated (`claude login` done)
- Provider auth registered (`openclaw models auth login --provider anthropic --method cli`)
- Fallback set to `anthropic/claude-sonnet-4-5` (API, for when subscription cap hit)
- Heartbeat stays on `anthropic/claude-haiku-4-5` (API, pennies)
- Subagents stay on `anthropic/claude-haiku-4-5` (API, pennies)

### Open question:
`agentRuntime.id` at defaults level routes ALL anthropic calls through CLI/subscription including haiku heartbeats/crons. On Max $200 probably fine, but verify after testing whether per-agent runtime scoping is needed.

### Sources:
- docs.openclaw.ai/providers/anthropic
- github.com/openclaw/openclaw/issues/63316
- OpenClaw CHANGELOG (agentRuntime added in 2026.4.x series)
