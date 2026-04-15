# Phase 58: gbrain Infrastructure - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Install gbrain CLI on EC2, make it invocable from Bob's Docker sandbox with a working PGLite database and embedding capability. Bob can run `gbrain --version`, `gbrain doctor`, `gbrain add`, and `gbrain search` from inside the sandbox.

</domain>

<decisions>
## Implementation Decisions

### OpenAI API Key
- **D-01:** Use existing OpenAI API key or create a dedicated one on Andy's OpenAI account
- **D-02:** Key goes in `agents.defaults.sandbox.docker.env` as `OPENAI_API_KEY` (established env var pattern)
- **D-03:** Cost is negligible (<$0.10 for full wiki embed, fractions of a cent for daily incremental)

### RAM & Storage
- **D-04:** No RAM concern -- PGLite is transient (CLI invocation, not a daemon). ~50-100MB during invocation, released after exit. No impact on gateway's 1.1GB steady-state.
- **D-05:** Storage: ~100-200MB for ~200 wiki pages + embeddings. Trivial on 40GB gp3.
- **D-06:** Data directory: `~/clawd/db/gbrain/` on host, symlink from `~/.gbrain/` if gbrain doesn't support `--data-dir` or `GBRAIN_HOME`. Bind-mount to `/workspace/db/gbrain/` in sandbox.

### Installation Method
- **D-07:** npm global install on EC2 host: `npm install -g gbrain` (same pattern as OpenClaw binary at `/home/ubuntu/.npm-global/bin/gbrain`)
- **D-08:** Bind-mount binary path to `/usr/local/bin/gbrain` in Docker sandbox (same pattern as `gh`, `sqlite3`)
- **D-09:** If gbrain has additional runtime deps (e.g., PGLite native modules), bind-mount those too

### Embedding Model
- **D-10:** Use `text-embedding-3-small` ($0.02/1M tokens, 1536 dimensions) -- best cost/quality ratio for personal knowledge base
- **D-11:** Not text-embedding-3-large (4x cost, marginal quality gain) or ada-002 (legacy)

### Claude's Discretion
- Gateway restart timing and batching with other config changes
- Exact bind-mount paths if gbrain's directory structure requires adjustments
- Whether to use symlink or GBRAIN_HOME env var for data directory (pick whichever gbrain supports)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### OpenClaw Configuration
- `~/.openclaw/openclaw.json` on EC2 -- sandbox bind-mount config, env vars, agent defaults
- `.planning/codebase/ARCHITECTURE.md` -- Docker sandbox architecture, bind-mount patterns

### Infrastructure
- `.planning/REQUIREMENTS.md` -- INFRA-01 through INFRA-04, HEALTH-02 requirements
- `.planning/PROJECT.md` §Infrastructure -- EC2 specs, Tailscale IP, workspace paths

### Established Patterns
- `.planning/codebase/CONVENTIONS.md` -- naming, error handling conventions
- Existing bind-mount examples: `gh` binary, `sqlite3` binary, `~/clawd/db/` directory mount

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **npm global bin pattern**: OpenClaw itself installed at `/home/ubuntu/.npm-global/bin/openclaw` -- gbrain follows same path
- **Docker bind-mount config**: `openclaw.json` has established `binds` array pattern for sandbox file access
- **Env var injection**: `agents.defaults.sandbox.docker.env` section in openclaw.json for sandbox environment variables

### Established Patterns
- **Binary bind-mount**: Read-only mount of host binary into sandbox (e.g., `gh:ro`, `sqlite3:ro`)
- **Directory bind-mount**: Read-write mount of data directories (e.g., `~/clawd/db/:rw`)
- **Symlink for canonical paths**: `~/clawd/research.db` and `~/clawd/coordination.db` symlinked to `~/clawd/db/`
- **systemd user service**: Gateway runs as `openclaw-gateway.service`, restart required for bind-mount changes

### Integration Points
- `openclaw.json` bind-mount configuration (add gbrain binary + data dir)
- `agents.defaults.sandbox.docker.env` (add OPENAI_API_KEY)
- Gateway service restart after config changes
- `gbrain doctor` as post-install verification

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches following established EC2/sandbox patterns.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 58-gbrain-infrastructure*
*Context gathered: 2026-04-15*
