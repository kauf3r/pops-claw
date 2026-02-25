# Requirements: YOLO Dev v2.7

**Defined:** 2026-02-24
**Core Value:** Bob autonomously builds a working prototype overnight and logs everything to a dashboard Andy checks in the morning.

## v2.7 Requirements

### Infrastructure

- [x] **INFRA-01**: yolo.db SQLite database created at ~/clawd/yolo-dev/yolo.db with builds table (id, date, slug, name, description, status, tech_stack, lines_of_code, files_created, self_score, self_evaluation, build_log, error_log, started_at, completed_at, duration_seconds)
- [x] **INFRA-02**: ~/clawd/yolo-dev/ directory created with bind-mount in openclaw.json sandbox config mapping to /workspace/yolo-dev/
- [x] **INFRA-03**: Build artifacts stored in ~/clawd/yolo-dev/{NNN}-{slug}/ with sequential numbering and README.md per build

### Build Pipeline

- [x] **BUILD-01**: Nightly cron job triggers Bob to execute an overnight build (isolated session, ~11 PM PT, Haiku model to avoid rate limit contention)
- [x] **BUILD-02**: YOLO_BUILD.md workspace reference doc defines the full build protocol — idea generation, execution, logging, evaluation
- [x] **BUILD-03**: Bob generates 3-5 project ideas informed by personal context (interests, recent voice notes, projects, skills), picks the best with reasoning, logs candidates to ideas.md
- [x] **BUILD-04**: YOLO_INTERESTS.md workspace protocol doc seeds idea generation with Andy's domains, technologies, and project types — editable anytime to steer direction
- [x] **BUILD-05**: Bob builds a working prototype using Python stdlib + vanilla HTML/JS as default stack, constrained to 100-500 LOC and 2-6 files
- [x] **BUILD-06**: Build status tracked in yolo.db with enum: idea → building → testing → success/partial/failed
- [x] **BUILD-07**: Bob self-evaluates each build on a 1-5 scale with reasoning (does it run, is the code clean, does it do what was intended)
- [x] **BUILD-08**: On failure or partial build, Bob writes POSTMORTEM.md explaining what was attempted, where it broke, and what would fix it
- [x] **BUILD-09**: Hard guardrails: 15-turn cap, 30-minute timeout, no pip/npm installs outside /workspace/, avoid repeating the same tech stack 3 builds in a row

### Dashboard & Notifications

- [x] **DASH-01**: Mission Control /yolo page displays build history as cards with status badges, self-scores, descriptions, and tech stack — newest first, filterable by status
- [ ] **DASH-02**: Morning briefing Section 11 includes last night's YOLO build: project name, status, self-score, one-line description
- [ ] **DASH-03**: Weekly review includes YOLO digest: N builds, best-rated, tech distribution, patterns
- [ ] **DASH-04**: Slack notification to DM when build starts and completes

## Future Requirements

### Build Enhancements (v2.8+)

- **BUILD-10**: Build artifact preview — if build produces index.html, render as iframe preview on /yolo page
- **BUILD-11**: Build retention policy — auto-cleanup of builds older than 30 days, keep top-rated
- **BUILD-12**: Tech stack variety enforcement via dashboard distribution chart and reference doc nudge

### Dashboard Enhancements (v2.8+)

- **DASH-05**: Build trend chart on /yolo page — success rate over time, average self-score trend
- **DASH-06**: Clickable build detail view with full build log, ideas.md, and file listing

## Out of Scope

| Feature | Reason |
|---------|--------|
| Human approval gate before building | Defeats the overnight autonomous premise. Post-hoc review via dashboard |
| Multi-agent collaboration on builds | Content pipeline proved multi-agent orchestration needs extensive stabilization |
| Deployment/hosting of prototypes | EC2 is t3.small with 2GB RAM. Running N services is a resource nightmare |
| Git repo per build | Adds sandbox complexity (git config, SSH keys). Directory versioning sufficient |
| Interactive "watch Bob build" mode | Requires WebSocket streaming. Read build log after completion |
| Build templates/scaffolding | Over-constrains creativity. Let Bob decide structure |
| Automatic PR for good builds | Mixes experimental space with production repos |
| Cost budgeting per build | Claude Pro 200 is flat rate. Rate limits handled by model routing |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 38 | Complete |
| INFRA-02 | Phase 38 | Complete |
| INFRA-03 | Phase 38 | Complete |
| BUILD-01 | Phase 39 | Complete |
| BUILD-02 | Phase 39 | Complete |
| BUILD-03 | Phase 39 | Complete |
| BUILD-04 | Phase 39 | Complete |
| BUILD-05 | Phase 39 | Complete |
| BUILD-06 | Phase 39 | Complete |
| BUILD-07 | Phase 39 | Complete |
| BUILD-08 | Phase 39 | Complete |
| BUILD-09 | Phase 39 | Complete |
| DASH-01 | Phase 40 | Complete |
| DASH-02 | Phase 41 | Pending |
| DASH-03 | Phase 41 | Pending |
| DASH-04 | Phase 41 | Pending |

**Coverage:**
- v2.7 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 -- traceability updated with phase mappings*
