# Phase 58: gbrain Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-15
**Phase:** 58-gbrain-infrastructure
**Areas discussed:** OpenAI API key sourcing, RAM & storage budget, Installation method, Embedding model

---

## OpenAI API Key Sourcing

| Option | Description | Selected |
|--------|-------------|----------|
| Existing key | Use existing OpenAI API key from Andy's account | |
| Dedicated new key | Create a dedicated key for gbrain on Andy's OpenAI account | |
| Either (recommended) | Use existing or create dedicated -- cost is negligible either way | ✓ |

**User's choice:** Accepted recommendation -- use existing or create dedicated key, inject via sandbox env vars
**Notes:** Cost < $0.10 for full wiki embed. Key goes in agents.defaults.sandbox.docker.env as OPENAI_API_KEY.

---

## RAM & Storage Budget

| Option | Description | Selected |
|--------|-------------|----------|
| No concern (recommended) | PGLite is transient CLI, not a daemon. ~50-100MB during invocation only. | ✓ |
| Monitor closely | Add RAM monitoring and alerts | |

**User's choice:** Accepted recommendation -- no RAM concern, PGLite is transient
**Notes:** Storage ~100-200MB on 40GB gp3. Data dir at ~/clawd/db/gbrain/ following established pattern.

---

## Installation Method

| Option | Description | Selected |
|--------|-------------|----------|
| npm global (recommended) | Same pattern as OpenClaw. Binary at /home/ubuntu/.npm-global/bin/gbrain | ✓ |
| cargo install | Rust binary, different toolchain | |
| Pre-built binary | Download release artifact | |

**User's choice:** Accepted recommendation -- npm global install, bind-mount binary into sandbox
**Notes:** Follows established pattern (OpenClaw, gh, sqlite3).

---

## Embedding Model

| Option | Description | Selected |
|--------|-------------|----------|
| text-embedding-3-small (recommended) | $0.02/1M tokens, 1536 dims. Best cost/quality for personal KB. | ✓ |
| text-embedding-3-large | $0.13/1M tokens, 3072 dims. Overkill for ~200 pages. | |
| text-embedding-ada-002 | Legacy model, no reason to prefer. | |

**User's choice:** Accepted recommendation -- text-embedding-3-small
**Notes:** Total wiki embedding cost < $0.05. Daily incremental embeds are fractions of a cent.

---

## Claude's Discretion

- Gateway restart timing and batching
- Exact bind-mount paths if gbrain's directory structure differs
- Symlink vs GBRAIN_HOME env var for data directory

## Deferred Ideas

None -- discussion stayed within phase scope.
