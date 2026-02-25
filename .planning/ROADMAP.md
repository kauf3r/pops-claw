# Roadmap: Proactive Daily Companion

## Milestones

- ✅ **v2.0 Proactive Daily Companion** — Phases 1-11 (shipped 2026-02-09)
- ✅ **v2.1 Content Marketing Pipeline** — Phases 12-18 (shipped 2026-02-09)
- ✅ **v2.2 Resend Email Integration** — Phases 19-23 (shipped 2026-02-17)
- ✅ **v2.3 Security & Platform Hardening** — Merged into v2.4 (0 phases executed)
- ✅ **v2.4 Content Distribution & Platform Hardening** — Phases 24-28 (shipped 2026-02-21)
- ✅ **v2.5 Mission Control Dashboard** — Phases 29-32 (shipped 2026-02-22)
- ✅ **v2.6 Content Pipeline Hardening** — Phase 33 (shipped 2026-02-23)

## Phases

<details>
<summary>✅ v2.0 Proactive Daily Companion (Phases 1-11) — SHIPPED 2026-02-09</summary>

- [x] Phase 1: Update, Memory & Security (2/2 plans) — completed 2026-02-07
- [x] Phase 2: Oura Ring Integration (1/1 plan) — completed 2026-02-08
- [x] Phase 3: Daily Briefing & Rate Limits (3/3 plans) — completed 2026-02-08
- [x] Phase 4: MCP Servers (1/1 plan) — completed 2026-02-08
- [x] Phase 5: Govee & Wyze Integrations (2/2 plans) — completed 2026-02-08
- [x] Phase 6: Multi-Agent Gateway (2/2 plans) — completed 2026-02-08
- [x] Phase 7: Multi-Agent Slack Channels (1/1 plan) — completed 2026-02-09
- [x] Phase 8: Multi-Agent Automation (2/2 plans) — completed 2026-02-09
- [x] Phase 9: Proactive Agent Patterns (3/3 plans) — completed 2026-02-08
- [x] Phase 10: Agentic Coding Workflow (2/2 plans) — completed 2026-02-09
- [x] Phase 11: Document Processing (2/2 plans) — completed 2026-02-09

Full details: [milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)

</details>

<details>
<summary>✅ v2.1 Content Marketing Pipeline (Phases 12-18) — SHIPPED 2026-02-09</summary>

- [x] Phase 12: Content DB + Agent Setup (3/3 plans) — completed 2026-02-09
- [x] Phase 13: Topic Research (2/2 plans) — completed 2026-02-09
- [x] Phase 14: Writing Pipeline (2/2 plans) — completed 2026-02-09
- [x] Phase 15: Review Pipeline (2/2 plans) — completed 2026-02-09
- [x] Phase 16: WordPress Publishing (2/2 plans) — completed 2026-02-09
- [x] Phase 17: Social Promotion (1/1 plan) — completed 2026-02-09
- [x] Phase 18: Pipeline Monitoring (2/2 plans) — completed 2026-02-09

Full details: [milestones/v2.1-ROADMAP.md](milestones/v2.1-ROADMAP.md)

</details>

<details>
<summary>✅ v2.2 Resend Email Integration (Phases 19-23) — SHIPPED 2026-02-17</summary>

- [x] Phase 19: Outbound Email Foundation (2/2 plans) — completed 2026-02-16
- [x] Phase 20: Inbound Email Infrastructure (2/2 plans) — completed 2026-02-17
- [x] Phase 21: Inbound Email Processing (2/2 plans) — completed 2026-02-17
- [x] Phase 22: Domain Warmup & Production Hardening (1/1 plan) — completed 2026-02-17
- [x] Phase 23: Email Integration Gap Closure (1/1 plan) — completed 2026-02-17

Full details: [milestones/v2.2-ROADMAP.md](milestones/v2.2-ROADMAP.md)

</details>

<details>
<summary>✅ v2.4 Content Distribution & Platform Hardening (Phases 24-28) — SHIPPED 2026-02-21</summary>

- [x] Phase 24: Critical Security Update (2/2 plans) — completed 2026-02-18
- [x] Phase 25: Post-Update Audit (2/2 plans) — completed 2026-02-18
- [x] Phase 26: Agent Observability (2/2 plans) — completed 2026-02-19
- [x] Phase 27: Email Domain Hardening (1/1 plan) — completed 2026-02-19
- [x] Phase 28: Platform Cleanup (2/2 plans) — completed 2026-02-21

Full details: [milestones/v2.4-ROADMAP.md](milestones/v2.4-ROADMAP.md)

</details>

<details>
<summary>✅ v2.5 Mission Control Dashboard (Phases 29-32) — SHIPPED 2026-02-22</summary>

- [x] Phase 29: Infrastructure & Database Foundation (2/2 plans) — completed 2026-02-21
- [x] Phase 30: Dashboard & Metrics (2/2 plans) — completed 2026-02-21
- [x] Phase 31: Agent Board (2/2 plans) — completed 2026-02-21
- [x] Phase 32: Memory, Office & Visualization (3/3 plans) — completed 2026-02-21

Full details: [milestones/v2.5-ROADMAP.md](milestones/v2.5-ROADMAP.md)

</details>

<details>
<summary>✅ v2.6 Content Pipeline Hardening (Phase 33) — SHIPPED 2026-02-23</summary>

- [x] Phase 33: Content Pipeline Improvements (4/4 plans) — completed 2026-02-23

Full details: [milestones/v2.6-ROADMAP.md](milestones/v2.6-ROADMAP.md)

</details>

### v2.7 YOLO Dev (In Progress)

**Milestone Goal:** Bob autonomously picks a wild project idea and builds a working prototype overnight, with a YOLO dashboard in Mission Control to track all builds.

- [x] **Phase 38: Infrastructure Foundation** - yolo.db, build directory, bind-mounts, single gateway restart
- [x] **Phase 39: Build Pipeline** - Skill, cron, reference docs, interests file, guardrails, end-to-end validation, gap closure (completed 2026-02-25)
- [x] **Phase 40: YOLO Dashboard** - Mission Control /yolo page with build history cards and status filtering (completed 2026-02-25)
- [ ] **Phase 41: Briefing & Notifications** - Morning briefing section, weekly digest, Slack DM notifications

## Phase Details

### Phase 38: Infrastructure Foundation
**Goal**: Storage layer and sandbox access exist so Bob can write builds and log metadata
**Depends on**: Nothing (first phase in v2.7)
**Requirements**: INFRA-01, INFRA-02, INFRA-03
**Success Criteria** (what must be TRUE):
  1. yolo.db exists at ~/clawd/yolo-dev/yolo.db with the builds table schema and can be read/written programmatically (Python sqlite3) from inside the Docker sandbox at /workspace/yolo-dev/yolo.db
  2. ~/clawd/yolo-dev/ directory exists on the host and is bind-mounted to /workspace/yolo-dev/ in the sandbox with read-write access
  3. Bob can create a numbered build directory (e.g., /workspace/yolo-dev/001-test/) with a README.md inside it from within a sandbox session
  4. Gateway has been restarted exactly once with all bind-mount and cron config changes batched together
**Plans**: 2 plans

Plans:
- [x] 38-01-PLAN.md -- Create yolo.db with builds table schema, configure bind-mount, restart gateway
- [x] 38-02-PLAN.md -- Validate infrastructure end-to-end from sandbox, 000-test/ smoke test

### Phase 39: Build Pipeline
**Goal**: Bob can autonomously generate an idea, build a working prototype, log everything to yolo.db, and deliver a summary -- triggered by a nightly cron
**Depends on**: Phase 38
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, BUILD-06, BUILD-07, BUILD-08, BUILD-09
**Success Criteria** (what must be TRUE):
  1. A nightly cron fires at ~11 PM PT in an isolated Haiku session and Bob executes a full build cycle without human intervention
  2. Bob generates 3-5 candidate ideas informed by YOLO_INTERESTS.md and personal context, picks one with reasoning, and logs candidates to ideas.md in the build directory
  3. Build produces a working prototype (Python stdlib + vanilla HTML/JS) constrained to 100-500 LOC and 2-6 files, with build status tracked through idea/building/testing/success/partial/failed in yolo.db
  4. Bob self-evaluates the build on a 1-5 scale with written reasoning, and writes POSTMORTEM.md on failure or partial completion
  5. Hard guardrails enforced: 15-turn cap, 30-minute timeout, no pip/npm installs outside /workspace/, tech stack variety (no same stack 3x in a row)
**Plans**: 3 plans (all complete)

Plans:
- [x] 39-01-PLAN.md -- Create YOLO_BUILD.md + YOLO_INTERESTS.md protocol docs on EC2, seed 001-chronicle into yolo.db
- [x] 39-02-PLAN.md -- Register yolo-dev-overnight cron job, manual trigger end-to-end validation
- [x] 39-03-PLAN.md -- Gap closure: fix cron-triggered build execution + add 15-turn cap guardrail

### Phase 40: YOLO Dashboard
**Goal**: Andy can view all YOLO builds, their status, scores, and tech stacks on a dedicated Mission Control page
**Depends on**: Phase 38 (yolo.db schema), Phase 39 (real build data to verify against)
**Requirements**: DASH-01
**Success Criteria** (what must be TRUE):
  1. Mission Control has a /yolo route accessible from the navbar that displays build history as cards with status badges (color-coded), self-scores, descriptions, and tech stack tags
  2. Build cards are sorted newest-first and can be filtered by status (all/success/partial/failed)
  3. Page auto-refreshes via SWR and displays accurate data from yolo.db within 30 seconds of a build completing
**Plans**: 2 plans

Plans:
- [x] 40-01-PLAN.md -- Register yolo.db, query module, API route
- [x] 40-02-PLAN.md -- YoloBuildCard component, /yolo page with filters, navbar link

### Phase 41: Briefing & Notifications
**Goal**: Andy learns about YOLO build results through existing communication channels without checking the dashboard
**Depends on**: Phase 39 (builds running), Phase 40 (dashboard exists)
**Requirements**: DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Morning briefing includes a Section 11 with last night's YOLO build: project name, status, self-score, and one-line description (or graceful "No build last night" when none ran)
  2. Weekly review includes a YOLO digest: total builds that week, best-rated build, tech stack distribution, and emerging patterns
  3. Bob sends a Slack DM notification when a build starts ("Starting YOLO build: {name}") and when it completes ("YOLO build complete: {name} -- {status}, score {N}/5")
**Plans**: TBD

Plans:
- [ ] 41-01: TBD
- [ ] 41-02: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-11 | v2.0 | 22/22 | Complete | 2026-02-09 |
| 12-18 | v2.1 | 14/14 | Complete | 2026-02-09 |
| 19-23 | v2.2 | 8/8 | Complete | 2026-02-17 |
| 24-28 | v2.4 | 9/9 | Complete | 2026-02-21 |
| 29-32 | v2.5 | 9/9 | Complete | 2026-02-22 |
| 33 | v2.6 | 4/4 | Complete | 2026-02-23 |
| 38 | v2.7 | Complete    | 2026-02-24 | 2026-02-24 |
| 39 | v2.7 | Complete    | 2026-02-25 | 2026-02-25 |
| 40 | v2.7 | 2/2 | Complete | 2026-02-25 |
| 41 | v2.7 | 0/2 | Not started | - |

**Total: 33 phases shipped, 66 plans completed, 7 milestones shipped**
**v2.7: 4 phases, ~8 plans planned (7 complete)**

---
*Updated: 2026-02-25 -- Phase 40 complete (dashboard + API). Next: Phase 41 (briefing & notifications).*
