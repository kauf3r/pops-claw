---
title: "content.db appears as 0 bytes inside Docker sandbox despite valid bind-mount"
category: integration-issues
component: openclaw-sandbox
severity: medium
date_solved: 2026-02-24
status: workaround-applied
tags: [docker, bind-mount, sqlite, openclaw, sandbox, content-pipeline]
related_beads: [pops-claw-jpt]
affected_agents: [ezra]
---

# content.db appears as 0 bytes inside Docker sandbox despite valid bind-mount

## Symptom

Ezra (publisher agent) reports `/workspace/content.db` is 0 bytes inside the Docker sandbox. Cannot query articles for WordPress publishing. Other agents (Quill, Sage) successfully read/wrote the same database earlier in the same session.

Error context: `publish-check` cron fires, Ezra session starts, but article lookup returns nothing because content.db is empty in sandbox.

## Investigation Steps

1. **Checked host file** - `~/clawd/content.db` is 114KB, healthy, contains article #16 with status=approved
2. **Checked for 0-byte stubs** - No stub at `~/clawd/agents/ezra/content.db` (cleaned in Phase 33-01)
3. **Checked bind-mount config** - `openclaw.json` has `~/clawd/content.db:/workspace/content.db:rw` in `agents.defaults.sandbox.docker.binds`
4. **Checked Ezra agent config** - Empty object `{}`, no overrides
5. **Checked other agents** - Quill and Sage successfully used content.db in the same session (wrote article, reviewed/scored it)

## Root Cause

**Suspected: Docker mount ordering issue.** OpenClaw mounts the agent workspace directory (`~/clawd/agents/ezra/`) as a Docker volume to `/workspace/`. The bind-mount of `content.db` to `/workspace/content.db` may be shadowed by the workspace volume mount depending on Docker mount ordering.

Why Quill/Sage work but Ezra doesn't is unclear — may be related to timing, container reuse, or agent-specific Docker invocation differences. Needs deeper investigation with `docker inspect` on running containers.

**Not confirmed yet** — this is the leading hypothesis based on available evidence.

## Workaround

Bob queries content.db from the host-side path and publishes the article body directly to WordPress via REST API, bypassing the sandbox file access entirely.

```
# Bob's workaround: query host DB, publish directly
sqlite3 ~/clawd/content.db "SELECT body FROM articles WHERE id = 16;"
# Then use WordPress REST API to create draft
```

## Proper Fix (TODO)

1. Compare `docker inspect` output for Ezra vs Quill containers to identify mount differences
2. If workspace volume shadows bind-mounts, restructure: either mount content.db outside `/workspace/` or ensure bind-mounts take precedence
3. Alternatively, move content.db INTO agent workspace dirs (but this breaks single-source-of-truth)
4. Gateway restart may fix mount ordering temporarily

## Prevention

- When adding new bind-mounts to OpenClaw sandbox, verify they're accessible from ALL agents that need them, not just the first one tested
- Add a startup health check: each content agent verifies `SELECT count(*) FROM articles` returns > 0 before proceeding
- Monitor for 0-byte files in sandbox — the Phase 33-01 cleanup found stubs in quill/, ezra/, main/ but the underlying cause (mount shadowing) wasn't fully resolved

## Cross-References

- Phase 33-01: Cleaned 0-byte stubs from 3 agent workspaces (same symptom, different manifestation)
- v2.6 MEMORY.md: "content.db path fixed" and "Stale DB" entries
- Bead `pops-claw-jpt`: Tracking issue for proper fix
