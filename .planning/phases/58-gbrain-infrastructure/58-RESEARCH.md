# Phase 58: gbrain Infrastructure - Research

**Researched:** 2026-04-15
**Domain:** gbrain CLI installation, PGLite embedded Postgres, Docker sandbox bind-mounting
**Confidence:** MEDIUM (gbrain is new software -- v0.10.1, released April 2026 -- with sparse documentation and known build issues)

## Summary

gbrain is an open-source personal knowledge brain CLI by Garry Tan (MIT license, v0.10.1). It uses PGLite (embedded Postgres 17.5 via WASM) for local storage and OpenAI embeddings for vector search. The critical finding is that gbrain requires **Bun runtime** (not Node.js/npm), which contradicts the CONTEXT.md assumption of `npm install -g`. The `bun link` command creates a symlink at `~/.bun/bin/gbrain` that uses `#!/usr/bin/env bun` shebang, meaning Bun must be available at execution time. A compiled standalone binary (`bun build --compile`) embeds the Bun runtime but has a **known open bug** with PGLite's WASM data loading (`$bunfs/root/postgres.data` ENOENT -- electric-sql/pglite#414, oven-sh/bun#15032). The safest path is installing Bun on the EC2 host, cloning gbrain, running `bun install && bun link`, then bind-mounting both the Bun binary and the gbrain installation into the Docker sandbox.

Additionally, the success criteria reference `gbrain add` which does not exist -- the correct command is `gbrain put <slug>`.

**Primary recommendation:** Install Bun + gbrain via `git clone && bun install && bun link` on EC2 host. Bind-mount the Bun binary, gbrain repo, and `~/.gbrain/` data directory into the sandbox. Use `gbrain init --pglite --path ~/clawd/db/gbrain/brain.pglite` to store data in the established database directory. Try the compiled binary first (may work with PGLite 0.4.4); fall back to Bun runtime bind-mount if WASM loading fails.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01/D-02/D-03: OpenAI API key in `agents.defaults.sandbox.docker.env` as `OPENAI_API_KEY`
- D-04: No RAM concern -- PGLite is transient CLI, ~50-100MB during invocation
- D-05: Storage ~100-200MB on 40GB gp3, trivial
- D-06: Data directory: `~/clawd/db/gbrain/` on host, symlink from `~/.gbrain/` if needed. Bind-mount to `/workspace/db/gbrain/` in sandbox
- D-07: ~~npm global install~~ **CORRECTION:** gbrain requires Bun, not npm. Same spirit (global CLI install on host) but different toolchain
- D-08: Bind-mount binary path into Docker sandbox (same pattern as `gh`, `sqlite3`)
- D-09: If gbrain has additional runtime deps, bind-mount those too
- D-10/D-11: Use `text-embedding-3-small` for embeddings

### Claude's Discretion
- Gateway restart timing and batching
- Exact bind-mount paths if gbrain's directory structure requires adjustments
- Whether to use symlink or env var for data directory (pick whichever gbrain supports)

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | gbrain CLI installed on EC2 with PGLite engine and compiled binary | gbrain v0.10.1 via `git clone && bun install && bun link`. PGLite is the default engine via `gbrain init`. Compiled binary via `bun build --compile --target=bun-linux-x64` but has known WASM issue -- try first, fall back to Bun runtime. |
| INFRA-02 | gbrain binary bind-mounted into Docker sandbox at `/usr/local/bin/gbrain` | If compiled binary works: single file bind-mount. If Bun runtime needed: bind-mount Bun binary + gbrain repo + wrapper script. |
| INFRA-03 | `~/.gbrain/` directory bind-mounted into sandbox for PGLite database access | gbrain stores config at `~/.gbrain/config.json` and PGLite data at configurable path. Use `--path` flag on `gbrain init` to point to `~/clawd/db/gbrain/brain.pglite`. Bind-mount both `~/.gbrain/` (config) and `~/clawd/db/` (data, already mounted). |
| INFRA-04 | OpenAI API key available in sandbox environment for embeddings | `OPENAI_API_KEY` env var in `agents.defaults.sandbox.docker.env`. gbrain checks this env var at runtime (overrides config.json). |
| HEALTH-02 | `gbrain doctor` passes all checks after setup | Doctor runs 8 checks: resolver, skill conformance, DB connection, pgvector, RLS, schema version, embedding health, link integrity. `--fast` skips DB checks. Several checks (resolver, skills) require the gbrain source repo to be accessible. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Not a code repository** -- this is a planning/docs repo for configuring an EC2 instance
- All changes happen via SSH to EC2 (100.72.143.9)
- Sandbox filesystem is read-only -- use bind-mounts, not setupCommand
- Bind-mount directories, not individual .db files (WAL/SHM issue documented in MEMORY.md)
- Gateway restart required for bind-mount config changes (systemd user service)
- State plan and wait for confirmation before deployment config changes
- Use full path for non-interactive SSH commands

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| gbrain | v0.10.1 | Knowledge brain CLI with hybrid RAG | Only tool that matches project requirements (PGLite, CLI mode, OpenAI embeddings) |
| Bun | latest (1.2.x+) | JavaScript/TypeScript runtime | Required by gbrain -- not optional |
| PGLite | v0.4.4 (bundled) | Embedded Postgres 17.5 via WASM | gbrain's default engine, zero-config |
| OpenAI API | text-embedding-3-small | Vector embeddings (1536 dims) | Locked decision D-10 |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `gbrain doctor` | Health check (8 checks) | Post-install verification, ongoing monitoring |
| `gbrain init --pglite` | Database initialization | One-time setup |
| `gbrain put <slug>` | Create/update brain pages | Testing (note: NOT `gbrain add`) |
| `gbrain search <query>` | Keyword search (tsvector) | Testing retrieval |
| `gbrain query <question>` | Hybrid search (vector + keyword + RRF) | Full semantic search |
| `gbrain embed --stale` | Generate missing embeddings | After adding pages |
| `gbrain stats` | Database statistics | Verify page/embedding counts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bun runtime | Compiled binary (`bun build --compile`) | Standalone, no Bun needed in sandbox. BUT has known PGLite WASM loading bug (open issues). Try first as primary approach. |
| PGLite | Supabase Postgres | Better for multi-user, but requires external DB server (RAM constraint on t3.small) |
| text-embedding-3-small | text-embedding-3-large | 4x cost, marginal quality gain for ~200 pages |

**Installation (on EC2 host):**
```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc

# Install gbrain
git clone https://github.com/garrytan/gbrain.git ~/gbrain
cd ~/gbrain && bun install && bun link
gbrain --version  # verify: should print "gbrain 0.10.1"
```

## Architecture Patterns

### Installation Strategy (Two-Path Approach)

**Path A: Compiled Binary (try first)**
```bash
cd ~/gbrain
bun build --compile --target=bun-linux-x64 --outfile bin/gbrain-linux-x64 src/cli.ts
# Test: ./bin/gbrain-linux-x64 --version
# Test: ./bin/gbrain-linux-x64 init --pglite --path ~/clawd/db/gbrain/brain.pglite
# Test: ./bin/gbrain-linux-x64 doctor --fast
```
If all three pass, use the compiled binary for sandbox bind-mount (single file, no Bun needed in sandbox).

**Path B: Bun Runtime (fallback if Path A fails with WASM error)**
```bash
# The bun link already created ~/.bun/bin/gbrain -> ~/gbrain/src/cli.ts
# Need to bind-mount into sandbox:
# 1. Bun binary: ~/.bun/bin/bun -> /usr/local/bin/bun (ro)
# 2. gbrain repo: ~/gbrain -> /opt/gbrain (ro)
# 3. Wrapper script: creates /usr/local/bin/gbrain that calls bun
```

### Data Directory Layout
```
~/clawd/db/gbrain/              # Host path (follows established ~/clawd/db/ pattern)
├── brain.pglite/               # PGLite database directory (Postgres WASM data files)
│   ├── PG_VERSION
│   ├── base/
│   └── global/

~/.gbrain/                      # Config directory (gbrain hardcodes this)
├── config.json                 # Engine config: { engine: "pglite", database_path: "...", openai_api_key: "..." }
└── (brain.pglite symlink?)     # Default PGLite location -- redirect to ~/clawd/db/gbrain/brain.pglite
```

### Sandbox Bind-Mount Configuration (openclaw.json)

**Path A additions (compiled binary):**
```json5
// agents.defaults.sandbox.docker.binds (add to existing array)
"/home/ubuntu/gbrain/bin/gbrain-linux-x64:/usr/local/bin/gbrain:ro",
"/home/ubuntu/.gbrain:/home/node/.gbrain:rw",
// ~/clawd/db/ is already mounted to /workspace/db/ -- no additional mount needed for PGLite data
```

**Path B additions (Bun runtime):**
```json5
// agents.defaults.sandbox.docker.binds (add to existing array)
"/home/ubuntu/.bun/bin/bun:/usr/local/bin/bun:ro",
"/home/ubuntu/gbrain:/opt/gbrain:ro",
"/home/ubuntu/.gbrain:/home/node/.gbrain:rw",
// Plus a wrapper script at a bind-mounted path
```

**Environment variables (agents.defaults.sandbox.docker.env):**
```json5
"OPENAI_API_KEY": "sk-..."
```

### Config.json Setup
```json
{
  "engine": "pglite",
  "database_path": "/workspace/db/gbrain/brain.pglite",
  "openai_api_key": "will-be-overridden-by-env-var"
}
```
Note: The `database_path` in config.json used INSIDE the sandbox must use the sandbox path (`/workspace/db/gbrain/brain.pglite`), not the host path. The config.json at `~/.gbrain/config.json` on the host will have the host path; the bind-mounted version seen inside the sandbox may need adjustment.

**Critical detail:** gbrain's config directory is hardcoded to `~/.gbrain/` (resolves from `$HOME`). Inside the sandbox, `$HOME` is `/home/node/`, so the bind-mount target must be `/home/node/.gbrain:rw`.

### Anti-Patterns to Avoid
- **Individual file bind-mounts for PGLite**: PGLite creates multiple files in its data directory. Mount the directory, not individual files (same lesson as SQLite WAL/SHM).
- **npm install -g gbrain**: Will fail -- gbrain is not published to npm registry as a traditional npm package. It requires Bun and `bun link` from a git clone.
- **Using `gbrain add`**: This command does not exist. Use `gbrain put <slug>` to create pages.
- **Storing PGLite data in default ~/.gbrain/brain.pglite**: Would be outside the established ~/clawd/db/ directory convention. Use `--path` flag to redirect.
- **Mounting ~/.gbrain/ as read-only**: Config and PGLite lock files need write access. Use `:rw`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Wrapper script for gbrain in sandbox | Complex shell script with path resolution | Simple 2-line wrapper: `#!/bin/sh` + `exec /usr/local/bin/bun /opt/gbrain/src/cli.ts "$@"` | Minimizes debugging surface |
| PGLite data directory management | Custom symlink chains | `gbrain init --pglite --path <dir>` | gbrain handles schema init, file locking, extensions |
| OpenAI API key injection | Custom config file templating | `OPENAI_API_KEY` env var (gbrain reads it automatically) | Env var overrides config.json |
| Post-install verification | Manual SQL queries against PGLite | `gbrain doctor --json` | Checks 8 categories automatically |

## Common Pitfalls

### Pitfall 1: Compiled Binary + PGLite WASM Loading
**What goes wrong:** `bun build --compile` bundles PGLite's WASM data files into Bun's virtual filesystem (`$bunfs`), but PGLite tries to read them from actual filesystem paths, causing ENOENT errors.
**Why it happens:** Known open bugs: electric-sql/pglite#414, oven-sh/bun#15032. Filed against PGLite 0.2.12 + Bun 1.1.33, but not confirmed fixed in 0.4.4.
**How to avoid:** Try compiled binary first (it might work with newer PGLite). If ENOENT on postgres.data, immediately switch to Path B (Bun runtime bind-mount).
**Warning signs:** Error message containing `$bunfs/root/postgres.data` or `ENOENT`.

### Pitfall 2: Config Path Mismatch Between Host and Sandbox
**What goes wrong:** `~/.gbrain/config.json` contains host paths (e.g., `/home/ubuntu/clawd/db/gbrain/brain.pglite`) but inside the sandbox, the mounted path is different (`/workspace/db/gbrain/brain.pglite`).
**Why it happens:** gbrain writes absolute paths to config.json during `init`. The sandbox has different mount points.
**How to avoid:** Run `gbrain init` from INSIDE the sandbox (or with sandbox-compatible paths). Alternatively, create a separate config.json for sandbox use, or use the `GBRAIN_DATABASE_URL` environment variable if supported.
**Warning signs:** `gbrain doctor` passes on host but fails in sandbox with path errors.

### Pitfall 3: ~/.gbrain/ Home Directory Resolution in Sandbox
**What goes wrong:** gbrain resolves config from `$HOME/.gbrain/`. In OpenClaw's sandbox, `$HOME` is `/home/node/`, so config must be at `/home/node/.gbrain/`.
**Why it happens:** Hardcoded path resolution using Node/Bun's `os.homedir()`.
**How to avoid:** Bind-mount `~/.gbrain/` to `/home/node/.gbrain/` in sandbox config.
**Warning signs:** "Config file not found" or "Database not initialized" errors when running gbrain in sandbox.

### Pitfall 4: PGLite Concurrent Access Crashes
**What goes wrong:** Two gbrain processes try to access the same PGLite database simultaneously, causing an `Aborted()` crash.
**Why it happens:** PGLite is single-process (WASM limitation). gbrain implements file locking, but if lock isn't released cleanly, next invocation may fail.
**How to avoid:** gbrain is CLI-only (not a daemon), so concurrent access is unlikely. But ensure cron jobs don't overlap with manual invocations. If stale lock, delete the lock file.
**Warning signs:** `Aborted()` error or lock acquisition timeout.

### Pitfall 5: Docker Mount Ordering (Workspace Volume Shadowing)
**What goes wrong:** OpenClaw mounts the agent workspace directory as a volume to `/workspace/`. Additional bind-mounts targeting paths WITHIN `/workspace/` may be shadowed.
**Why it happens:** Docker mount ordering can cause volume mounts to override bind-mounts (documented in content.db 0-byte issue, Phase 33).
**How to avoid:** The `~/clawd/db/` directory bind-mount to `/workspace/db/` is an established working pattern. Ensure gbrain data goes INSIDE this already-mounted directory, not as a separate mount competing with the workspace volume.
**Warning signs:** Files appear empty or missing inside sandbox despite existing on host.

### Pitfall 6: gbrain doctor Skills/Resolver Checks
**What goes wrong:** `gbrain doctor` checks for skills directory and resolver health. If only the binary is mounted (not the full repo), these checks fail.
**Why it happens:** Doctor assumes access to the gbrain source tree (skills/ directory).
**How to avoid:** For Path A (compiled binary), use `gbrain doctor --fast` which skips filesystem checks. For Path B (full repo mount), all checks should pass. Alternatively, accept warnings on skill checks since Bob uses BRAIN_OPS.md protocol, not gbrain skills.
**Warning signs:** Doctor reports "resolver" or "skill conformance" failures.

## Code Examples

### gbrain init with custom PGLite path
```bash
# Source: garrytan/gbrain src/commands/init.ts
gbrain init --pglite --path ~/clawd/db/gbrain/brain.pglite --key "$OPENAI_API_KEY" --non-interactive
```

### gbrain doctor verification
```bash
# Source: garrytan/gbrain src/commands/doctor.ts
gbrain doctor --json
# Expected output: 8 checks, all "ok"
# Health score: 100 (baseline) - 20 per fail - 5 per warn

gbrain doctor --fast
# Skips database checks, runs filesystem-only checks
```

### Create and search a test page
```bash
# Source: garrytan/gbrain CLI docs
# Note: "add" does not exist -- use "put"
echo '---
type: person
title: Test Person
tags: [test]
---

This is a test page for verification.' | gbrain put test-person

gbrain embed test-person
gbrain search "test person"
gbrain query "who is the test person?"
```

### Wrapper script for Path B (Bun runtime in sandbox)
```bash
#!/bin/sh
# /usr/local/bin/gbrain -- wrapper for bun-based gbrain
exec /usr/local/bin/bun /opt/gbrain/src/cli.ts "$@"
```

### openclaw.json bind-mount additions
```json5
// In agents.defaults.sandbox.docker section:
{
  "binds": [
    // ... existing binds ...
    // Path A (compiled binary):
    "/home/ubuntu/gbrain/bin/gbrain-linux-x64:/usr/local/bin/gbrain:ro",
    // OR Path B (Bun runtime):
    "/home/ubuntu/.bun/bin/bun:/usr/local/bin/bun:ro",
    "/home/ubuntu/gbrain:/opt/gbrain:ro",
    "/home/ubuntu/scripts/gbrain-wrapper.sh:/usr/local/bin/gbrain:ro",
    // Both paths need:
    "/home/ubuntu/.gbrain:/home/node/.gbrain:rw"
    // ~/clawd/db/ -> /workspace/db/ already mounted
  ],
  "env": {
    // ... existing env vars ...
    "OPENAI_API_KEY": "sk-..."
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| npm install | Bun + git clone + bun link | gbrain v0.1+ (April 2026) | Cannot use npm global install pattern |
| Postgres server | PGLite (embedded WASM) | gbrain default | No external DB needed |
| CLI sqlite3 in sandbox | Python sqlite3 fallback | v2.8 (Phase 43) | Precedent: tools may need runtime adapters in sandbox |

**Deprecated/outdated:**
- `gbrain add` -- never existed. Use `gbrain put <slug>`.
- `gbrain doctor --fix` -- does not exist in current code. Doctor provides remedial commands but has no auto-fix flag.

## Open Questions

1. **Does compiled binary work with PGLite 0.4.4?**
   - What we know: Bug filed against PGLite 0.2.12 + Bun 1.1.33 (Nov 2024). gbrain uses PGLite 0.4.4 (March 2026 release). Architecture was refactored in v0.4.
   - What's unclear: Whether the WASM loading was restructured enough to fix the `$bunfs` path issue
   - Recommendation: Try `bun build --compile` on EC2 and test `gbrain init`. If ENOENT, switch to Path B. Budget 5 minutes for this test.

2. **What is $HOME inside the OpenClaw sandbox?**
   - What we know: Typical OpenClaw sandbox uses `/home/node/` (node user). Andy's setup may differ.
   - What's unclear: Exact user and home directory in the sandbox container
   - Recommendation: Check with `docker exec <container> env | grep HOME` or `cat /etc/passwd` before configuring bind-mounts.

3. **Config.json path translation**
   - What we know: gbrain writes absolute paths to `~/.gbrain/config.json` during init. Host and sandbox have different mount points.
   - What's unclear: Whether gbrain supports relative paths or env var override for database_path
   - Recommendation: Either run `gbrain init` from inside sandbox with sandbox paths, or manually edit config.json after init to use sandbox-compatible paths. `GBRAIN_DATABASE_URL` env var is for Postgres connections only, not PGLite paths.

4. **Bun version on EC2 vs sandbox compatibility**
   - What we know: Bun installs latest by default. gbrain doesn't specify minimum Bun version.
   - What's unclear: Whether the Bun binary from host works inside the sandbox Docker image (glibc compatibility)
   - Recommendation: Install Bun on EC2, verify the binary is dynamically linked against compatible glibc. OpenClaw sandbox uses bookworm-slim (Debian 12, glibc 2.36) which should be compatible.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Bun | gbrain runtime | TBD (install needed) | -- | Required, no fallback |
| git | gbrain clone | likely available | -- | -- |
| OpenAI API | Embeddings | TBD (key needed) | -- | Keyword-only search (no vectors) |
| Docker sandbox | Bind-mounts | available | -- | -- |
| ~/clawd/db/ mount | PGLite data | available | -- | -- |

**Missing dependencies with no fallback:**
- Bun must be installed on EC2 host (not currently present)

**Missing dependencies with fallback:**
- OpenAI API key: keyword search works without it, but vector search (the whole point) requires it

## Validation Architecture

> Validation for this phase is manual/SSH-based since changes happen on a remote EC2 instance, not in a local codebase with tests.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual SSH verification (no automated test framework -- this is an infrastructure config phase) |
| Quick run command | `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 'gbrain doctor --json'` |
| Full suite command | `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 'gbrain --version && gbrain doctor --json && echo "test" \| gbrain put test-verification && gbrain search "test" && gbrain embed test-verification'` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | gbrain CLI installed with PGLite | smoke | `gbrain --version` via SSH | N/A |
| INFRA-02 | Binary accessible in sandbox | smoke | SSH into EC2, `openclaw exec main -- gbrain --version` or equivalent | N/A |
| INFRA-03 | PGLite data accessible in sandbox | smoke | `gbrain doctor --json` from inside sandbox | N/A |
| INFRA-04 | OpenAI API key in sandbox env | smoke | `gbrain embed test-verification` from inside sandbox | N/A |
| HEALTH-02 | Doctor passes | smoke | `gbrain doctor --json` (health score = 100 or acceptable with skill warnings) | N/A |

### Wave 0 Gaps
None -- this is infrastructure configuration, not code. No test files or framework needed.

## Sources

### Primary (HIGH confidence)
- [garrytan/gbrain GitHub repo](https://github.com/garrytan/gbrain) - README, package.json, source code (init.ts, doctor.ts, config.ts, cli.ts, pglite-engine.ts)
- [gbrain INSTALL_FOR_AGENTS.md](https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md) - Official install instructions
- [gbrain GBRAIN_VERIFY.md](https://github.com/garrytan/gbrain/blob/master/docs/GBRAIN_VERIFY.md) - Verification checklist

### Secondary (MEDIUM confidence)
- [electric-sql/pglite#414](https://github.com/electric-sql/pglite/issues/414) - PGLite + Bun compile bug report
- [oven-sh/bun#15032](https://github.com/oven-sh/bun/issues/15032) - Bun-side issue for PGLite compile
- [PGlite v0.4 announcement](https://electric-sql.com/blog/2026/03/25/announcing-pglite-v04) - Architecture refactor details
- [OpenClaw sandbox documentation](https://docs.openclaw.ai/gateway/sandboxing) - Bind-mount format and security
- [OpenClaw configuration](https://docs.openclaw.ai/gateway/configuration) - openclaw.json format

### Tertiary (LOW confidence)
- [GBrain Setup Guide (vibesparking.com)](https://www.vibesparking.com/en/blog/ai/2026-04-11-gbrain-setup-guide/) - Third-party guide
- [GBrain overview (toolhunter.cc)](https://www.toolhunter.cc/tools/gbrain) - Feature summary

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM -- gbrain is well-documented but very new (v0.10.1, April 2026). PGLite + Bun compile compatibility is the main uncertainty.
- Architecture: MEDIUM -- bind-mount patterns are established in this project (11 milestones of precedent), but gbrain's Bun dependency adds a new element not previously encountered.
- Pitfalls: HIGH -- compiled binary WASM issue is well-documented with open GitHub issues. Path mismatch and mount ordering issues are documented from previous phases.

**Research date:** 2026-04-15
**Valid until:** 2026-04-22 (7 days -- fast-moving project, gbrain may release new versions)
