# Requirements: Pops-Claw v2.9 Memory System Overhaul

**Defined:** 2026-03-08
**Core Value:** Bob's memory system actually works — information survives compaction, retrieval finds it, and monitoring proves it.

## v2.9 Requirements

### Compaction Config

- [ ] **COMP-01**: reserveTokensFloor raised from 24K to 40K in openclaw.json
- [ ] **COMP-02**: softThresholdTokens raised from 1.5K to 8K in openclaw.json
- [ ] **COMP-03**: Gateway restarted and memory flush verified to fire in a test session

### Memory Search

- [ ] **SRCH-01**: QMD collections bootstrapped with `qmd update && qmd embed`, verified with test query
- [ ] **SRCH-02**: Hybrid search weights configured (vectorWeight: 0.7, textWeight: 0.3) in memorySearch config

### Memory Content

- [ ] **CONT-01**: MEMORY.md created at correct path (`~/clawd/agents/main/MEMORY.md`) and indexed by QMD
- [ ] **CONT-02**: MEMORY.md seeded with curated long-term knowledge (key decisions, preferences, system facts)
- [ ] **CONT-03**: Memory flush prompt improved to produce richer daily summaries

### Retrieval Discipline

- [ ] **RETR-01**: Retrieval protocol added to AGENTS.md with specific trigger categories and example queries
- [ ] **RETR-02**: Daily memory flush cron rescheduled to end-of-day for better session summaries

### Health Monitoring

- [ ] **HLTH-01**: Memory health check script verifies daily logs exist, QMD indexing works, and search returns results
- [ ] **HLTH-02**: Health check runs on cron and alerts (via Slack DM) if memory system is broken

## Future Requirements

### Memory Expansion

- **MEXP-01**: Seed MEMORY.md for all 7 agents (not just Bob)
- **MEXP-02**: Mission Control /memory page health sparklines and indexing status
- **MEXP-03**: Git backup of workspace memory files with auto-commit cron
- **MEXP-04**: Raise contextTokens from 100K to 150K+ (after OOM risk assessment)

## Out of Scope

| Feature | Reason |
|---------|--------|
| contextTokens increase beyond 100K | OOM risk on t3.small (2GB RAM) — needs memory profiling first |
| Multi-agent MEMORY.md seeding | Bob is primary agent; others are cron-only and already have daily logs |
| Mission Control memory panel | Adds Next.js work to a config-focused milestone — defer to v2.10 |
| New memory backend | QMD + Gemini setup is sound; the infrastructure works, just needs config/behavioral fixes |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COMP-01 | Phase 51 | Pending |
| COMP-02 | Phase 51 | Pending |
| COMP-03 | Phase 51 | Pending |
| SRCH-01 | Phase 51 | Pending |
| SRCH-02 | Phase 51 | Pending |
| CONT-01 | Phase 52 | Pending |
| CONT-02 | Phase 52 | Pending |
| CONT-03 | Phase 52 | Pending |
| RETR-01 | Phase 53 | Pending |
| RETR-02 | Phase 53 | Pending |
| HLTH-01 | Phase 54 | Pending |
| HLTH-02 | Phase 54 | Pending |

**Coverage:**
- v2.9 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 — Phase mappings added (12/12 covered)*
