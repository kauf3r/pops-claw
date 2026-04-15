# Requirements: Pops-Claw v2.11 Knowledge Brain

**Defined:** 2026-04-15
**Core Value:** Bob gets a persistent world knowledge layer via gbrain — people, companies, concepts, and relationships compound over time, survive session compaction, and are searchable via hybrid RAG.

## v2.11 Requirements

### Infrastructure

- [ ] **INFRA-01**: gbrain CLI installed on EC2 with PGLite engine and compiled binary
- [ ] **INFRA-02**: gbrain binary bind-mounted into Docker sandbox at `/usr/local/bin/gbrain`
- [ ] **INFRA-03**: `~/.gbrain/` directory bind-mounted into sandbox for PGLite database access
- [ ] **INFRA-04**: OpenAI API key available in sandbox environment for embeddings

### Knowledge Import

- [ ] **KNOW-01**: claude-life-os repo cloned on EC2 and LLM-context wiki (200+ pages) imported into gbrain
- [ ] **KNOW-02**: MEMORY.md imported as seed brain content
- [ ] **KNOW-03**: All imported pages embedded with vector embeddings via `gbrain embed`
- [ ] **KNOW-04**: Incremental sync cron keeps brain current with claude-life-os git repo

### Brain Operations

- [ ] **BRAIN-01**: Bob checks gbrain before external APIs when asked about people, companies, or concepts
- [ ] **BRAIN-02**: Bob captures entity mentions from conversations into gbrain pages (signal detection)
- [ ] **BRAIN-03**: BRAIN_OPS.md workspace protocol doc deployed with lookup, capture, and citation patterns
- [ ] **BRAIN-04**: Nightly embed cron indexes new/modified brain pages

### Health & Monitoring

- [ ] **HEALTH-01**: Weekly brain health check cron reports stats and issues to Slack
- [ ] **HEALTH-02**: `gbrain doctor` passes all checks after setup

## Future Requirements (Deferred)

- **ADV-01**: Meeting prep auto-pulls attendee dossiers from brain before meetings
- **ADV-02**: Dream cycle (nightly entity enrichment, citation fixing, orphan detection)
- **ADV-03**: Email/meeting ingestion pipelines (email-to-brain, meeting-sync recipes)
- **ADV-04**: Migration to Supabase if brain exceeds PGLite capacity

## Out of Scope

| Feature | Reason |
|---------|--------|
| gbrain MCP daemon mode | RAM constraint — t3.small has 2GB, gateway uses 1.1GB. CLI mode is sufficient. |
| gbrain skill system (25 skills) | Bob uses workspace protocol docs, not gbrain triggers. BRAIN_OPS.md wraps CLI. |
| Replace QMD memory | QMD handles operational memory (compaction, flush). gbrain handles world knowledge. Different domains. |
| gbrain publish (HTML pages) | Not a current use case for Bob |
| gbrain task manager | Bob uses coordination.db for tasks |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | TBD | Pending |
| INFRA-02 | TBD | Pending |
| INFRA-03 | TBD | Pending |
| INFRA-04 | TBD | Pending |
| KNOW-01 | TBD | Pending |
| KNOW-02 | TBD | Pending |
| KNOW-03 | TBD | Pending |
| KNOW-04 | TBD | Pending |
| BRAIN-01 | TBD | Pending |
| BRAIN-02 | TBD | Pending |
| BRAIN-03 | TBD | Pending |
| BRAIN-04 | TBD | Pending |
| HEALTH-01 | TBD | Pending |
| HEALTH-02 | TBD | Pending |

**Coverage:**
- v2.11 requirements: 14 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 14

---
*Requirements defined: 2026-04-15*
