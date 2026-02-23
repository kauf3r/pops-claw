# Roadmap: Proactive Daily Companion

## Milestones

- ✅ **v2.0 Proactive Daily Companion** — Phases 1-11 (shipped 2026-02-09)
- ✅ **v2.1 Content Marketing Pipeline** — Phases 12-18 (shipped 2026-02-09)
- ✅ **v2.2 Resend Email Integration** — Phases 19-23 (shipped 2026-02-17)
- ✅ **v2.3 Security & Platform Hardening** — Merged into v2.4 (0 phases executed)
- ✅ **v2.4 Content Distribution & Platform Hardening** — Phases 24-28 (shipped 2026-02-21)
- ✅ **v2.5 Mission Control Dashboard** — Phases 29-32 (shipped 2026-02-22)

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

### v2.6 Agent Memory & Dashboard Polish

- [x] **Phase 34: Memory Curation & Bootstrap** - Curate MEMORY.md under budget, fix flush consistency
- [ ] **Phase 35: Memory Retrieval Discipline** - Retrieval instructions, LEARNINGS.md, content agent memory
- [ ] **Phase 36: Memory Health Monitoring** - Dashboard panel for per-agent memory metrics
- [ ] **Phase 37: Agent Board Polish** - Context usage indicators and visual refinements

## Phase Details

### Phase 34: Memory Curation & Bootstrap
**Goal**: Bob's MEMORY.md fits within the 200-line auto-load budget and memory flushes fire reliably across all session types
**Depends on**: Nothing (first phase of v2.6)
**Requirements**: MEM-01, MEM-02
**Success Criteria** (what must be TRUE):
  1. MEMORY.md is under 150 lines with reference material moved to docs/ directory files that agents can retrieve on demand
  2. Bob's daily log entries appear for every active day, not just days with long sessions
  3. Gateway restart with curated MEMORY.md shows reduced bootstrap token consumption in observability.db
**Plans**: 2 plans (1 wave)

Plans:
- [x] 34-01: Curate MEMORY.md under budget — move 6+ reference sections to docs/, trim to 120-140 lines
- [x] 34-02: Fix memory flush consistency — daily-memory-flush cron + lower softThresholdTokens to 3000

### Phase 35: Memory Retrieval Discipline
**Goal**: Agents actively search their memory before starting tasks, and content agents retain context across cron-triggered sessions
**Depends on**: Phase 34 (freed bootstrap budget makes room for retrieval instructions)
**Requirements**: MEM-03, MEM-04, MEM-05
**Success Criteria** (what must be TRUE):
  1. AGENTS.md boot sequence includes explicit instructions to search daily logs and LEARNINGS.md before executing tasks
  2. LEARNINGS.md contains seeded entries from real operational knowledge (not an empty template)
  3. Quill, Sage, and Ezra each have bootstrap memory files in their agent workspace so cron sessions start with prior context
  4. An agent asked about something from a previous session can retrieve it via memory search without being told where to look
**Plans**: 2 plans (2 waves)

Plans:
- [ ] 35-01-PLAN.md -- Add Memory Protocol to AGENTS.md + create/seed LEARNINGS.md with MARKER entry
- [ ] 35-02-PLAN.md -- Create BOOTSTRAP.md for Quill, Sage, and Ezra content agents

### Phase 36: Memory Health Monitoring
**Goal**: Andy can see the health of every agent's memory system at a glance in Mission Control
**Depends on**: Phase 35 (memory system must be stable before monitoring it)
**Requirements**: MON-01, MON-02, MON-03
**Success Criteria** (what must be TRUE):
  1. Mission Control shows per-agent memory chunk count and last-updated timestamp on a memory health panel
  2. MEMORY.md line count is displayed alongside the 200-line auto-load limit so Andy can see how close to budget each agent is
  3. Memory flush frequency (flushes per day over last 7 days) is visible as a trend indicator
  4. The panel updates on the existing 30s SWR polling cycle without new infrastructure
**Plans**: TBD

### Phase 37: Agent Board Polish
**Goal**: Agent cards show context utilization at a glance and the board looks polished and professional
**Depends on**: Phase 36 (context indicators change card layout; polish after layout is final)
**Requirements**: DASH-01, DASH-02
**Success Criteria** (what must be TRUE):
  1. Each agent card on /agents shows context window utilization as a colored progress bar (green/amber/red)
  2. Each agent card shows cache hit rate and 24h cost
  3. Agent board has refined layout, spacing, and card hierarchy that feels intentional rather than scaffolded
  4. Inactive agents (no recent LLM calls) show dash placeholders instead of misleading zeros
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 34 -> 35 -> 36 -> 37

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 34. Memory Curation & Bootstrap | v2.6 | Complete    | 2026-02-23 | 2026-02-23 |
| 35. Memory Retrieval Discipline | v2.6 | 0/2 | Planned | - |
| 36. Memory Health Monitoring | v2.6 | 0/TBD | Not started | - |
| 37. Agent Board Polish | v2.6 | 0/TBD | Not started | - |

---
*Updated: 2026-02-23 -- Phase 34 complete (2/2 plans). Next: Phase 35 Memory Retrieval Discipline.*
