# Requirements: Pops-Claw v2.4

**Defined:** 2026-02-17
**Core Value:** Proactive daily companion — distribute content to subscribers, harden security, and gain observability.

## v2.4 Requirements

### Subscriber Management

- [ ] **DIST-01**: Resend Audience created with initial seed list of industry contacts
- [ ] **DIST-02**: Bob can add and remove contacts from subscriber list via skill command

### Weekly Digest

- [ ] **DIST-03**: Weekly cron compiles articles published in the last 7 days from content.db
- [ ] **DIST-04**: Digest email includes article titles, summaries, and links to airspaceintegration.com
- [ ] **DIST-05**: Digest sent via Resend Broadcasts API to subscriber audience on a consistent weekly schedule

### Security Update

- [ ] **SEC-01**: OpenClaw updated from v2026.2.6-3 to v2026.2.17 (CVE-2026-25253 patched)
- [ ] **SEC-02**: SecureClaw plugin installed and 51-check audit passes with no critical findings
- [ ] **SEC-03**: SecureClaw runtime behavioral rules active (15 rules governing external content, credentials, destructive commands)
- [ ] **SEC-04**: Post-update audit confirms all 20 cron jobs firing on schedule
- [ ] **SEC-05**: Post-update audit confirms all 10 skills detected and functional
- [ ] **SEC-06**: Post-update audit confirms all 7 agents heartbeating/responding
- [ ] **SEC-07**: New prompt injection protections verified (browser/web content "untrusted by default")

### Observability

- [ ] **OBS-01**: `llm_input`/`llm_output` hook payloads configured for agent monitoring
- [ ] **OBS-02**: Agent activity summary (token usage, model distribution, turn counts) available to Bob
- [ ] **OBS-03**: Morning briefing includes agent observability section (anomalous usage, errors, rate limit proximity)

### Email Hardening

- [ ] **EML-01**: DMARC policy escalated from p=none to p=quarantine after confirming 2 clean weeks
- [ ] **EML-02**: WARMUP.md 5-step checklist executed (DNS verified, auth tested, inbox placement confirmed, monitoring active)
- [ ] **EML-03**: Email health metrics (bounce/complaint rates) trending clean in morning briefing

### Platform Cleanup

- [ ] **CLN-01**: Gmail OAuth scope reduction (remove 2 excess scopes, re-auth gog)
- [ ] **CLN-02**: Doctor warnings resolved — deprecated auth profile migrated to setup-token
- [ ] **CLN-03**: Doctor warnings resolved — legacy session key canonicalization
- [ ] **CLN-04**: `dmPolicy`/`allowFrom` config aliases adopted (if applicable to current setup)
- [ ] **CLN-05**: `gateway.remote.url` config documented and verified post-update

## Future Requirements

### Deferred from v2.4

- **DIST-06**: Per-article subscriber notification email on publish (after human approval)
- **DIST-07**: Pitch copy generation for published articles (human sends manually)
- **DIST-08**: WordPress signup form for organic subscriber growth
- **MSG-01**: `message_sending` hooks for outbound message gating/filtering
- **DISC-01**: Discord Components v2 (buttons, selects, modals)
- **TEL-01**: Telegram poll support
- **IOS-01**: iOS alpha node app integration

## Out of Scope

| Feature | Reason |
|---------|--------|
| Per-article notifications | Digest-only for now; avoids double-sending |
| Pitch copy generation | Human handles outreach manually for now |
| Public subscriber signup form | Seed list only; no organic growth mechanism yet |
| Full automation (no human gate) | Safety over speed; human approves publish |
| Social media API integration | Copy-only promotion continues from v2.1 |
| ClawHub skills | Not used; ClawHavoc risk not applicable |
| vLLM provider | No local model hosting planned |
| Multi-node distributed deployment | Single EC2 sufficient |
| External observability SaaS | Privacy risk, overkill for single-user deployment |
| Full LLM prompt/response logging | PII risk; metadata only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 24 | Pending |
| SEC-02 | Phase 24 | Pending |
| SEC-03 | Phase 24 | Pending |
| SEC-04 | Phase 25 | Pending |
| SEC-05 | Phase 25 | Pending |
| SEC-06 | Phase 25 | Pending |
| SEC-07 | Phase 25 | Pending |
| OBS-01 | Phase 26 | Pending |
| OBS-02 | Phase 26 | Pending |
| OBS-03 | Phase 26 | Pending |
| EML-01 | Phase 27 | Pending |
| EML-02 | Phase 27 | Pending |
| EML-03 | Phase 27 | Pending |
| CLN-01 | Phase 28 | Pending |
| CLN-02 | Phase 28 | Pending |
| CLN-03 | Phase 28 | Pending |
| CLN-04 | Phase 28 | Pending |
| CLN-05 | Phase 28 | Pending |
| DIST-01 | Phase 29 | Pending |
| DIST-02 | Phase 29 | Pending |
| DIST-03 | Phase 29 | Pending |
| DIST-04 | Phase 29 | Pending |
| DIST-05 | Phase 29 | Pending |

**Coverage:**
- v2.4 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after roadmap creation (traceability complete)*
