# Project Research Summary: v2.7 YOLO Dev

**Project:** pops-claw -- Autonomous Overnight Prototype Builder
**Domain:** AI agent autonomous code generation + Mission Control dashboard integration
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

YOLO Dev is architecturally the simplest milestone since v2.1 because every capability it needs already exists in the pops-claw system. Bob runs in a Docker sandbox with Python 3, bash, curl, git, and sqlite3. He already writes files to bind-mounted directories, executes shell commands, and logs structured data to SQLite. Mission Control already reads 5 SQLite databases and renders pages using the same query-module + API-route + SWR pattern. The content pipeline (v2.1) established the exact model YOLO Dev replicates: a skill teaches the behavior, a cron triggers it nightly, a reference doc provides session context, SQLite stores all metadata, and a dashboard page displays results. YOLO Dev is a new behavior on an existing platform, not a new platform.

The recommended approach is pure constraint-driven design. Prototypes use Python stdlib and static HTML/CSS/JS only -- no pip packages, no Node.js, no frameworks. This is not a limitation; it is the feature. Constraints force complete-in-one-session builds, prevent yak-shaving on dependency management, and keep the Docker sandbox lightweight enough to run alongside 20 existing cron jobs on a t3.small with 2GB RAM. The skill instructs Bob on idea selection (from a curated idea bank + generated options), prototype building, programmatic smoke testing, and SQLite logging -- all within a hard 15-turn session limit. The overnight autonomous coding pattern is well-established in the AI agent community (the "Ralph Wiggum" loop) and the guardrails from that research (iteration limits, time limits, scope constraints) are directly incorporated into the YOLO Dev skill design.

The critical risks are resource-driven: OOM from unbounded Docker memory, rate limit exhaustion from long Sonnet builds starving daytime crons, and disk accumulation from undeleted build artifacts. All three are addressable with pre-emptive configuration in Phase 1 -- Docker memory caps, Haiku model selection, and a 5-build retention policy. The one gap that cannot be resolved by research is skill prompt quality: how good Bob's builds are depends on the YOLO_SESSION.md instructions, which must be tuned empirically after the first week of nightly runs.

## Key Findings

### Recommended Stack

YOLO Dev adds zero new npm packages and zero new Docker infrastructure to the existing system. The entire capability is built from five elements: a new OpenClaw skill, a new cron job, two workspace reference docs, a new SQLite database (yolo.db), and a new Mission Control page -- all following patterns already validated in production.

**Core technologies:**
- OpenClaw skill (`yolo-dev`): Teaches Bob the build protocol. Same SKILL.md format as 13 existing skills.
- OpenClaw cron (`yolo-dev-overnight`): Nightly trigger at midnight PT (06:00 UTC). Same JSON schema as 20 existing crons. Model: Haiku (not Sonnet) to protect rate limit budget.
- Workspace docs (`YOLO_SESSION.md`, `YOLO_IDEAS.md`): Session instructions and idea bank. Same protocol-doc pattern as MEETING_PREP.md, STANDUP.md.
- SQLite (`yolo.db`): Build metadata database at `~/clawd/yolo.db`, bind-mounted to `/workspace/yolo.db`. Same pattern as content.db, email.db. Written by Bob via sqlite3 CLI, read by Mission Control via better-sqlite3.
- Next.js 14 / better-sqlite3 / SWR (all existing): `/yolo` page in Mission Control following the Phase 29-30 established dashboard pattern.

**Schema decision:** Design yolo.db from the dashboard down, not from the build up. Capture rich metadata on day one: `status`, `duration_seconds`, `iteration_count`, `error_count`, `lines_of_code`, `tech_stack`, `idea_source`, `artifact_path`, `is_runnable`, `smoke_test_passed`. Retrofitting this via ALTER TABLE creates NULLs in early rows and requires schema migrations.

### Expected Features

**Must have (table stakes -- v2.7 launch):**
- Nightly cron trigger at midnight PT, isolated session, Haiku model
- Idea selection from YOLO_IDEAS.md (curated bank) or Bob-generated, with anti-repetition tracking
- Prototype build in `/workspace/yolo-dev/{date}-{slug}/` -- Python stdlib or static HTML
- Programmatic smoke test after build (run the code, check exit code or HTTP response)
- Build logging to yolo.db with rich metadata
- Slack summary delivery to channel (not DM -- channel delivery survives gateway restarts)
- Mission Control `/yolo` page with build history cards, status badges, stats row
- Morning briefing Section 11: last night's YOLO result (name, status, score, LOC)
- Build retention: auto-delete builds older than the last 5 on every run

**Should have (add after 5-7 successful nights):**
- Slack start/complete notifications to #ops or #yolo-dev
- Weekly YOLO digest in the existing weekly-review cron
- Tech stack variety tracking in dashboard (prevent same stack 3 nights in a row)
- Build failure post-mortems (`POSTMORTEM.md` in failed build directory)

**Defer to v2.8+:**
- Build artifact screenshot/preview in dashboard (requires Camofox browser during overnight build -- high complexity)
- Build quality trend sparklines (need 20+ data points to be meaningful)
- Idea backlog table in yolo.db (separate from the ideas flat file)
- Theme nights ("Python night", "CLI night") -- fun but premature before basic loop works

**Anti-features (do not build):**
- Human approval gate (defeats autonomous purpose)
- Multi-agent collaboration on builds (adds coordination overhead; single-agent is sufficient)
- Deployment/hosting of built prototypes (security surface, resource risk on t3.small)
- Git repo per build (over-engineering for throwaway prototypes)
- Build queue / Redis (one build per cron, sequential, fail gracefully)

### Architecture Approach

YOLO Dev is a cron-triggered skill execution following the same pattern as the content pipeline. The data flow is: cron fires -> OpenClaw creates isolated Bob session -> Bob reads YOLO_SESSION.md -> Bob selects idea from YOLO_IDEAS.md -> Bob builds prototype in `/workspace/yolo-dev/{slug}/` -> Bob runs smoke test -> Bob logs to yolo.db via sqlite3 CLI -> Bob posts summary to Slack channel -> Mission Control reads yolo.db and displays on `/yolo` page.

**Major components:**
1. `yolo-dev` skill (`~/.openclaw/skills/yolo-dev/SKILL.md`): Brain of the system. Defines idea selection, build constraints (stdlib only, max 200 LOC, single file preferred), smoke test protocol, DB logging format, Slack delivery format.
2. Cron + Session Doc (`YOLO_SESSION.md`): Trigger mechanism. Cron fires with short message; Bob reads the session doc for full instructions. Same as all 20 existing crons.
3. Build artifacts directory (`~/clawd/yolo-dev/`): Persistent storage for all build outputs. Bind-mounted to `/workspace/yolo-dev/` in sandbox. Convention: `{YYYY-MM-DD}-{slug}/` directory per build.
4. `yolo.db` (SQLite, 6th database): Build metadata. Two tables: `builds` (summary) and `build_files` (file manifest). Indexed on `date DESC` and `status`.
5. Mission Control `/yolo` page: Standard query-module + API-route + SWR pattern. Stats row (total builds, success rate, total LOC, streak) + scrollable build card list.

**Two new bind-mounts in openclaw.json** (must be added together, require one gateway restart):
- `/home/ubuntu/clawd/yolo.db:/workspace/yolo.db:rw`
- `/home/ubuntu/clawd/yolo-dev:/workspace/yolo-dev:rw`

**Key pattern to follow:** `yolo.db` must be created on the HOST before the first bind-mount is activated. `sqlite3 ~/clawd/yolo.db "SELECT 1;"` is the one-time setup step. The Docker bind-mount requires the host-side file to exist first.

### Critical Pitfalls

1. **OOM kills the gateway overnight** -- A YOLO build that installs pip dependencies (numpy, pandas) can spike memory past the 4GB ceiling (2GB RAM + 2GB swap), triggering the Linux OOM killer. Mitigation: set Docker memory limit (`--memory=1g --memory-swap=1.5g`) in the cron or agent config; restrict the build stack to Python stdlib only; add a pre-build memory check (`free -m` > 500MB available). This must be configured in Phase 1 before any build runs.

2. **Rate limit exhaustion starves daytime crons** -- A long Sonnet build at midnight consuming 15-20 high-token turns can exhaust the Claude Pro 200 rolling 5-hour window, causing the 6 AM morning briefing to fail or degrade. Mitigation: use Haiku (not Sonnet) as the cron model -- Haiku has a separate rate pool and is sufficient for Python stdlib prototypes. Set a hard 15-turn session limit in the cron configuration.

3. **Disk accumulation corrupts SQLite databases** -- Without a retention policy, build artifacts (code + optional venvs) accumulate. The EC2 starts at 55% disk usage with ~13GB free. At 100-500KB per build, 100 builds is manageable; at 100-500MB (with dependencies), 10 builds can fill the disk. When disk drops below 5% free, SQLite WAL checkpointing fails silently, leading to database corruption. Mitigation: implement a 5-build retention policy as part of the build teardown from day one; prohibit pip/npm installs (no venv accumulation); add disk threshold to health-check.sh.

4. **Debug-retry infinite loop burns all resources** -- LLMs attempting to fix code errors will retry indefinitely without explicit guardrails. A 50-turn build session that never produces output is the #1 failure mode for autonomous coding agents. Mitigation: hard 15-turn limit (configured in cron or skill instructions) and hard 30-minute wall-clock timeout (`timeout 1800`). Log `iteration_count` in yolo.db -- builds exceeding 10 iterations are early warning indicators.

5. **Cron schedule collision with existing 20 jobs** -- The YOLO build is a 30-minute heavy session that fires during a window where heartbeat crons (every 15 min, 4 agents) are also running. Multiple concurrent LLM sessions on a 2GB system creates memory pressure and SQLITE_BUSY conflicts on shared databases. Mitigation: schedule the build at 06:00 UTC (midnight PT, 6 hours before the morning briefing at 2 PM UTC), use `isolated: true` to prevent session sharing, verify no other cron fires within 10 minutes of the build start.

6. **Docker read-only filesystem prevents builds** -- Bob cannot `pip install` or write to system paths inside the container. If the skill doesn't explicitly constrain the tech stack to writable paths (`/workspace/`), Bob will attempt system installs, fail with permission errors, and enter a debug loop. Mitigation: the skill must explicitly state what IS available (Python stdlib, bash, sqlite3 CLI) and what is NOT (pip install, npm install, system paths). Test the sandbox environment before writing the skill.

7. **DM delivery fails after gateway restart** -- The gateway restart required for YOLO Dev configuration clears all DM sessions. If the build tries to post to Bob's DM channel without an active session, the notification silently fails. Mitigation: deliver build summaries to a Slack channel (e.g., #ops or #yolo-dev) using the `channel:ID` format from v2.6, not DM. Include a file-based fallback: write summary to `/workspace/yolo-results-latest.md` that the morning briefing can pick up.

## Implications for Roadmap

Based on all research findings, the dependency-aware phase structure is:

### Phase 1: Infrastructure Foundation
**Rationale:** All other phases depend on the storage layer and Docker configuration existing. This is also the only phase requiring a gateway restart -- batch everything into one.
**Delivers:** yolo-dev directory, yolo.db (schema pre-created), bind-mounts configured, cron job stub added, gateway restarted once.
**Addresses features:** Build artifact storage, DB logging infrastructure, bind-mount for sandbox access.
**Avoids pitfalls:** Pitfall 1 (OOM) by adding Docker memory limits; Pitfall 3 (disk) by pre-configuring retention policy; Pitfall 7 (DM failure) by choosing channel delivery; Pitfall 6 (sandbox limitations) by verifying environment before writing skill.
**Schema must include:** `id`, `date`, `project_name`, `slug`, `description`, `tech_stack`, `status`, `artifacts_path`, `idea_source`, `lines_of_code`, `files_created`, `iteration_count`, `error_count`, `duration_minutes`, `is_runnable`, `smoke_test_passed`, `build_log`, `error_message`, `created_at`, `updated_at`. Design this from the dashboard, not from the build process.

### Phase 2: Skill + Cron + Reference Docs
**Rationale:** Bob needs explicit instructions (skill + session doc) before the first build can run. This phase can be deployed without a gateway restart -- skill files and workspace docs are hot-loaded.
**Delivers:** `yolo-dev` skill, `YOLO_SESSION.md` cron reference doc, `YOLO_IDEAS.md` idea bank seeded with 5-10 starter ideas, first manual cron trigger to validate the end-to-end loop.
**Uses stack:** Existing skill system, workspace protocol doc pattern.
**Implements:** Skill component, cron trigger, session reference doc.
**Avoids pitfalls:** Pitfall 2 (rate limits) by configuring Haiku model and 15-turn limit; Pitfall 4 (debug loop) by including hard turn and time limits in the skill; Pitfall 5 (cron collision) by verifying schedule doesn't overlap existing jobs; Pitfall 9 (unverified builds) by requiring programmatic smoke tests.
**Key design decisions:** The YOLO_SESSION.md is the most important artifact in this milestone. It defines scope constraints (stdlib only, 100-200 LOC target, single file preferred), anti-repetition mechanics (include list of past build slugs in context), smoke test protocol (run the code, capture output, verify exit 0), and delivery format (channel:ID, not DM).

### Phase 3: Mission Control /yolo Page
**Rationale:** Dashboard can be built in parallel with Phase 2 (it only requires the schema to exist, not actual data). However, building it after Phase 2's first manual test ensures there is real data to test the UI against.
**Delivers:** `/yolo` route in Mission Control with stats row, build history cards, build detail view with logs.
**Uses stack:** Next.js 14, better-sqlite3, SWR, shadcn/ui, Recharts -- all existing.
**Implements:** Query module (`queries/yolo.ts`), API route (`/api/dashboard/yolo`), page component (`/app/yolo/page.tsx`), navbar link.
**Avoids pitfalls:** Pitfall 8 (schema design) -- the dashboard exposes whether the schema is rich enough; any gaps surface immediately during UI implementation.
**Standard pattern, no research needed:** Identical to Phase 29-30 dashboard implementation.

### Phase 4: Morning Briefing + Cleanup Cron
**Rationale:** Polish and maintenance layer. Only meaningful after the core loop has run successfully for 3-5 nights and the data is real.
**Delivers:** YOLO section in morning briefing (last night's build summary), automated build artifact cleanup script (keep last 5), yolo-build added to Mission Control's cron calendar display.
**Addresses features:** Morning briefing integration (P1 feature), tech stack variety tracking, weekly YOLO digest (if 5+ builds exist).
**Avoids pitfalls:** Pitfall 3 (disk accumulation) with automated retention; ensures the morning briefing section is never empty (graceful "No build yet" default).

### Phase Ordering Rationale

- Phase 1 is a prerequisite for everything: bind-mounts must exist before Bob can write, yolo.db must exist before Bob can log, cron stub must be in openclaw.json for Phase 2 to test.
- Phases 1 and 2 share a single gateway restart: batch all openclaw.json changes (bind-mounts + cron entry) into one restart in Phase 1; Phase 2 skill and workspace files are hot-loaded without restart.
- Phase 3 is independent of the gateway: Mission Control is a separate Next.js service. It can be built while Phase 2's first build is running.
- Phase 4 requires validated data: adding the morning briefing section without real builds produces misleading "No builds yet" output every morning. Wait for 3-5 successful builds before integrating.
- The gateway restart in Phase 1 must be followed immediately by a DM to Bob to re-establish his session before the YOLO cron fires.

### Research Flags

Phases needing deeper research during planning:
- **Phase 2 (Skill Design):** The quality of YOLO_SESSION.md cannot be predicted by research -- it must be iterated after seeing actual build outputs. Plan for a skill refinement pass after the first week. The initial skill should be conservative (tight scope, simple ideas) and loosen constraints as empirical results show what Bob can reliably accomplish.
- **Phase 2 (Model Selection):** Verify whether Haiku produces acceptable code quality for the prototype scope defined. If Haiku builds are consistently poor-quality or fail smoke tests, escalate to Sonnet with a tighter turn limit (10 instead of 15) and monitor rate limits.

Phases with established patterns (skip research):
- **Phase 1:** Bind-mount + SQLite schema + cron stub. All documented in prior milestones. Copy from content.db pattern.
- **Phase 3:** Mission Control page. Direct copy of Phase 29-30 implementation. `queries/yolo.ts` is nearly identical to `queries/metrics.ts`.
- **Phase 4:** Morning briefing section. Direct copy of any existing briefing section pattern. Cleanup cron is a shell script following `prune-sessions.sh`.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies. Every technology validated in production across 6 milestones. No version conflicts possible. |
| Features | HIGH | All features map directly to existing system patterns. The one uncertain feature (build quality) is explicitly deferred to empirical tuning. |
| Architecture | HIGH | YOLO Dev follows the content pipeline pattern exactly. Four prior milestones have proven the cron + skill + SQLite + dashboard pattern. |
| Pitfalls | HIGH | Critical pitfalls are derived from known system constraints (2GB RAM, 13GB free disk, Claude Pro 200 rate limits, Docker read-only FS). These are facts, not predictions. |

**Overall confidence: HIGH**

### Gaps to Address

- **Skill prompt quality (empirical, not researchable):** How good Bob's nightly builds are depends entirely on the YOLO_SESSION.md instructions and cannot be determined without running actual builds. Plan for a mandatory skill refinement pass after 5-7 nights of builds. Track `iteration_count` and `smoke_test_passed` in yolo.db as quality signals from day one.

- **Python version in sandbox (needs EC2 verification):** Research indicates Python 3.11 (Debian Bookworm) but the exact available version should be verified via `python3 --version` inside an exec'd container before writing the skill. Some stdlib features differ between 3.8 and 3.11.

- **Haiku code quality threshold (empirical):** Research recommends Haiku for rate limit safety, but whether Haiku can reliably generate working 100-200 LOC Python prototypes is unknown. If the first 3-5 builds are consistently poor with Haiku, escalate model selection and adjust cron schedule to protect rate limits differently.

- **Idea bank seeding (requires human input):** YOLO_IDEAS.md needs to be populated with 10-20 initial ideas that reflect Andy's actual interests. Research identified categories (CLI tools, data visualizers, API mashups, automation scripts, simple games) but the specific ideas should be generated collaboratively rather than pre-populated by research.

- **Cron schedule verification:** The 06:00 UTC schedule must be checked against all 20 existing cron jobs to confirm no collision within a 30-minute window. This requires inspecting the current openclaw.json or cron-jobs.json on EC2.

## Sources

### Primary (HIGH confidence)
- PROJECT.md (internal) -- full system inventory, constraints, infrastructure details
- MEMORY.md (internal) -- EC2 access, sandbox architecture, bind-mount patterns, cron lessons
- Phase 12 (internal) -- content DB + agent setup, established DB + bind-mount + skill pattern
- Phase 29-30 (internal) -- Mission Control dashboard query module + API route + SWR pattern
- Phase 33 (internal) -- cron reference doc + channel:ID delivery pattern
- v2.6 ROADMAP.md (internal) -- most recent milestone structure and phase conventions
- Anthropic engineering blog: Demystifying Evals for AI Agents -- build quality evaluation patterns

### Secondary (MEDIUM confidence)
- Ralph Wiggum autonomous loop pattern -- overnight AI coding agent guardrails
- OpenClaw official docs (sandboxing, skills, cron) -- configuration schema details
- Martin Fowler: Exploring Gen AI / Codex autonomous agents -- task scoping for code agents
- DEV Community: Why Your Overnight AI Agent Fails -- failure mode catalog

### Tertiary (LOW confidence -- verify on EC2)
- Python version in Docker sandbox (verify before writing skill)
- sqlite3 CLI behavior with bind-mounted DB files (behavior documented but verify with empty file)
- Exact cron schedule overlap with existing 20 jobs (inspect cron-jobs.json)

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*
