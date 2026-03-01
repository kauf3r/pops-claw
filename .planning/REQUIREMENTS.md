# Requirements: Pops-Claw

**Defined:** 2026-03-01
**Core Value:** Proactive AI companion with Mission Control Dashboard as single pane of glass.

## v2.8 Requirements

Requirements for v2.8 Bug Fixes & Dashboard Polish. Each maps to roadmap phases.

### Bug Fixes

- [x] **BUG-01**: Ezra publish-check creates WordPress drafts for approved articles
- [x] **BUG-02**: ~~AeroVironment fly_status values are tracked and displayed (not null)~~ — Re-scoped: fly_status is in Supabase (airspace-operations-dashboard), not content.db. Tracked as separate task.

### YOLO Detail Page

- [ ] **YOLO-01**: User can click a build card to navigate to /yolo/{slug} detail page
- [ ] **YOLO-02**: Detail page displays full build log with timestamps
- [ ] **YOLO-03**: Detail page displays errors encountered during build
- [ ] **YOLO-04**: Detail page displays self-evaluation scores and reasoning
- [ ] **YOLO-05**: Detail page lists all files created during build

### Build Trends

- [ ] **TREND-01**: /yolo page shows build success rate chart over time
- [ ] **TREND-02**: /yolo page shows average self-score chart over time

### Agent Board

- [ ] **AGENT-01**: Agent cards show context/token usage indicators (visual bar or percentage)
- [ ] **AGENT-02**: Agent board has consistent visual styling and spacing

### Build Artifacts

- [ ] **PREV-01**: User can preview index.html build artifacts in an iframe on the detail page
- [ ] **PREV-02**: Builds older than 30 days are automatically cleaned up (top-rated retained)

## Future Requirements

### Content Distribution (deferred from v2.4)

- **DIST-01**: Subscriber digest via Resend Broadcasts
- **DIST-02**: Pitch copy generation for outreach

### Voice Notes (deferred)

- **VN-01**: Process 28 stuck voice-memory-v2 backlog notes

## Out of Scope

| Feature | Reason |
|---------|--------|
| LIFT Summit prep | Separate workstream, not a code milestone |
| Range Ops display | Deferred to future ops-focused milestone |
| Pre-ops workflow | Deferred to future ops-focused milestone |
| Voice input | Evaluate at day 60 |
| Public API exposure | Not needed for personal use |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUG-01 | Phase 43 | Done |
| BUG-02 | Phase 43 | Re-scoped (pops-claw-9b3) |
| YOLO-01 | Phase 44 | Pending |
| YOLO-02 | Phase 44 | Pending |
| YOLO-03 | Phase 44 | Pending |
| YOLO-04 | Phase 44 | Pending |
| YOLO-05 | Phase 44 | Pending |
| TREND-01 | Phase 45 | Pending |
| TREND-02 | Phase 45 | Pending |
| AGENT-01 | Phase 46 | Pending |
| AGENT-02 | Phase 46 | Pending |
| PREV-01 | Phase 47 | Pending |
| PREV-02 | Phase 47 | Pending |

**Coverage:**
- v2.8 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-03-01*
*Last updated: 2026-03-01 -- traceability updated with phase mappings*
