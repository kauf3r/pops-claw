# Pitfalls Research

**Domain:** Autonomous overnight code generation ("YOLO Dev") added to existing resource-constrained OpenClaw multi-agent deployment
**Researched:** 2026-02-24
**Confidence:** HIGH (pitfalls derived from existing system constraints documented in MEMORY.md, production history across 6 milestones, web research on AI code generation failures and Docker sandbox risks, and Claude Pro 200 rate limit documentation)

> This file supersedes the v2.6-era PITFALLS.md which covered memory system improvements and dashboard polish.
> Those pitfalls (MEMORY.md curation, flush thresholds, gateway restart session loss, bootstrap truncation,
> LEARNINGS.md noise, per-agent memory DB queries) remain valid. This file covers v2.7 YOLO Dev: autonomous
> overnight builds on a 2GB RAM EC2 with Docker sandbox, 20 existing cron jobs, and Claude Pro 200 rate limits.

---

## Critical Pitfalls

### Pitfall 1: Overnight Build OOMs the EC2 Instance, Killing Gateway + All 20 Cron Jobs

**What goes wrong:**
The YOLO Dev build cron triggers overnight. Bob starts generating code, installing dependencies (pip install, npm install), and running the prototype. A Python build pulls in numpy/pandas/scipy (common for "wild idea" projects), and pip compilation spikes memory past the 2GB RAM + 2GB swap = 4GB total ceiling. The Linux OOM killer activates. Because the OpenClaw gateway has `OOMScoreAdjust=-900` on tailscaled and sshd but NOT on the gateway process itself, the OOM killer targets the gateway or Docker container. The gateway dies, taking all 20 cron jobs offline. The morning briefing at 6 AM PT doesn't fire. No one knows the system is down until Andy checks manually.

**Why it happens:**
The t3.small has 2GB RAM. The existing system at steady state uses: OpenClaw gateway (~300-500MB), Docker sandbox container (~200-400MB), Mission Control Next.js (~150-250MB), 5 SQLite databases, systemd services. That's already 700MB-1.2GB committed. A YOLO build that spawns subprocess for code execution, plus pip/npm dependency installation, plus the built application running -- all inside the Docker sandbox -- can easily consume the remaining 800MB-1.3GB and overflow into swap. Once swap is exhausted, OOM kills the highest-scoring process. The Docker container running the build has no memory limit set (based on existing configuration). The 2GB swapfile was added specifically to prevent OOM recurrence (MEMORY.md), but a build with heavy dependencies will blow through it.

**How to avoid:**
- Set Docker container memory limits via `agents.defaults.sandbox.docker` config or a YOLO-specific agent config: `--memory=1g --memory-swap=1.5g` to cap the build container at 1GB RAM + 500MB swap, leaving 1GB+ for the gateway and system services
- Restrict the YOLO build stack to lightweight dependencies: Python stdlib + `http.server` + single-file HTML. No numpy, no pandas, no heavy frameworks. Enforce this in the build skill instructions
- Add a pre-build memory check: `free -m | awk '/^Mem:/{if($7<500) exit 1}'` -- abort the build if less than 500MB available
- Add a disk space check: `df -BM / | awk 'NR==2{if(int($4)<2000) exit 1}'` -- abort if less than 2GB free
- Set `OOMScoreAdjust=500` on the YOLO build process (higher = killed first) so the OOM killer takes the build, not the gateway. The gateway already has systemd `Restart=always` but the build should be the sacrificial process
- Monitor with the existing health-check.sh script (runs every 5 min), which already alerts at <200MB available memory

**Warning signs:**
- `free -m` shows swap usage >50% during overnight hours
- health-check.sh logs memory warnings during YOLO build windows
- Docker container restarts visible in `docker ps` logs
- Morning briefing fails to deliver the day after a YOLO build
- `journalctl --user -u openclaw-gateway.service` shows OOM kills or unexpected restarts

**Phase to address:** Phase 1 (Infrastructure Setup) -- Docker memory limits and pre-build resource checks must be in place before any build runs

---

### Pitfall 2: YOLO Build Burns Through Claude Pro 200 Rate Limits, Starving Morning Briefing and All Daytime Crons

**What goes wrong:**
The overnight build starts at midnight PT. Bob generates an idea, writes code, hits an error, debugs it, rewrites, tests again -- a multi-turn agentic loop typical of coding tasks. Each iteration uses Sonnet (the default for complex tasks) with large context windows (code + error output + conversation history). By 3 AM, the build has consumed 15-20 Sonnet turns with 100K+ tokens each. The 5-hour rolling window hasn't expired. At 6 AM, the morning briefing fires -- also Sonnet -- and gets rate-limited. The briefing fails or runs on Haiku (if fallback is configured), producing a degraded output. Heartbeat crons for all 4 agents also contend for capacity. The AirSpace email monitor at 8 AM PT fails. The entire daytime cron schedule is degraded because the overnight build consumed the rate budget.

Claude Pro 200 (Max $200/mo) has a rolling 5-hour window with ~900 Opus or equivalent Sonnet messages. But the YOLO build can easily burn 30-50 Sonnet turns in a single session if it enters a debug-retry loop. The 5-hour window means tokens used at midnight are still counted at 5 AM -- exactly when morning crons start.

**Why it happens:**
Claude Pro 200 uses a rolling window, not a daily reset. The YOLO build naturally consumes heavy Sonnet/Opus tokens because code generation and debugging are the most token-intensive tasks. The existing 20 cron jobs assume rate limit capacity is available during their scheduled times. Adding a heavy overnight consumer creates contention that didn't exist before. There's no mechanism in OpenClaw to "reserve" rate limit capacity for specific cron jobs.

**How to avoid:**
- Run the YOLO build on Haiku, not Sonnet or Opus. Haiku is sufficient for generating small Python/HTML prototypes and has separate rate limit pools. The build skill should explicitly set `model: "haiku"` in the cron job configuration. This is the single most important mitigation
- Set a hard turn limit on the build session: max 15 turns. If the build isn't working after 15 iterations, it's not going to work. Log the failure and move on. This prevents the debug-retry spiral that burns tokens
- Schedule the build to START at 10 PM PT and COMPLETE by 2 AM PT (hard deadline). This leaves a 4-hour buffer before the 6 AM morning briefing, allowing the rolling window to partially expire
- Add a pre-build rate limit check: query remaining capacity before starting. If Sonnet capacity is below 50%, skip the build tonight. (This may require checking the `retry-after` header or tracking usage in yolo.db)
- Use `isolated: true` for the YOLO cron job so it doesn't share session context with other agents, keeping the context window smaller
- Log actual token usage per build in yolo.db for post-hoc analysis and tuning

**Warning signs:**
- Morning briefing arrives late or with degraded content (Haiku instead of Sonnet)
- `429 Too Many Requests` errors in gateway logs during 6-8 AM PT
- Heartbeat crons show increased `lastDurationMs` (waiting for rate limit retry)
- Observability.db shows elevated token counts during midnight-6 AM window
- YOLO build sessions exceeding 20 turns (debug spiral indicator)

**Phase to address:** Phase 2 (Build Pipeline Cron) -- model selection and turn limits must be defined before the first build runs

---

### Pitfall 3: Build Fills 13GB Free Disk, Corrupting SQLite Databases and Breaking Everything

**What goes wrong:**
The YOLO build generates code, installs dependencies, and stores build artifacts at `~/clawd/yolo-dev/`. Over 2-3 weeks of nightly builds, each build directory accumulates: Python virtualenv (~200MB-500MB with dependencies), node_modules (~100MB-300MB), generated code, build logs, and the built application. With no cleanup, 10-15 builds consume 3-8GB. Meanwhile, the 5 SQLite databases (health.db, coordination.db, content.db, email.db, observability.db) plus the new yolo.db are writing WAL files. When disk drops below 5% free, SQLite WAL checkpointing fails silently. New writes corrupt the WAL. The next gateway restart attempts to replay the corrupted WAL, destroying the database. Email.db, coordination.db, or content.db -- databases that took months to build -- are lost.

The EC2 has 40GB gp3 EBS with ~13GB free (55% used, per MEMORY.md). That's the starting point, not a comfortable buffer.

**Why it happens:**
Build artifacts are "temporary" but never get cleaned up because each build is a unique project. Nobody thinks to delete last week's YOLO builds. pip/npm dependency caches grow silently. Docker layer caches consume space. The build process has no awareness of disk space and no self-cleaning mechanism. SQLite is remarkably resilient to low-disk conditions up to the moment it isn't -- WAL corruption at 0 bytes free is catastrophic and usually unrecoverable without backups.

**How to avoid:**
- Implement a build retention policy FROM DAY ONE: keep only the last 5 builds, auto-delete older ones. The build cleanup should run as part of each build's teardown, not as a separate cron
- Set a per-build size budget: 500MB max per build directory. The build skill should check `du -sm` of the build directory and abort if it exceeds the limit
- Store build artifacts OUTSIDE the Docker sandbox bind-mount if possible, or at minimum in a dedicated `~/clawd/yolo-dev/` directory that's easy to find and clean
- Add disk space monitoring to the existing health-check.sh: warn at 70% used (12GB remaining), critical at 80% used (8GB remaining), abort YOLO builds at 85% (6GB remaining)
- Do NOT install pip/npm packages globally in the Docker container (read-only FS prevents this anyway). Use per-build virtual environments and clean them up with the build
- Run `sqlite3 <db> 'PRAGMA wal_checkpoint(TRUNCATE)'` weekly on all 6 databases to keep WAL files from growing unbounded
- Consider adding a `docker system prune -f` to a weekly maintenance cron to clean unused Docker layers

**Warning signs:**
- `df -h` shows >70% disk usage
- health-check.sh disk alerts in logs
- SQLite "database is locked" or "disk I/O error" in gateway logs
- `ls -la ~/clawd/yolo-dev/` shows more than 5 build directories
- WAL files (*.db-wal) growing beyond 10MB

**Phase to address:** Phase 1 (Infrastructure Setup) for disk monitoring thresholds; Phase 2 (Build Pipeline) for retention policy and per-build size limits

---

### Pitfall 4: Build Agent Enters Debug-Retry Infinite Loop, Running for Hours and Consuming All Resources

**What goes wrong:**
Bob generates a prototype, runs it, gets an error. The skill instructs Bob to "fix the error and try again." Bob fixes one error, introduces another. The fix-run-error cycle repeats 30, 50, 100 times. Each iteration consumes a full LLM turn (Sonnet-level tokens), writes more code to disk, and may spawn subprocesses that don't get cleaned up. After 3 hours, the build has consumed the entire rate limit, written 2GB of debug iterations to disk, and left orphaned Python/Node processes running in the Docker container. The build never produces a working prototype -- it just consumed resources until something else broke.

Research confirms this is the #1 failure mode for autonomous coding agents. Multi-turn AI agents frequently fall into "Loop Drift" -- misinterpreting termination signals, generating repetitive actions, or suffering from inconsistent internal state. AI-assisted code has 1.7x more issues than human-authored code, making debug loops more likely. Without guardrails, agents "drift from the original task, get stuck in infinite exploration cycles, or generate plausible-looking code that's fundamentally wrong."

**Why it happens:**
LLMs are optimistic. When told to "fix the error," Claude will always try -- it never says "this approach is fundamentally wrong, I should start over" or "I've tried 10 times and should give up." The agent has no concept of diminishing returns. Each retry feels like progress (the error message changed!) even when it's circular. The skill instructions say "build a working prototype" which the agent interprets as "keep trying until it works" rather than "try for 15 minutes then declare failure."

**How to avoid:**
- Hard turn limit: maximum 15 LLM turns per build. After 15 turns, the build MUST terminate regardless of state. Log the result (success, partial, or failed) and move on. This is the single most critical guardrail
- Hard time limit: maximum 30 minutes wall-clock time per build. Implement via `timeout 1800` on the cron job or a watchdog timer in the build skill
- "Same error" detection: if the agent encounters the same error message (or substantially similar) 3 times in a row, terminate the build as "stuck." Don't let it try a 4th time
- Scope the prototype to trivially achievable: single Python file under 200 lines, no external dependencies beyond stdlib, serve on localhost. If the idea requires complex dependencies, the idea is too ambitious for a YOLO build -- log it as a "future idea" and skip
- Log each iteration count in yolo.db: `iteration_count`, `errors_encountered`, `time_elapsed`. Review these metrics to tune the limits
- Kill orphaned processes after build completes: `pkill -f "python.*yolo"` or equivalent cleanup in the build teardown

**Warning signs:**
- yolo.db shows builds with >15 iterations
- Build duration exceeding 30 minutes in logs
- Same error appearing 3+ times in build logs
- Gateway memory/CPU spikes sustained for >1 hour overnight
- Orphaned processes visible in `docker exec <container> ps aux`

**Phase to address:** Phase 2 (Build Pipeline) -- turn limits and time limits are non-negotiable before the first build

---

### Pitfall 5: YOLO Build Cron Collides With Existing 20 Cron Jobs, Creating Cascading Failures

**What goes wrong:**
The YOLO build is scheduled at midnight PT (07:00 UTC). But the existing cron schedule has: anomaly-check running every 6 hours (likely fires near midnight UTC), heartbeat crons for 4 agents every 15 minutes, and the session pruning script at 04:00 UTC. The YOLO build starts at 07:00 UTC and runs for 30+ minutes. During that window, heartbeat crons for all 4 agents fire (at :00, :02, :04, :06). The gateway is processing the YOLO build's LLM session and simultaneously handling 4 heartbeat sessions. On a 2GB RAM system, 5 concurrent LLM sessions (even with Haiku heartbeats) overwhelm available memory. The gateway queues sessions, heartbeats timeout, the build's context is interrupted. Or worse: the build and a heartbeat both try to write to coordination.db simultaneously, and despite WAL mode, one gets a SQLITE_BUSY timeout.

**Why it happens:**
OpenClaw processes cron jobs through the gateway, which manages all agent sessions. The `maxConcurrent` parameter controls concurrent sessions per agent, but a YOLO build session competes with heartbeat sessions for the same gateway resources (RAM, CPU, LLM API calls). The existing 20 crons were designed for a system WITHOUT a long-running overnight build. Adding a 30-minute build session is fundamentally different from the existing pattern of brief cron jobs (heartbeats: ~2 minutes, briefings: ~5-10 minutes).

**How to avoid:**
- Disable heartbeat crons during the YOLO build window. Heartbeats at 2 AM serve no purpose -- nobody is reading Slack at 2 AM. Schedule the build for 2-4 AM PT (09:00-11:00 UTC) and disable heartbeats from 1:30 AM to 4:30 AM PT
- Alternatively, use a dedicated "yolo-builder" agent with its own session target. This prevents session contention with the main agent's DM sessions. The builder can be a minimal agent with no heartbeat cron, no Slack channel, just the build skill
- Set the YOLO cron to `isolated: true` so it creates a fresh session rather than injecting into an existing agent session. Isolated sessions are lighter weight and don't accumulate conversation history
- Verify `maxConcurrent` is set: if the gateway tries to run the YOLO build and 4 heartbeats simultaneously, ensure `maxConcurrent: 2` or similar to queue rather than crash
- Time the build to avoid the session prune at 04:00 UTC and any other system maintenance crons
- Add the YOLO cron to Mission Control's cron calendar page so it's visible alongside all 20 existing crons

**Warning signs:**
- Heartbeat crons showing "missed" or elevated duration during YOLO build hours
- Gateway logs showing "session queue full" or timeout errors during builds
- coordination.db SQLITE_BUSY errors during overnight hours
- Build cron firing at the same minute as another cron (visible in cron-jobs.json)
- Multiple agent sessions visible in `openclaw sessions` simultaneously

**Phase to address:** Phase 2 (Build Pipeline Cron) -- cron scheduling and concurrency limits must account for all 20 existing jobs

---

### Pitfall 6: Docker Read-Only Filesystem Prevents Build Execution, Build Skill Silently Fails

**What goes wrong:**
The build skill instructs Bob to "create a Python file, install dependencies, and run the prototype." Bob tries to write a file to `/workspace/yolo-dev/my-project/main.py`. The write succeeds because `/workspace/` is a bind-mount to `~/clawd/agents/main/` on the host. But then Bob tries to `pip install flask` -- which tries to write to `/usr/local/lib/python3/...` inside the Docker container. The sandbox filesystem is READ-ONLY. The pip install fails with a permission error. Bob tries to debug it (Pitfall 4 loop), doesn't understand the sandbox architecture, and wastes 10 turns trying to install packages before the turn limit kicks in. The build produces nothing.

Or worse: Bob tries to run `python3 /workspace/yolo-dev/my-project/main.py` but the Python binary in the Docker container is from the base image and doesn't have the packages Bob expected. The code imports `requests` -- not available in the sandbox. The same debug loop ensues.

**Why it happens:**
The Docker sandbox filesystem is read-only by design (documented in MEMORY.md: "Sandbox filesystem is READ-ONLY -- use bind-mounts for host binaries"). This is correct for security. But the YOLO build assumes a writable environment where the agent can install packages and run code. These two requirements conflict. The agent doesn't know about the sandbox architecture unless explicitly told. Even if told, Claude tends to "try anyway" when it thinks it knows a workaround (e.g., `pip install --user` or `pip install --target`).

**How to avoid:**
- Pre-install a curated set of packages in the Docker image that covers 90% of YOLO build needs: `python3`, `http.server` (stdlib), `json`, `sqlite3`, `flask` (lightweight), `requests`. Build a custom Docker image or extend the existing one
- OR: use `pip install --target=/workspace/yolo-dev/<project>/deps/` which writes to the bind-mounted writable path. Add `sys.path.insert(0, '/workspace/yolo-dev/<project>/deps/')` to the generated code. This is hacky but works within the sandbox constraints
- The build skill instructions MUST explicitly state: "The Docker sandbox is read-only. You can only write to /workspace/. Do not attempt to install packages globally. Use only standard library modules or pre-installed packages: [list]. If your idea requires packages not available, choose a different idea"
- For Python: venv creation inside `/workspace/` works: `python3 -m venv /workspace/yolo-dev/<project>/venv && /workspace/yolo-dev/<project>/venv/bin/pip install flask`. This keeps everything in the writable bind-mount
- Test the sandbox environment BEFORE deploying the build skill: SSH to EC2, exec into the Docker container, verify what packages are available and what paths are writable

**Warning signs:**
- Build logs showing "Permission denied" or "Read-only file system" errors
- yolo.db showing 100% failure rate on builds
- Build skill producing only failed builds with pip/npm install errors
- Agent repeatedly trying the same install command with minor variations

**Phase to address:** Phase 1 (Infrastructure Setup) -- sandbox environment must be verified and documented before the build skill is written

---

## Moderate Pitfalls

### Pitfall 7: Idea Generation Produces Stale or Repetitive Ideas After a Few Weeks

**What goes wrong:**
The YOLO build starts with an "idea generation" step where Bob picks a project idea. The first week's ideas are creative and varied. By week 3, Bob keeps generating variations of the same 5 themes: weather dashboard, task manager, personal finance tracker, habit tracker, portfolio site. The ideas feel stale because the LLM's "randomness" is constrained by: (1) the same system prompt context every night, (2) the same user interests described in the workspace, (3) no feedback loop from previous builds to avoid repetition.

**Why it happens:**
LLMs are stochastic but not truly random. Given the same prompt (system context + "pick a wild idea"), they'll generate from the same probability distribution. Temperature helps but doesn't prevent convergence over time. Without explicit "don't repeat these" instructions, the model has no mechanism to track what it's already built.

**How to avoid:**
- Store all previous ideas (built or not) in yolo.db and include the list of past ideas in the generation prompt: "You have already built: [list]. Generate a completely different idea"
- Include a "theme" rotation: weekday determines the category (Mon=data viz, Tue=game, Wed=automation tool, Thu=creative art, Fri=utility, Sat=API mashup, Sun=wild card). This forces variety
- Seed the prompt with external randomness: today's date, a random word from a word list, a recent headline. This shifts the probability distribution each night
- Allow manual idea injection: Andy can DM Bob with "Tonight build: [idea]" and the build cron checks for manual overrides before generating its own idea
- Set temperature to 1.0 (or max allowed) for the idea generation step only, not for the code generation step

**Warning signs:**
- yolo.db shows 3+ builds in the same category within a 2-week window
- Review of build names/descriptions shows obvious thematic repetition
- Andy stops finding the builds interesting (the whole point of YOLO Dev)

**Phase to address:** Phase 3 (Idea Generation + Build Skill) -- the skill design must include anti-repetition mechanics

---

### Pitfall 8: yolo.db Schema Design Prevents Useful Querying for Mission Control Dashboard

**What goes wrong:**
yolo.db is created with a minimal schema: `builds(id, name, status, created_at)`. The Mission Control `/yolo` page needs to display: build duration, lines of code, technology used, idea source, iteration count, error count, token usage, file manifest, whether the build is runnable. None of this data was captured. Retrofitting the schema requires migrating existing data or losing it. The dashboard shows a bare table with name and status -- not the rich, interesting display that makes YOLO Dev fun to monitor.

**Why it happens:**
Schema design happens in the infrastructure phase. Feature requirements come from the dashboard design phase. If these phases aren't coordinated, the schema captures what's easy to store (build start/end, pass/fail) rather than what's interesting to display. The "move fast" instinct says "we can add columns later" -- but SQLite ALTER TABLE only supports ADD COLUMN, not renames or type changes, and existing rows have NULL for new columns.

**How to avoid:**
- Design the yolo.db schema based on what the `/yolo` dashboard page needs to display, not what the build process naturally produces. Work backwards from the dashboard mockup
- Capture rich metadata from the start, even if some fields are initially unused:
  ```sql
  CREATE TABLE builds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    idea_source TEXT,        -- 'generated', 'manual', 'theme-rotation'
    theme TEXT,              -- category/theme
    status TEXT NOT NULL,    -- 'running', 'success', 'partial', 'failed'
    model TEXT,              -- 'haiku', 'sonnet'
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds INTEGER,
    iteration_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    lines_of_code INTEGER,
    tech_stack TEXT,         -- 'python', 'html', 'python+flask'
    artifact_path TEXT,      -- relative path to build directory
    artifact_size_bytes INTEGER,
    is_runnable BOOLEAN DEFAULT 0,
    serve_port INTEGER,      -- if the build runs a web server
    notes TEXT               -- agent's self-assessment
  );
  ```
- Include a `build_logs` table for per-iteration detail (iteration number, action taken, error message, tokens used)
- Add the yolo.db path to Mission Control's `db-paths.ts` on day one -- don't leave it for the dashboard phase

**Warning signs:**
- Dashboard `/yolo` page only shows name + status (boring, uninformative)
- Feature requests for "show me how many lines of code" or "show me the errors" that require schema changes
- yolo.db has only 3-4 columns after the build pipeline is complete

**Phase to address:** Phase 1 (Infrastructure Setup) for schema design; Phase 4 (Dashboard) for verification that schema supports all display needs

---

### Pitfall 9: Build Artifacts Become Unrunnable Immediately Because Bob Doesn't Test Them

**What goes wrong:**
Bob generates a Python web app, writes it to disk, declares "Build complete! Created a weather dashboard that serves on port 8080." Andy visits the `/yolo` page, sees the build, tries to run it. It crashes on import because Bob wrote `import flask` but Flask isn't installed in the environment where it needs to run. Or the code references a file path that only exists inside the Docker container. Or it hardcodes `localhost` but needs to bind to `0.0.0.0` to be accessible via Tailscale. The build is "complete" in yolo.db but not actually functional.

**Why it happens:**
AI-generated code has a known "looks done but isn't" problem. The code is syntactically correct and logically plausible, but wasn't actually executed end-to-end in the target environment. Bob wrote the code and maybe ran `python main.py` to see "server started," but didn't verify that the endpoint returns data or that the HTML renders correctly. The build skill says "build a prototype" -- Bob interprets this as "write the code" rather than "write and verify the code works."

**How to avoid:**
- The build skill MUST include a verification step: after writing code, run it, make an HTTP request to the endpoint (if it's a web app), and verify the response is non-empty. Only mark as `is_runnable: true` if verification passes
- For web apps: `curl http://localhost:<port>` and check for a 200 response. For CLI tools: run with `--help` or a test input and check exit code 0
- Include a "smoke test" template in the build skill: the agent writes a test script alongside the main code that exercises the primary function
- Don't rely on the agent's self-assessment ("I tested it and it works"). Require programmatic verification via exit code or HTTP response
- Store the smoke test result in yolo.db: `smoke_test_passed BOOLEAN, smoke_test_output TEXT`

**Warning signs:**
- yolo.db shows builds marked `is_runnable: true` that crash when actually run
- All builds are Python files that import unavailable packages
- Build artifacts reference paths that don't exist outside the Docker container
- Andy tries 5 builds, none of them work -- the feature feels broken

**Phase to address:** Phase 3 (Build Skill) -- verification step is part of the skill design, not an afterthought

---

### Pitfall 10: Gateway Restart for YOLO Config Changes Kills DM Sessions + Overnight Cron Delivery

**What goes wrong:**
Setting up YOLO Dev requires changes to `openclaw.json`: possibly adding a new agent, adding the build cron, setting Docker memory limits, adding yolo.db bind-mount. Each change requires a gateway restart. The restart clears DM sessions (documented repeatedly in MEMORY.md and prior PITFALLS.md). If the restart happens at 10 PM and the YOLO build cron fires at midnight, the build may try to deliver results to a DM session that no longer exists. The build output goes nowhere. Next morning, Andy checks the `/yolo` page and sees a "success" but no Slack notification.

**Why it happens:**
Same root cause as Pitfall 3 from the prior PITFALLS.md: gateway holds sessions in memory, restart clears them, cron delivery to DM channels fails silently. This is especially painful for YOLO Dev because the WHOLE POINT is to wake up and see what Bob built. If the notification doesn't arrive, the feature feels useless even if the build succeeded.

**How to avoid:**
- Batch ALL openclaw.json changes for YOLO Dev into a single restart
- Restart BEFORE the evening, then immediately DM Bob to re-establish the session
- The YOLO build cron should deliver to a Slack CHANNEL (e.g., #ops or a new #yolo-dev channel), NOT to a DM session. Channel delivery doesn't require an active DM session
- Use the `Channel:ID` format that was enforced in v2.6 for reliable delivery
- If DM delivery is desired, include a fallback: write a summary to a file in the workspace that the morning briefing can pick up and include in Section 10 (or a new section)

**Warning signs:**
- Build succeeds in yolo.db but no Slack message received
- `openclaw sessions` shows no active DM session after a restart
- Build cron logs show "ok" status but the delivery target session doesn't exist

**Phase to address:** Phase 1 (Infrastructure Setup) for the one-time config restart; Phase 2 (Build Pipeline) for delivery channel selection

---

### Pitfall 11: Security Risk -- Build Agent Generates Code That Accesses Host Resources or Leaks Credentials

**What goes wrong:**
Bob generates a "system monitoring dashboard" as a YOLO project. The generated code reads `/proc/meminfo`, scans environment variables (which contain API keys via the sandbox .env), and serves them on an HTTP endpoint. Or Bob generates a "file manager" that traverses the `/workspace/` directory and displays all files -- including `email-config.json`, `verified-bundle.json`, and other sensitive files in the agent workspace. The build runs on a port that's accessible via Tailscale (if Bob binds to 0.0.0.0).

Docker sandbox provides filesystem isolation, but the bind-mount at `/workspace/` contains sensitive operational files (API configs, OAuth tokens referenced in email.db, coordination data). The sandbox .env file is explicitly mounted as an environment source. A malicious or naive code generation could expose these.

**Why it happens:**
The agent has no concept of "sensitive data" when generating code. Code that reads environment variables or lists files is perfectly normal Python/Node. The Docker sandbox prevents host filesystem access but the bind-mounted `/workspace/` IS the agent's operational workspace containing real data. The existing `agents.defaults.sandbox.docker.env` list includes API keys that the agent legitimately needs for normal operation but shouldn't expose in a YOLO build.

**How to avoid:**
- The YOLO build should write to an isolated subdirectory: `/workspace/yolo-dev/<build-id>/`. The build skill instructions must say: "Only read and write files within your build directory. Do not access any files outside of it"
- Generated code should NEVER bind to 0.0.0.0. The build skill must instruct: "If creating a web server, bind to 127.0.0.1 only"
- Generated code should NEVER read environment variables. The build skill must instruct: "Do not use os.environ or process.env in generated code"
- Consider running the YOLO build in a separate Docker container with a more restrictive bind-mount (only `~/clawd/yolo-dev/`, not the full agent workspace). This requires a custom sandbox config for the YOLO agent
- SecureClaw's 15 behavioral rules should cover some of this, but verify that code generation is included in the rule set (it was designed for operational security, not generated code security)
- No YOLO build should be served on a port accessible outside localhost. If a build creates a web server, access it only via SSH tunnel, never via Tailscale direct

**Warning signs:**
- Generated code containing `os.environ`, `process.env`, or file path traversal
- Build serving on 0.0.0.0 or a high port visible via Tailscale
- Generated code reading files outside its build directory
- SecureClaw audit flagging code generation patterns

**Phase to address:** Phase 3 (Build Skill) for code generation constraints; Phase 1 (Infrastructure Setup) for isolated bind-mount if using a separate YOLO agent

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| No Docker memory limit on builds | Faster setup, no config needed | OOM kills gateway on first heavy build | Never -- set `--memory=1g` from day one |
| Run builds on Sonnet instead of Haiku | Better code quality | Burns rate limit budget, starves daytime crons | Only if explicit rate limit budget is tracked and the build is a special occasion |
| No build retention policy | Keep all builds for history | Disk fills in 2-3 weeks, SQLite corruption risk | Never -- auto-delete builds >5 from day one |
| Skip schema richness ("add columns later") | Faster initial DB setup | Dashboard shows boring data, schema migrations needed, NULLs in existing rows | First 48 hours of prototyping only; must finalize schema before first real build |
| No verification step in build skill | Builds "complete" faster | Builds are unrunnable, feature feels broken, user loses trust | Never -- verification is what makes YOLO Dev useful |
| DM delivery instead of channel delivery | Feels more personal | Restart kills session, build notifications silently lost | Only with a channel-delivery fallback |
| Build runs in main agent's session | No new agent needed | Build context pollutes main agent's conversation history, compaction issues | Never -- use `isolated: true` or a dedicated agent |
| No turn/time limit on builds | Agent "tries harder" | Debug spiral burns all resources, produces nothing | Never -- hard limits are the most critical guardrail |

---

## Integration Gotchas

Common mistakes when connecting YOLO Dev to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| yolo.db and Mission Control | Creating yolo.db but not adding it to `db-paths.ts` | Add yolo.db path to the DB singleton factory on day one, even before the dashboard page exists |
| YOLO cron and existing 20 crons | Scheduling without checking for time conflicts | Map all 21 crons on Mission Control's calendar page; verify no overlaps within a 15-minute window |
| Build skill and Docker sandbox | Assuming the agent can install packages freely | Explicitly document what's available in the sandbox; pre-install common packages in the Docker image |
| Build delivery and Slack | Using DM delivery like other crons | Use channel delivery (Channel:ID format) for reliability across gateway restarts |
| Build artifacts and disk space | Storing artifacts with no cleanup | Implement retention policy in the build teardown step, not as a separate maintenance cron |
| yolo.db and morning briefing | Not including build results in the briefing | Add a "YOLO Build" section to the morning briefing reference doc so Andy sees overnight results |
| Build agent and rate limits | Using the same model (Sonnet) as daytime crons | Use Haiku for builds to avoid contention with the Sonnet rate limit pool |
| Build logs and observability.db | Not connecting build sessions to the observability pipeline | Ensure the build cron's agent/session appears in observability.db so token usage is tracked |
| Docker memory limits and gateway | Setting container-level limits that also restrict the gateway | Memory limits should apply to the build process/container only, not to the gateway's Docker host settings |
| YOLO dashboard and SWR | Building the /yolo page without auto-refresh | Match existing SWR pattern (30s polling) so the page updates live during active builds |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No build retention + nightly builds | Disk fills at ~500MB/build/night = 3.5GB/week | Auto-delete oldest builds, keep last 5 | After 2-3 weeks (7-10GB consumed of 13GB free) |
| Build runs on Sonnet | Rate limit contention visible in morning briefing | Use Haiku for builds; reserve Sonnet for daytime | First morning after a heavy debug-loop build |
| No turn limit on debug loops | Build runs for 3+ hours, 50+ turns, all resources consumed | Hard cap at 15 turns and 30 minutes | First build that hits an error the agent can't fix |
| Single yolo.db with no indexing | Dashboard queries slow as build count grows | Add indexes on `status`, `created_at`, `theme` | After 100+ builds (~3-4 months) |
| Build process spawns subprocesses that aren't cleaned up | Docker container accumulates zombie processes, memory creep | Kill all child processes in build teardown | After 5-10 builds without cleanup |

---

## Security Mistakes

Domain-specific security issues for autonomous code generation in a Docker sandbox.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Generated code reads environment variables containing API keys | Keys exposed in build artifacts or served on HTTP endpoints | Build skill must explicitly forbid `os.environ`/`process.env`; consider a separate YOLO container without sensitive env vars |
| Build binds web server to 0.0.0.0 instead of 127.0.0.1 | Build accessible to anyone on the Tailscale network | Build skill must mandate `127.0.0.1` binding; post-build check for listening ports |
| Generated code traverses /workspace/ reading sensitive files | Operational configs, OAuth tokens, email data exposed | Isolate builds to `/workspace/yolo-dev/<id>/`; consider separate bind-mount for YOLO agent |
| Build output includes secrets in logs stored in yolo.db | API keys persisted in plaintext in build_logs table | Scrub logs for known secret patterns before storage; never log full environment |
| Build creates network connections to external services | Agent could hit rate limits on external APIs or leak data | Docker network restrictions or explicit build skill instructions to avoid external requests |
| Generated code writes to /workspace/ paths outside build directory | Could overwrite operational files (coordination.db, email-config.json, etc.) | Build skill must restrict writes to build directory; consider filesystem quota or chroot |

---

## UX Pitfalls

Common user experience mistakes for an overnight autonomous builder.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No notification when build completes | Andy wakes up not knowing if YOLO ran, has to check dashboard manually | Post to Slack channel with build name + status + link to artifact |
| Failed builds show as bare "FAILED" status | No idea what went wrong, no entertainment value in failures | Include the error summary and iteration count; failed builds can be interesting too |
| Dashboard shows builds as a plain table | Boring, doesn't convey the fun/creative intent of YOLO Dev | Show build cards with name, description, tech stack, LOC count, status badge, and a "Run" button |
| No way to manually trigger a build | Must wait until midnight to test the feature | Add a DM trigger: "Hey Bob, do a YOLO build: [idea]" that runs the same pipeline on-demand |
| No way to see what's currently building | During the overnight build, no visibility into progress | A "Currently Building" status card that shows the active build name and iteration count |
| Build history has no way to filter or search | After 30+ builds, finding a specific one requires scrolling | Add status filter (success/failed/partial) and text search on build name/description |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Docker memory limits:** `--memory` flag set in config AND verified with `docker inspect` AND tested by running a memory-heavy Python script AND confirmed that hitting the limit kills the container (not the gateway)
- [ ] **Build cron scheduling:** Cron created AND verified no overlap with existing 20 crons AND heartbeats disabled during build window AND `isolated: true` set AND model set to `haiku`
- [ ] **Turn/time limits:** Max 15 turns enforced AND max 30 min timeout enforced AND "same error" detection working AND limits logged in yolo.db AND verified by intentionally triggering a failing build
- [ ] **Disk management:** Retention policy auto-deletes builds >5 AND per-build size limit checked AND disk space pre-check runs before build AND WAL checkpoint cron running weekly AND `df` verified after 5 builds
- [ ] **Sandbox compatibility:** Build skill tested inside Docker container AND package availability verified AND writable paths documented AND `pip install --target` or venv approach tested AND import errors handled gracefully
- [ ] **yolo.db schema:** All dashboard-needed columns present AND indexes on status/created_at AND db-paths.ts updated AND WAL mode enabled AND tested with 10+ sample rows
- [ ] **Build verification:** Smoke test runs after build AND HTTP response checked for web apps AND exit code checked for CLI tools AND `is_runnable` flag set accurately AND failed verification logged in yolo.db
- [ ] **Delivery channel:** Slack channel delivery configured (not DM) AND Channel:ID format used AND post-restart delivery tested AND morning briefing includes YOLO section AND manual trigger works
- [ ] **Security constraints:** Build skill forbids env var access AND mandates localhost binding AND restricts file access to build directory AND generated code reviewed for path traversal AND SecureClaw rules compatible
- [ ] **Rate limit protection:** Build uses Haiku model AND 15-turn cap prevents token burn AND 4-hour buffer before morning briefing AND token usage logged in yolo.db AND no 429 errors observed after first week

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| OOM kills gateway (Pitfall 1) | LOW | systemd auto-restarts gateway (`Restart=always`). DM Bob to re-establish session. Check all crons fire on next cycle. If Docker container died, it restarts on next agent session. Add memory limits to prevent recurrence |
| Rate limit burns morning briefing (Pitfall 2) | MEDIUM | Wait for 5-hour rolling window to expire. Manually trigger briefing: `openclaw agent --agent main --message "Run morning briefing"`. Switch YOLO builds to Haiku to prevent recurrence |
| Disk fills, SQLite corruption (Pitfall 3) | HIGH | If WAL is corrupted, restore from backup (if exists) or rebuild database from source data. Delete all YOLO build artifacts: `rm -rf ~/clawd/yolo-dev/*`. Run `sqlite3 <db> 'PRAGMA integrity_check'` on all 6 databases. Implement retention policy immediately |
| Debug loop runs for hours (Pitfall 4) | LOW | Kill the build session: `openclaw sessions` to find it, then restart gateway if needed. Add turn/time limits. Review yolo.db for iteration count to calibrate limits |
| Cron collision causes cascading failures (Pitfall 5) | MEDIUM | Restart gateway. Verify all 20 crons are enabled and firing. Reschedule YOLO build to a non-conflicting window. Disable heartbeats during build window |
| Sandbox prevents all builds (Pitfall 6) | LOW | Test sandbox manually. Pre-install needed packages in Docker image. Update build skill to use only available tools. Rebuild Docker image if needed: this takes ~10 min |
| Ideas repeat (Pitfall 7) | LOW | Add past-ideas list to generation prompt. Implement theme rotation. Low-urgency fix -- boring ideas don't break anything |
| Schema too sparse for dashboard (Pitfall 8) | MEDIUM | `ALTER TABLE builds ADD COLUMN <col>`. Existing rows get NULL. Write a migration script to backfill from build logs if available. Better to get the schema right upfront |
| Builds not runnable (Pitfall 9) | LOW | Add verification step to build skill. Re-run recent builds with verification enabled. Update `is_runnable` flag for existing builds after manual testing |
| Restart kills YOLO delivery (Pitfall 10) | LOW | Switch to channel delivery. Re-establish DM session by messaging Bob. Build data is in yolo.db -- only the notification was lost |
| Generated code leaks secrets (Pitfall 11) | HIGH | Immediately delete the build artifacts. Rotate any exposed API keys. Audit all builds in yolo.db for env var access patterns. Tighten build skill constraints. Consider separate container with no sensitive env vars |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| OOM kills gateway (1) | Infrastructure Setup | Docker `--memory=1g` confirmed via `docker inspect`; health-check.sh alerts at <200MB |
| Rate limit burn (2) | Build Pipeline Cron | Build cron uses `model: haiku`; 15-turn cap in skill; no 429 errors for 1 week |
| Disk fills (3) | Infrastructure Setup + Build Pipeline | Retention policy auto-deletes; `df` shows >30% free after 1 week of builds |
| Debug loop (4) | Build Pipeline | yolo.db shows no builds with >15 iterations; timeout kills builds >30 min |
| Cron collision (5) | Build Pipeline Cron | Mission Control calendar shows no cron overlaps; heartbeats disabled during build window |
| Sandbox incompatibility (6) | Infrastructure Setup | Manual test: exec into container, run sample Python script with imports, verify success |
| Idea staleness (7) | Build Skill Design | yolo.db shows no duplicate themes in same 2-week window after 30+ builds |
| Schema sparseness (8) | Infrastructure Setup | yolo.db has 15+ columns; dashboard mockup maps to schema columns 1:1 |
| Unrunnable builds (9) | Build Skill Design | yolo.db `is_runnable` matches actual runnability for 80%+ of builds |
| Restart kills delivery (10) | Infrastructure Setup + Build Pipeline | Build notification arrives on Slack channel after a gateway restart test |
| Security exposure (11) | Build Skill Design | No generated code contains `os.environ`; builds only access their own directory |

---

## Sources

- [Agentic Resource Exhaustion: The Infinite Loop Attack on AI](https://instatunnel.my/blog/agentic-resource-exhaustion-the-infinite-loop-attack-of-the-ai-era) -- resource exhaustion patterns, max iteration caps, termination strategies (MEDIUM confidence)
- [Why AI Coding Agents Aren't Production-Ready](https://venturebeat.com/ai/why-ai-coding-agents-arent-production-ready-brittle-context-windows-broken) -- context window brittleness, broken refactors, operational awareness gaps (MEDIUM confidence)
- [AI-Generated Code Quality Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) -- 1.7x more issues in AI PRs, 30-41% technical debt increase (MEDIUM confidence)
- [Why AI Agents Get Stuck in Loops](https://www.fixbrokenaiapps.com/blog/ai-agents-infinite-loops) -- loop drift, repetitive actions, termination signal misinterpretation (MEDIUM confidence)
- [AI Coding Degrades: Silent Failures Emerge - IEEE Spectrum](https://spectrum.ieee.org/ai-coding-degrades) -- quality plateau/decline in 2025 AI coding models (MEDIUM confidence)
- [Docker Sandboxes: A New Approach for Coding Agent Safety](https://www.docker.com/blog/docker-sandboxes-a-new-approach-for-coding-agent-safety/) -- sandbox architecture, security model, limitations (HIGH confidence)
- [Why Docker Sandboxes Alone Don't Make AI Agents Safe](https://blog.arcade.dev/docker-sandboxes-arent-enough-for-agent-safety) -- sandbox bypass risks, credential exposure, network access concerns (MEDIUM confidence)
- [Container Escape Vulnerabilities: AI Agent Security 2026](https://blaxel.ai/blog/container-escape) -- container escape vectors, bind-mount risks, socket access dangers (MEDIUM confidence)
- [Docker Resource Constraints](https://docs.docker.com/engine/containers/resource_constraints/) -- memory limits, OOM behavior, container resource management (HIGH confidence)
- [Rate Limits - Claude API Docs](https://platform.claude.com/docs/en/api/rate-limits) -- token bucket algorithm, rolling windows, acceleration limits (HIGH confidence)
- [Claude Pro & Max Weekly Rate Limits Guide 2026](https://hypereal.tech/a/weekly-rate-limits-claude-pro-max-guide) -- 5-hour rolling window, weekly caps, off-peak behavior (MEDIUM confidence)
- [Claude Code Limits](https://www.truefoundry.com/blog/claude-code-limits-explained) -- quotas, concurrent sessions, rate limit mechanics (MEDIUM confidence)
- [OpenClaw Cron Jobs Documentation](https://docs.openclaw.ai/automation/cron-jobs) -- cron scheduling, stagger windows, isolated jobs, maxConcurrent (HIGH confidence)
- [Debugging AI-Generated Code: 8 Failure Patterns](https://www.augmentcode.com/guides/debugging-ai-generated-code-8-failure-patterns-and-fixes) -- common failure modes in AI code, security vulnerability rates (MEDIUM confidence)
- Project MEMORY.md (project internal) -- EC2 constraints, Docker sandbox read-only, 2GB RAM + 2GB swap, 13GB free disk, OOM recovery, gateway restart behavior, 20 cron jobs, all agent configurations (HIGH confidence)
- Project PROJECT.md (project internal) -- complete system inventory, agent roster, cron schedule, database list, key decisions, constraint documentation (HIGH confidence)

---
*Pitfalls research for: pops-claw v2.7 YOLO Dev autonomous overnight builder*
*Researched: 2026-02-24*
