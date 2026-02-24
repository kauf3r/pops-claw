# Feature Landscape: YOLO Dev v2.7

**Domain:** Autonomous overnight prototype builder for a personal AI agent system
**Researched:** 2026-02-24
**Confidence:** HIGH (features derived from existing OpenClaw infrastructure, proven cron/skill/DB patterns, and current autonomous coding agent ecosystem)

## Context

YOLO Dev adds overnight autonomous prototype building to Bob's existing capabilities. A cron fires late at night, Bob picks a project idea informed by personal context (interests, recent conversations, existing skills), builds a working prototype in his Docker sandbox, logs everything to yolo.db, and Andy wakes up to a new project on the `/yolo` dashboard page.

**Critical constraint:** Bob operates inside a Docker sandbox with network=bridge. He can write files, execute shell commands, and run scripts inside the container. The workspace at `~/clawd/yolo-dev/` is bind-mounted to `/workspace/yolo-dev/` in the sandbox. All builds happen inside the container. Bob already has 13 skills and 20 crons -- the patterns are proven and repeatable.

**Existing infrastructure leveraged:**
- OpenClaw cron system (20 crons already running, proven scheduling)
- Docker sandbox (read-only FS with bind-mount pattern for writes)
- SQLite database pattern (5 DBs already, yolo.db follows the same model)
- Mission Control Next.js 14 dashboard (5 pages already, `/yolo` extends)
- Skill system (13 skills deployed, SKILL.md + YAML frontmatter pattern)
- Workspace protocol docs (CONTENT_TRIGGERS.md pattern proven in v2.6)
- observability.db (token tracking already exists per agent)

**What Bob CAN do in sandbox:**
- Write files to bind-mounted directories
- Execute `python3`, `node`, `bash` scripts
- Install pip/npm packages (within the container)
- Use `curl` for HTTP requests (bridge networking)
- Read workspace files for context

**What Bob CANNOT do in sandbox:**
- Persist data outside bind-mounted paths (container resets)
- Run Docker-in-Docker
- Access host services directly (uses bridge network)
- Modify OpenClaw config or gateway

---

## Table Stakes

Features that make YOLO Dev functional. Without these, the feature does not exist.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Nightly cron trigger | The entire premise is "overnight builds." Without a cron, nothing fires | LOW | Follows exact pattern of 20 existing crons. `systemEvent` with reference doc pattern (YOLO_BUILD.md). Schedule: ~11 PM PT, isolated session, Sonnet model. Single cron entry in openclaw.json |
| Idea generation from context | Bob must pick something to build, informed by interests and recent context, not random | MEDIUM | Reference doc (YOLO_BUILD.md) provides idea generation instructions. Bob reads PRODUCT_CONTEXT.md, recent voice notes, coordination.db tasks, personal interests list. Outputs a project brief before building. Context sources are all already in the workspace or bind-mounted |
| Prototype building in sandbox | Bob writes actual code that runs. Not just a plan -- a working artifact | MEDIUM | Python + HTML as the default stack (both available in sandbox). Bob creates project directory under `/workspace/yolo-dev/{date}-{slug}/`, writes code, runs it, verifies output. Follows existing sandbox write patterns |
| Build artifact storage | Artifacts must persist after the session ends. Container resets, bind-mount survives | LOW | `~/clawd/yolo-dev/` bind-mounted to `/workspace/yolo-dev/`. Each build gets its own directory: `{YYYY-MM-DD}-{project-slug}/`. Contains source code, README.md, and any output files. Identical to how content.db and email.db are bind-mounted today |
| Build logging to yolo.db | Must know: what was built, when, did it work, how long did it take | MEDIUM | New SQLite database at `~/clawd/yolo-dev/yolo.db`. Schema: builds table (id, date, project_name, slug, description, status, started_at, completed_at, duration_seconds, tech_stack, lines_of_code, files_created, build_log, error_log). Bind-mounted alongside artifacts. Bob writes to it via SQL in sandbox |
| Build status tracking | Each build has a clear outcome: success, partial, or failed | LOW | Status enum in yolo.db: `idea`, `building`, `testing`, `success`, `partial`, `failed`. Bob updates status as it progresses. Final status reflects whether the prototype actually runs |
| README per build | Every build must explain what it is and how to run it | LOW | Bob writes `README.md` in each project directory. Contains: project name, what it does, how to run, tech used, what worked, what did not. This is the "morning briefing" for each build |
| Mission Control `/yolo` page | Andy checks the dashboard to see what shipped overnight | MEDIUM | New page in Mission Control. Reads yolo.db via better-sqlite3 (same pattern as all other pages). Shows build history as cards with status badges. Route: `/yolo`. Navigation link in sidebar |

### Confidence: HIGH
Every table-stakes feature uses a pattern already proven in the existing system. Cron, skill, SQLite, bind-mount, Mission Control page -- all have 5+ working examples to copy from.

---

## Differentiators

Features that transform YOLO Dev from "Bob builds random things overnight" into something genuinely delightful and useful.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Morning briefing integration | "Oh, Bob built something last night" shows up in the existing morning briefing alongside health, calendar, email | LOW | Add Section 11 (or equivalent) to morning briefing cron. Query yolo.db for builds from the previous night. Include project name, status, one-line description. Zero new infrastructure -- just a new section in an existing reference doc |
| Build quality self-evaluation | Bob rates his own build on a 1-5 scale with reasoning. "3/5 -- runs but the UI is ugly" | LOW | Add `self_score` (integer 1-5) and `self_evaluation` (text) columns to yolo.db builds table. Bob evaluates after building: does it run? Is the code clean? Does it do what was intended? Stored alongside build metadata. Useful for trending quality over time |
| Interest/context seeding file | A curated `YOLO_INTERESTS.md` file that Andy edits to steer idea generation toward domains he cares about | LOW | Workspace protocol doc at `~/clawd/agents/main/YOLO_INTERESTS.md`. Lists domains, technologies, project types Andy finds interesting. Bob reads it during idea generation. Andy can update anytime to shift the direction. Same pattern as CONTENT_TRIGGERS.md |
| Idea-to-build pipeline (not just random) | Bob generates 3-5 ideas, picks the best one with reasoning, then builds it. The selection logic is visible | LOW | Part of the YOLO_BUILD.md reference doc instructions. Bob writes `ideas.md` in the project directory before starting. Lists candidates with brief rationale, marks the selected one. Andy can see the decision process |
| Build log streaming to Slack | Short notification to DM or #ops when build starts and completes. "YOLO: Starting 'weather-dashboard'... YOLO: Done! 3/5, 47 files" | LOW | Bob already sends messages to Slack channels from crons. Add a brief start/complete notification to #ops or DM. Not the full log -- just status bookends. Uses existing `sessions_send` delivery pattern |
| Tech stack variety tracking | Track what technologies Bob uses across builds. Prevent repetition -- if the last 3 builds were all Python Flask, nudge toward something different | LOW | `tech_stack` column in yolo.db (text/JSON). Dashboard shows tech distribution across all builds. Reference doc can include "avoid repeating the same stack 3 times in a row" as a soft constraint |
| Build artifact preview | `/yolo` page shows a screenshot or HTML preview of the built artifact when applicable | HIGH | Would require Bob to take a screenshot of the running app (Camofox browser is available) or serve static HTML. Technically possible but adds complexity. Defer unless simple (e.g., if the build produces index.html, serve it as an iframe preview) |
| Weekly YOLO digest | Once a week, Bob summarizes all builds: best one, patterns, ideas for next week | LOW | Add to existing weekly-review cron. Query yolo.db for the past 7 days. Summarize: N builds, best-rated, most interesting, tech distribution. Same pattern as content pipeline weekly report |
| Failure analysis and learning | When a build fails, Bob writes a post-mortem in the project directory explaining what went wrong and what to try differently | LOW | Part of YOLO_BUILD.md instructions. On failure, write `POSTMORTEM.md` in the project directory. Include: what was attempted, where it broke, what would fix it, time spent. Valuable for trending failure patterns |

### Confidence: HIGH for all LOW/MEDIUM complexity items. These use proven patterns. MEDIUM for build artifact preview (requires browser automation integration during overnight builds, which adds execution complexity).

---

## Anti-Features

Features to explicitly NOT build. Each would add complexity disproportionate to value, or would conflict with the existing system architecture.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Human approval gate before building | "What if Bob builds something bad?" | The entire point of YOLO is autonomous overnight execution. An approval gate means Andy stays up to approve, defeating the purpose. Bob operates in a sandbox -- worst case is wasted tokens and disk space | Post-hoc review via dashboard. Bob builds freely, Andy reviews in the morning. Self-evaluation scores flag questionable builds |
| Multi-agent collaboration on builds | "Have Sentinel review Bob's code, or Vector research the idea" | Adds coordination complexity, increases token usage significantly, and the content pipeline already proved that multi-agent workflows need careful orchestration (took 3+ phases to stabilize). Single-agent builds are simpler and sufficient for prototypes | Bob builds alone. If a build concept matures into a real project, it graduates to the multi-agent workflow |
| Deployment/hosting of built prototypes | "Automatically deploy to a URL so I can share it" | Requires a web server, port management, DNS, HTTPS, and security considerations for every prototype. The EC2 is a t3.small with 2GB RAM. Running N arbitrary prototypes as services is a resource and security nightmare | Artifacts stored as files. Andy can manually run interesting ones via SSH. If something is worth deploying, it gets its own infrastructure intentionally |
| Git repo creation per build | "Each build should be its own git repo with commit history" | Git operations inside the Docker sandbox add complexity (git config, SSH keys, GitHub auth). The build is already versioned by date directory. Commit history for a 2-hour prototype is not meaningful | Directory-based versioning: `{date}-{slug}/`. If a build graduates, manually `git init` it |
| Persistent package cache across builds | "Don't re-download pip/npm packages every night" | Docker container resets between sessions. Maintaining a package cache requires additional bind-mount configuration and cache invalidation logic. Most prototypes use standard library or a few small packages | Accept the reinstall cost. Prototype builds are small -- package install is minutes, not hours |
| Interactive build mode ("watch Bob build live") | "Stream Bob's terminal output to the dashboard" | Requires WebSocket streaming, terminal emulation in the browser, and real-time log forwarding from the Docker container. Massive infrastructure for watching a process that runs while you sleep | Read the build log after completion. The `build_log` column in yolo.db captures the narrative. If real-time observation is needed, SSH into the container |
| Build templates / scaffolding system | "Pre-built templates for common project types (Flask app, React app, CLI tool)" | Over-constrains what Bob builds. Templates make sense for human developers who want consistency. For an autonomous agent, templates limit creativity and make builds feel formulaic | Let Bob decide the structure. The reference doc can suggest preferred patterns without enforcing rigid templates |
| Automatic PR creation for good builds | "If the build scores 4+, create a GitHub PR" | Mixes the experimental YOLO space with production repos. A 4/5 self-score does not mean production-ready code. Creates noise in GitHub. Blurs the line between prototype and production | Keep YOLO artifacts in `~/clawd/yolo-dev/`. Graduation to a real repo is a deliberate human decision |
| Cost budgeting per build | "Set a token limit per build to prevent runaway spending" | Andy is on Claude Pro 200 (flat rate). There are no per-token costs. Rate limits are the real constraint, not cost. Adding a token budget system solves a problem that does not exist | Model routing handles rate limits. Use Sonnet for builds (already the default for isolated crons). If builds hit rate limits, reduce frequency |

---

## Feature Dependencies

```
YOLO_BUILD.md (reference doc)
    |-- required by: nightly cron (reads instructions from here)
    |-- required by: idea generation (instructions define context sources)
    |-- required by: build execution (instructions define output format)

yolo.db schema
    |-- required by: build logging (Bob writes build records)
    |-- required by: /yolo dashboard page (reads build history)
    |-- required by: morning briefing section (reads last night's build)
    |-- required by: weekly digest (reads past 7 days)

~/clawd/yolo-dev/ bind-mount
    |-- required by: artifact storage (build files persist here)
    |-- required by: yolo.db (database lives here)
    |-- requires: openclaw.json sandbox config update (add bind-mount)

Nightly cron
    |-- requires: YOLO_BUILD.md (reference doc)
    |-- requires: bind-mount configured (writes to yolo-dev/)
    |-- requires: yolo.db schema created (logs builds)

/yolo dashboard page
    |-- requires: yolo.db with data (reads build history)
    |-- requires: Mission Control running (Next.js server)
    |-- independent of: cron and build execution (can be built in parallel)

YOLO_INTERESTS.md (context seeding)
    |-- enhances: idea generation quality
    |-- independent of: everything else (additive, not blocking)

Morning briefing integration
    |-- requires: yolo.db with data
    |-- requires: nightly cron to have run at least once
    |-- modifies: existing morning-briefing cron reference doc

Slack notifications
    |-- requires: nightly cron running
    |-- independent of: dashboard and DB schema
```

### Dependency Notes

- **YOLO_BUILD.md is the keystone.** The reference doc defines how Bob generates ideas, builds prototypes, and logs results. Everything else depends on these instructions being clear and complete.
- **yolo.db and bind-mount are infrastructure prerequisites.** Must be configured before the first cron run. But the dashboard page can be built in parallel since it just needs the schema to exist (even empty).
- **Dashboard and cron are independent work streams.** The `/yolo` page reads from yolo.db. The cron writes to yolo.db. They share the schema but not execution. Can be built and tested independently.
- **Morning briefing and Slack notifications are additive.** They enhance the experience but are not required for the core loop (cron -> build -> log -> dashboard).

---

## MVP Definition

### Launch With (v2.7)

Minimum viable YOLO Dev -- the overnight build loop works end to end.

- [ ] **YOLO_BUILD.md reference doc** -- Instructions for idea generation, build execution, quality evaluation, and logging. The "brain" of YOLO Dev
- [ ] **yolo.db schema + bind-mount** -- Database and filesystem infrastructure. Build records and artifacts persist across container resets
- [ ] **Nightly cron job** -- Triggers the build. Scheduled ~11 PM PT, isolated session, Sonnet model
- [ ] **YOLO_INTERESTS.md** -- Andy's interests/domains file for seeding idea generation. Quick to create, high impact on build relevance
- [ ] **Prototype building capability** -- Bob generates ideas, picks one, builds it, runs it, evaluates it, logs it. The core loop
- [ ] **Mission Control `/yolo` page** -- Build history dashboard. Cards with status badges, timestamps, descriptions, self-scores
- [ ] **Morning briefing integration** -- One section in existing briefing: "Last night's YOLO build: [name] -- [status] [score]/5"

### Add After Validation (v2.7.x)

Features to add once the core loop runs successfully for 5-7 nights.

- [ ] **Slack build notifications** -- Start/complete messages to #ops. Add after confirming the cron runs reliably
- [ ] **Weekly YOLO digest** -- Add to weekly-review cron after accumulating 5+ builds
- [ ] **Tech stack variety tracking** -- Dashboard chart showing tech distribution. Add after 10+ builds
- [ ] **Failure analysis post-mortems** -- POSTMORTEM.md on failed builds. Add once failure patterns emerge

### Future Consideration (v2.8+)

Features to defer until YOLO Dev is a proven, running system.

- [ ] **Build artifact preview** -- Screenshots or iframe previews on dashboard. Requires browser automation integration
- [ ] **Build quality trending** -- Sparkline showing self-scores over time. Needs 20+ data points to be meaningful
- [ ] **Idea backlog** -- Persist rejected ideas for future consideration. Needs a separate ideas table in yolo.db
- [ ] **Theme nights** -- "Python night" / "CLI tool night" / "data viz night" constraints. Fun but premature before the basic loop works

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Depends On Existing Infra |
|---------|------------|---------------------|----------|---------------------------|
| Nightly cron trigger | HIGH | LOW | P1 | Cron system (20 examples) |
| YOLO_BUILD.md reference doc | HIGH | LOW | P1 | Workspace protocol doc pattern |
| yolo.db schema + bind-mount | HIGH | LOW | P1 | SQLite + bind-mount pattern (5 DBs) |
| Prototype building in sandbox | HIGH | MEDIUM | P1 | Docker sandbox (existing) |
| Build artifact storage | HIGH | LOW | P1 | Bind-mount pattern (existing) |
| Mission Control /yolo page | HIGH | MEDIUM | P1 | Next.js dashboard (5 pages) |
| YOLO_INTERESTS.md | MEDIUM | LOW | P1 | Workspace doc pattern |
| Morning briefing integration | MEDIUM | LOW | P1 | Morning briefing cron (existing) |
| Build quality self-evaluation | MEDIUM | LOW | P1 | Part of build instructions |
| Idea-to-build pipeline visibility | MEDIUM | LOW | P1 | Part of build instructions |
| Slack notifications | MEDIUM | LOW | P2 | Slack delivery pattern (existing) |
| Weekly YOLO digest | LOW | LOW | P2 | Weekly review cron (existing) |
| Failure post-mortems | LOW | LOW | P2 | Part of build instructions |
| Tech stack variety tracking | LOW | LOW | P2 | yolo.db column + dashboard chart |
| Build artifact preview | MEDIUM | HIGH | P3 | Camofox browser (available but complex) |
| Build quality trending | LOW | MEDIUM | P3 | Recharts (available), needs data |
| Idea backlog persistence | LOW | MEDIUM | P3 | New yolo.db table |

**Priority key:**
- P1: Must have for v2.7 launch -- the overnight build loop works and is visible
- P2: Add after 5-7 successful nightly builds -- enhance the experience
- P3: Future consideration -- needs data or justification first

---

## Comparable Systems Analysis

| Feature | Ralph Wiggum Loop | Codex / Jules | Code Agents (code-agents.ai) | YOLO Dev Approach |
|---------|-------------------|---------------|------------------------------|-------------------|
| Trigger | Manual (user starts loop) | Manual (task assignment) | Manual (task queue) | Automated (nightly cron) |
| Scope | Defined by PRD/prompt | Single task/issue | Issue-based | Autonomous idea selection |
| Duration | Hours to days | 1-30 minutes | Variable | Single overnight session (~2h) |
| Evaluation | Completion promise | Test suite pass/fail | PR review | Self-evaluation 1-5 scale |
| Artifacts | Git commits/PRs | PRs with diffs | PRs | Directory with README |
| Logging | Git history | Platform dashboard | Platform dashboard | yolo.db + /yolo page |
| Idea generation | None (human provides) | None (human provides) | None (human provides) | Context-aware autonomous |

**Key differentiator for YOLO Dev:** No other system autonomously generates its own project ideas from personal context. Ralph Wiggum, Codex, Jules, and Code Agents all require a human to define the task. YOLO Dev's entire premise is that Bob picks the idea himself, which makes the "what will I wake up to?" experience unique and delightful.

---

## Sources

### Autonomous Coding Agent Patterns
- [Ralph Wiggum: Autonomous Loops for Claude Code](https://paddo.dev/blog/ralph-wiggum-autonomous-loops/) -- HIGH confidence (established technique for overnight autonomous coding)
- [Awesome Claude: Ralph Wiggum](https://awesomeclaude.ai/ralph-wiggum) -- HIGH confidence (community reference)
- [Code Agents: Ship production code while you sleep](https://code-agents.ai/) -- MEDIUM confidence (commercial product, feature reference)
- [Martin Fowler: Autonomous Coding Agents (Codex Example)](https://martinfowler.com/articles/exploring-gen-ai/autonomous-agents-codex-example.html) -- HIGH confidence (authoritative analysis)

### Failure Handling and Recovery
- [GoCodeo: Error Recovery and Fallback Strategies](https://www.gocodeo.com/post/error-recovery-and-fallback-strategies-in-ai-agent-development) -- MEDIUM confidence (general patterns)
- [DEV Community: Why Your Overnight AI Agent Fails](https://dev.to/thebasedcapital/why-your-overnight-ai-agent-fails-and-how-episodic-execution-fixes-it-2g50) -- MEDIUM confidence (failure mode analysis)
- [Agents Arcade: Error Handling in Agentic Systems](https://agentsarcade.com/blog/error-handling-agentic-systems-retries-rollbacks-graceful-failure) -- MEDIUM confidence

### Build Quality Evaluation
- [Anthropic: Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) -- HIGH confidence (official Anthropic engineering blog)
- [OpenObserve: How AI Agents Automated Our QA](https://openobserve.ai/blog/autonomous-qa-testing-ai-agents-claude-code/) -- MEDIUM confidence

### Dashboard Design (Build History)
- [Google Antigravity Codelabs: Mission Control Dashboard](https://codelabs.developers.google.com/getting-started-google-antigravity) -- MEDIUM confidence (agent dashboard patterns)
- [GitHub: Agentic QA Framework](https://github.com/partarstu/agentic-qa-framework) -- MEDIUM confidence (dashboard feature reference)

### OpenClaw Platform
- [OpenClaw Docs: Skills](https://docs.openclaw.ai/tools/skills) -- HIGH confidence (official documentation)
- [OpenClaw Docs: Sandboxing](https://docs.openclaw.ai/gateway/sandboxing) -- HIGH confidence (official documentation)
- [Docker Blog: Run OpenClaw Securely in Docker Sandboxes](https://www.docker.com/blog/run-openclaw-securely-in-docker-sandboxes/) -- HIGH confidence

### Internal Sources (HIGH confidence)
- PROJECT.md: Full system inventory, constraints, infrastructure details
- CLAUDE.md: Project overview, key files, working patterns
- MEMORY.md: EC2 access, sandbox architecture, cron configuration, lessons learned
- Previous FEATURES.md (v2.5): Dashboard patterns, data access patterns, anti-feature reasoning

---

*Feature research for: YOLO Dev v2.7 -- autonomous overnight prototype builder for pops-claw*
*Researched: 2026-02-24*
*Replaces: previous FEATURES.md covering Mission Control Dashboard v2.5 (shipped)*
