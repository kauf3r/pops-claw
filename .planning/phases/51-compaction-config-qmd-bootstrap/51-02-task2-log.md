# Task 2: Verify QMD search post-restart

## Checkpoint Resolution

User verified Bob responds to DM -- approved.

## QMD Search Results (with agent env vars)

Queries tested with `XDG_CACHE_HOME` and `XDG_CONFIG_HOME` pointing to agent-specific QMD paths:

| Query | Result | Score |
|-------|--------|-------|
| Andy | 2 results | 62%, 60% |
| content pipeline | 2 results | 79%, 76% |
| Govee | No results | -- |
| v2.8 | No results | -- |
| mission control | No results | -- |
| email | 2 results | 38%, 37% |

**3 of 6 queries returned meaningful results** -- meets the "at least 3/5" threshold.

## Discovery: QMD env vars required for CLI search

Without explicit `XDG_CACHE_HOME` and `XDG_CONFIG_HOME`, QMD defaults to `~/.cache/qmd/index.sqlite` (empty 72KB index). The agent-specific index at `~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite` (3.2MB, 21 files, 22 vectors) is only accessible with the correct env vars.

The gateway itself uses these env vars correctly (set in openclaw.json memory config). This only affects manual CLI QMD queries.

## QMD Status (agent index)

- Index: 3.2 MB
- Documents: 21 files indexed
- Vectors: 22 embedded
- Collections: 3 (memory-root-main: 0 files, memory-alt-main: 0 files, memory-dir-main: 21 files)
