# Requirements: Pops-Claw v2.6

**Defined:** 2026-02-23
**Core Value:** Make Bob's memory system reliable and give Andy visibility into memory health via Mission Control.

## v2.6 Requirements

### Memory System

- [ ] **MEM-01**: MEMORY.md curated from 304 lines to under 150 lines, reference docs moved to docs/ directory
- [ ] **MEM-02**: Memory flush triggers consistently across session types (daily logs written for all active days, not just long sessions)
- [ ] **MEM-03**: AGENTS.md boot sequence includes explicit retrieval instructions (search daily logs and LEARNINGS.md before tasks)
- [ ] **MEM-04**: LEARNINGS.md activated with seeded entries from existing operational knowledge (not empty framework)
- [ ] **MEM-05**: Content agents (Quill, Sage, Ezra) have bootstrap memory files so they retain context across cron sessions

### Memory Health Monitoring

- [ ] **MON-01**: Mission Control memory health panel shows per-agent chunk count and last-updated timestamp
- [ ] **MON-02**: Memory health panel shows MEMORY.md line count vs 200-line auto-load limit
- [ ] **MON-03**: Memory health panel shows memory flush frequency (flushes per day over last 7 days)

### Dashboard Polish

- [ ] **DASH-01**: Agent board cards show context usage indicators (token consumption as percentage of context window)
- [ ] **DASH-02**: Agent board visual refinements (carried from v2.5 Phase 31.2 -- layout, spacing, card hierarchy)

## Future Requirements

### Memory System (v2.7+)

- **MEM-F01**: Hybrid search backend (QMD or BM25+vectors+reranking) replacing pure FTS5
- **MEM-F02**: Automated MARKER retrieval test with pass/fail indicator in Mission Control
- **MEM-F03**: Memory curation alerts when MEMORY.md exceeds line threshold
- **MEM-F04**: Handover protocol -- agent writes current context to daily log before session end or model switch

### Dashboard (v2.7+)

- **DASH-F01**: Daily log timeline view (chronological, not just card grid)
- **DASH-F02**: Dead code cleanup (global-search.tsx Convex stub)

## Out of Scope

| Feature | Reason |
|---------|--------|
| QMD/hybrid search backend | Complexity -- validate FTS5 is actually insufficient first before upgrading |
| WebSocket real-time memory updates | Memory changes daily, not in real-time -- 30s SWR polling sufficient |
| Multi-agent memory comparison view | Single-user dashboard -- not needed for ops monitoring |
| Gateway restart automation | Too risky to automate -- manual restart with DM re-establish is safer |
| LEARNINGS.md auto-population from agent errors | Risk of noise -- manual curation preferred until pattern is proven |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEM-01 | Phase 34 | Pending |
| MEM-02 | Phase 34 | Pending |
| MEM-03 | Phase 35 | Pending |
| MEM-04 | Phase 35 | Pending |
| MEM-05 | Phase 35 | Pending |
| MON-01 | Phase 36 | Pending |
| MON-02 | Phase 36 | Pending |
| MON-03 | Phase 36 | Pending |
| DASH-01 | Phase 37 | Pending |
| DASH-02 | Phase 37 | Pending |

**Coverage:**
- v2.6 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after renumber -- all 10 requirements mapped to phases 34-37 (Phase 33 reserved for content-pipeline on main)*
