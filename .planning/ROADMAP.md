# Roadmap: Proactive Daily Companion

## Milestones

- ✅ **v2.0 Proactive Daily Companion** — Phases 1-11 (shipped 2026-02-09)
- ✅ **v2.1 Content Marketing Pipeline** — Phases 12-18 (shipped 2026-02-09)
- ✅ **v2.2 Resend Email Integration** — Phases 19-23 (shipped 2026-02-17)
- ✅ **v2.3 Security & Platform Hardening** — Merged into v2.4 (0 phases executed)
- 🚧 **v2.4 Content Distribution & Platform Hardening** — Phases 24-29 (in progress)

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

### 🚧 v2.4 Content Distribution & Platform Hardening (In Progress)

**Milestone Goal:** Turn the content pipeline into a distribution engine -- auto-send weekly digests to subscribers via Resend -- while folding in deferred security hardening, observability, email domain hardening, and platform cleanup from v2.3.

- [x] **Phase 24: Critical Security Update** — Update OpenClaw to v2026.2.17 and install SecureClaw security plugin (completed 2026-02-18)
- [ ] **Phase 25: Post-Update Audit** — Verify all crons, skills, agents, and injection protections survived the update
- [ ] **Phase 26: Agent Observability** — Add LLM hooks, activity summaries, and observability briefing section
- [ ] **Phase 27: Email Domain Hardening** — Escalate DMARC, execute warmup checklist, verify health metrics
- [ ] **Phase 28: Platform Cleanup** — Reduce Gmail scope, resolve doctor warnings, adopt config aliases
- [ ] **Phase 29: Content Distribution** — Subscriber audience, weekly digest compilation and send via Resend Broadcasts

## Phase Details

### Phase 24: Critical Security Update
**Goal**: Bob is running on a patched, security-audited OpenClaw with runtime behavioral protections active
**Depends on**: Nothing (first phase of v2.4)
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. `openclaw --version` reports v2026.2.17 on EC2
  2. SecureClaw plugin is installed and its 51-check audit completes with zero critical failures
  3. SecureClaw's 15 runtime behavioral rules are active (external content sandboxed, credential access blocked, destructive commands gated)
  4. Gateway service is running and Bob responds to a Slack DM
**Plans**: 2 plans

Plans:
- [ ] 24-01-PLAN.md -- Baseline, backup & OpenClaw update to v2026.2.17
- [ ] 24-02-PLAN.md -- SecureClaw plugin install, audit, behavioral rules & smoke test

### Phase 25: Post-Update Audit
**Goal**: Every existing automation is confirmed functional after the major version jump, and new prompt injection protections are verified
**Depends on**: Phase 24
**Requirements**: SEC-04, SEC-05, SEC-06, SEC-07
**Success Criteria** (what must be TRUE):
  1. All 20 cron jobs appear in `openclaw cron list` and fire on their next scheduled run without errors
  2. All 10 skills appear in `openclaw skill list` and Bob can invoke each without "skill not found"
  3. All 7 agents respond to a heartbeat or direct message (main, landos, rangeos, ops, quill, sage, ezra)
  4. Browser/web content fetched by Bob is treated as untrusted -- SecureClaw injection protections block embedded prompt injection payloads
**Plans**: 2 plans

Plans:
- [ ] 25-01-PLAN.md -- Manifest verification audit (20 crons, 13 skills, 7 agents) with inline fixes
- [ ] 25-02-PLAN.md -- Prompt injection protection verification (browser + email vectors, 8 payloads)

### Phase 26: Agent Observability
**Goal**: Bob can see how all agents are using LLM resources and surfaces anomalies in the morning briefing
**Depends on**: Phase 24 (hooks require v2026.2.17; independent of phases 25, 27, 28)
**Requirements**: OBS-01, OBS-02, OBS-03
**Success Criteria** (what must be TRUE):
  1. LLM hook payloads are configured and firing (verified by log output after at least one agent turn)
  2. Bob can report per-agent token usage, model distribution (Haiku/Sonnet/Opus), and turn counts for the last 24 hours
  3. Morning briefing includes an "Agent Observability" section that flags anomalous usage spikes, errors, or rate limit proximity
**Plans**: TBD

Plans:
- [ ] 26-01: TBD

### Phase 27: Email Domain Hardening
**Goal**: Email domain reputation is production-grade with enforced DMARC and verified deliverability -- prerequisite for subscriber sends in Phase 29
**Depends on**: Phase 24 (gateway must be running; independent of phases 25, 26, 28)
**Requirements**: EML-01, EML-02, EML-03
**Success Criteria** (what must be TRUE):
  1. DMARC DNS record for mail.andykaufman.net shows `p=quarantine` (verified via `dig TXT _dmarc.mail.andykaufman.net`)
  2. WARMUP.md 5-step checklist is fully executed: DNS verified, authentication tested, inbox placement confirmed, monitoring active, escalation complete
  3. Email health metrics in morning briefing show bounce rate < 5% and complaint rate < 0.1% over the most recent 7-day window
**Plans**: TBD

Plans:
- [ ] 27-01: TBD

### Phase 28: Platform Cleanup
**Goal**: All deferred maintenance items resolved -- clean doctor output, minimal OAuth scopes, modern config patterns
**Depends on**: Phase 24 (gateway must be running; independent of phases 25, 26, 27)
**Requirements**: CLN-01, CLN-02, CLN-03, CLN-04, CLN-05
**Success Criteria** (what must be TRUE):
  1. `gog auth list` shows Gmail OAuth with only required scopes (excess scopes removed; minimum: gmail.readonly + gmail.send + gmail.modify + calendar.readonly)
  2. `openclaw doctor` outputs zero warnings (deprecated auth profile migrated, legacy session key resolved)
  3. `openclaw.json` uses `dmPolicy`/`allowFrom` config aliases where applicable to current setup
  4. `gateway.remote.url` is documented in PROJECT.md and verified reachable from VPS after update
**Plans**: TBD

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD

### Phase 29: Content Distribution
**Goal**: Published articles reach subscribers automatically via weekly digest emails sent through Resend Broadcasts
**Depends on**: Phase 27 (DMARC must be at p=quarantine before subscriber sends begin)
**Requirements**: DIST-01, DIST-02, DIST-03, DIST-04, DIST-05
**Success Criteria** (what must be TRUE):
  1. Resend Audience exists with a seed list of industry contacts, and Bob can add/remove contacts via skill command
  2. Weekly cron fires and compiles all articles published in the last 7 days from content.db into a digest
  3. Digest email includes article titles, summaries, and links to airspaceintegration.com -- formatted with the existing HTML email template
  4. Digest is sent via Resend Broadcasts API to the subscriber audience on a consistent weekly schedule
**Plans**: TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 24 -> 25 -> 26 -> 27 -> 28 -> 29
Note: Phases 26, 27, 28 depend only on Phase 24 (not each other) but execute sequentially for simplicity. Phase 29 hard-depends on Phase 27.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Update, Memory & Security | v2.0 | 2/2 | Complete | 2026-02-07 |
| 2. Oura Ring Integration | v2.0 | 1/1 | Complete | 2026-02-08 |
| 3. Daily Briefing & Rate Limits | v2.0 | 3/3 | Complete | 2026-02-08 |
| 4. MCP Servers | v2.0 | 1/1 | Complete | 2026-02-08 |
| 5. Govee & Wyze Integrations | v2.0 | 2/2 | Complete | 2026-02-08 |
| 6. Multi-Agent Gateway | v2.0 | 2/2 | Complete | 2026-02-08 |
| 7. Multi-Agent Slack Channels | v2.0 | 1/1 | Complete | 2026-02-09 |
| 8. Multi-Agent Automation | v2.0 | 2/2 | Complete | 2026-02-09 |
| 9. Proactive Agent Patterns | v2.0 | 3/3 | Complete | 2026-02-08 |
| 10. Agentic Coding Workflow | v2.0 | 2/2 | Complete | 2026-02-09 |
| 11. Document Processing | v2.0 | 2/2 | Complete | 2026-02-09 |
| 12. Content DB + Agent Setup | v2.1 | 3/3 | Complete | 2026-02-09 |
| 13. Topic Research | v2.1 | 2/2 | Complete | 2026-02-09 |
| 14. Writing Pipeline | v2.1 | 2/2 | Complete | 2026-02-09 |
| 15. Review Pipeline | v2.1 | 2/2 | Complete | 2026-02-09 |
| 16. WordPress Publishing | v2.1 | 2/2 | Complete | 2026-02-09 |
| 17. Social Promotion | v2.1 | 1/1 | Complete | 2026-02-09 |
| 18. Pipeline Monitoring | v2.1 | 2/2 | Complete | 2026-02-09 |
| 19. Outbound Email Foundation | v2.2 | 2/2 | Complete | 2026-02-16 |
| 20. Inbound Email Infrastructure | v2.2 | 2/2 | Complete | 2026-02-17 |
| 21. Inbound Email Processing | v2.2 | 2/2 | Complete | 2026-02-17 |
| 22. Domain Warmup & Hardening | v2.2 | 1/1 | Complete | 2026-02-17 |
| 23. Email Integration Gap Closure | v2.2 | 1/1 | Complete | 2026-02-17 |
| 24. Critical Security Update | 2/2 | Complete    | 2026-02-18 | - |
| 25. Post-Update Audit | 1/2 | In Progress|  | - |
| 26. Agent Observability | v2.4 | 0/? | Not started | - |
| 27. Email Domain Hardening | v2.4 | 0/? | Not started | - |
| 28. Platform Cleanup | v2.4 | 0/? | Not started | - |
| 29. Content Distribution | v2.4 | 0/? | Not started | - |

---
*Updated: 2026-02-17 -- v2.4 Content Distribution & Platform Hardening roadmap created*
