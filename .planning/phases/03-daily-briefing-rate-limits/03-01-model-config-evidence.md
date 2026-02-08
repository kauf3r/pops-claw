# 03-01 Model Routing & Session Config Evidence

## Model Aliases (verified on EC2)

```
Aliases (3):
- haiku -> anthropic/claude-haiku-4-5
- sonnet -> anthropic/claude-sonnet-4-5
- opus -> anthropic/claude-opus-4-5
```

## Model Status

```
Default       : anthropic/claude-sonnet-4-5
Fallbacks (1) : anthropic/claude-opus-4-5
Aliases (3)   : haiku, sonnet, opus
```

## Compaction Config (from openclaw.json)

```json
{
  "mode": "safeguard",
  "reserveTokensFloor": 24000,
  "memoryFlush": {
    "enabled": true,
    "softThresholdTokens": 6000,
    "prompt": "Write any lasting notes to memory/$(date +%Y-%m-%d).md; reply with NO_REPLY if nothing to store.",
    "systemPrompt": "Session nearing compaction. Store durable memories now."
  }
}
```

## Session Capping

- `agents.defaults.contextTokens`: 100000
- Note: `session.historyLimit` not valid in v2026.2.6; `contextTokens` provides token-based capping

## Verification Commands Run

- `openclaw models aliases list` -- 3 aliases confirmed
- `openclaw models status` -- default=sonnet, fallback=opus
- `openclaw models fallbacks list` -- opus confirmed
- Config JSON inspection confirmed all compaction settings

*Captured: 2026-02-08*
