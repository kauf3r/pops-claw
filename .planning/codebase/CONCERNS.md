# Codebase Concerns

**Analysis Date:** 2026-01-18

## Tech Debt

**Incomplete Pipeline Phases (Stub Implementations):**
- Issue: Pipeline modules (Phase 2-4) contain stub implementations returning placeholder data
- Files: `src/pipeline/core/campaign-engine.js`, `src/pipeline/core/data-manager.js`, `src/pipeline/core/kpi-tracker.js`
- Impact: Users may call methods expecting real functionality; stub methods return hardcoded/zero values creating silent failures
- Fix approach: Either complete implementations or throw NotImplementedError with clear phase references

**Missing Input Validation:**
- Issue: Property and UAS data processing lacks input validation before expensive API calls
- Files: `src/index.js:56` (landData), `src/index.js:77` (UAS data), `src/land/analyzer.js:17`
- Impact: Invalid data reaches Claude API, wastes tokens, returns unpredictable results
- Fix approach: Add JSON schema validation (e.g., Zod/Joi) at entry points before Claude API calls

**Missing Retry Logic:**
- Issue: Claude API calls fail immediately without retry on transient errors
- Files: `src/core/claude.js:73-77`, `src/index.js:62` (marked TODO)
- Impact: Network blips cause complete workflow failures; poor resilience
- Fix approach: Add exponential backoff retry (3 retries, 1s/2s/4s delays) around API calls

**No Caching Layer:**
- Issue: Identical property analyses trigger fresh API calls each time
- Files: `src/land/analyzer.js:16` (marked TODO)
- Impact: Redundant API costs; slow repeated analyses; no benefit from previous work
- Fix approach: Add simple in-memory cache keyed by property hash, or SQLite cache with TTL

**Database Type PostgreSQL Not Implemented:**
- Issue: PostgreSQL support promised but throws "coming in Phase 4" error
- Files: `src/pipeline/data/pipeline-database.js:82-83`
- Impact: Cannot scale beyond SQLite; misleading configuration options in pipeline-config.js
- Fix approach: Either implement PostgreSQL driver or remove config options and document SQLite-only

**External Service Health Checks Not Implemented:**
- Issue: Pipeline health check returns false for all external services (Land Insights, RocketPrint, Pebble CRM, AnswerForce)
- Files: `src/pipeline/pipeline-index.js:177-180`
- Impact: Health dashboard always shows services as unavailable; no monitoring of actual service status
- Fix approach: Implement basic ping/auth checks for each configured API

## Known Bugs

**Silent Empty Returns in Integration Services:**
- Symptoms: Methods return empty arrays/null instead of errors when external services fail
- Files: `src/services/today.js:35,57,66,79,92`, `src/integrations/rangeos-vps.js:139,198,258,305`, `src/integrations/beads.js:70,78,130,136,153`
- Trigger: Any failure in SSH, webhook, or CLI execution
- Workaround: Callers cannot distinguish "no data" from "service failed"

**Browser Automation Uses Generic Selectors:**
- Symptoms: County website scraping fails on most real county sites
- Files: `src/browser/automation.js:127-141`
- Trigger: Any county assessor website that doesn't match hardcoded selectors
- Workaround: Requires per-county selector customization, but no adapter pattern exists

## Security Considerations

**API Key Handling:**
- Risk: API keys logged partially in startup output (first 15 chars + last 4)
- Files: `config/index.js:93`, `test-config.js:30`
- Current mitigation: Only partial key shown, but still more than necessary
- Recommendations: Remove all key logging; use asterisks or "configured" status only

**SSH Credentials in Code:**
- Risk: Default VPS host IP and username hardcoded in source
- Files: `src/integrations/rangeos-vps.js:17-18` (IP: 165.22.139.214, user: officernd)
- Current mitigation: Environment variables can override
- Recommendations: Remove all default credentials; require explicit configuration

**StrictHostKeyChecking Disabled:**
- Risk: SSH connections skip host key verification, vulnerable to MITM
- Files: `src/integrations/rangeos-vps.js:36`
- Current mitigation: None
- Recommendations: Add known_hosts management or require explicit opt-in for insecure mode

**Browser Automation User Agent Spoofing:**
- Risk: Hardcoded fake Chrome user agent may violate website ToS
- Files: `src/browser/automation.js:34`
- Current mitigation: None
- Recommendations: Document legal implications; allow configurable user agent

## Performance Bottlenecks

**Sequential API Calls in Workflows:**
- Problem: Workflow methods call Claude API sequentially even when analyses are independent
- Files: `src/land/workflows.js:169-180` (generates 3 content types sequentially)
- Cause: await inside for-loop instead of Promise.all
- Improvement path: Use Promise.all for independent API calls; batch similar requests

**No Connection Pooling for Database:**
- Problem: SQLite uses single connection; no pooling for PostgreSQL path
- Files: `src/pipeline/data/pipeline-database.js`
- Current capacity: Limited concurrent database operations
- Scaling path: Add better-sqlite3 for sync operations or connection pool for async

**Bulk Analysis Serializes Batches:**
- Problem: Bulk property analysis processes batches sequentially with optional delays
- Files: `src/land/workflows.js:82-98`
- Current capacity: ~5 properties per batch, sequential processing
- Improvement path: Increase batch size; parallelize more aggressively with rate limiting

## Fragile Areas

**JSON Parsing from Claude Responses:**
- Files: `src/core/claude.js:474-487`
- Why fragile: Regex-based extraction of JSON from varied Claude response formats; assumes JSON code block or bare JSON object
- Safe modification: Add new patterns to parseJSONResponse(); test with sample responses
- Test coverage: No unit tests for JSON parsing edge cases

**CLI Command Parsing:**
- Files: `src/index.js:160-244`
- Why fragile: Simple switch statement; no argument parsing; hardcoded commands
- Safe modification: Extract to command registry; add argument parser (e.g., commander.js)
- Test coverage: Manual testing only; no automated CLI tests

**Beads CLI Text Parsing:**
- Files: `src/integrations/beads.js:84-103`
- Why fragile: Regex parsing of `bd ready` text output; format may change
- Safe modification: Prefer --json flag; update regex if format changes
- Test coverage: No unit tests for text parsing

## Scaling Limits

**SQLite for Pipeline:**
- Current capacity: Single-file database; write locks on concurrent access
- Limit: ~100 concurrent users; large batch imports may timeout
- Scaling path: Migrate to PostgreSQL (config exists but not implemented)

**In-Memory Service Stats:**
- Current capacity: Stats reset on restart; no persistence
- Limit: Loss of usage tracking across restarts
- Scaling path: Persist stats to database; add periodic snapshots (`src/core/claude.js:19-26`)

## Dependencies at Risk

**@anthropic-ai/sdk:**
- Risk: Single AI provider dependency; no abstraction layer
- Impact: Cannot switch to alternative models without major refactor
- Migration plan: Add AI service abstraction interface; implement adapters per provider

**Playwright (Optional):**
- Risk: Heavy dependency for browser automation; requires separate install
- Impact: Browser features fail if not installed; no graceful degradation
- Migration plan: Add lazy loading; clear error messages for missing optional dependencies

## Missing Critical Features

**No Test Framework Configured:**
- Problem: package.json test script echoes error; no Jest/Vitest configured
- Blocks: Cannot run automated tests; CI/CD integration impossible
- Files: `package.json:14`

**No Rate Limiting:**
- Problem: No protection against Claude API rate limits
- Blocks: Bulk operations may exhaust quota; no backpressure mechanism
- Files: All Claude API call sites

**No Authentication/Authorization:**
- Problem: CLI and services have no user authentication
- Blocks: Cannot secure multi-user deployment; no audit trail of who did what
- Files: All entry points

## Test Coverage Gaps

**Core Claude Service:**
- What's not tested: API error handling, JSON parsing edge cases, token counting accuracy
- Files: `src/core/claude.js`
- Risk: Claude API changes may break parsing silently; no regression detection
- Priority: High

**Land Analyzer Scoring:**
- What's not tested: Score calculation boundary conditions, flag identification logic
- Files: `src/land/analyzer.js`
- Risk: Investment scores may be incorrect at edge cases; business impact high
- Priority: High

**Pipeline Database Operations:**
- What's not tested: Transaction rollback, concurrent access, data pull lifecycle
- Files: `src/pipeline/data/pipeline-database.js`
- Risk: Data corruption or loss under edge conditions
- Priority: Medium

**Integration Services:**
- What's not tested: SSH connection failures, webhook timeouts, CLI output parsing
- Files: `src/integrations/beads.js`, `src/integrations/rangeos-vps.js`
- Risk: Silent failures in external integrations; users see empty data
- Priority: Medium

**Browser Automation:**
- What's not tested: Page load failures, selector not found, screenshot capture
- Files: `src/browser/automation.js`
- Risk: Scraping workflows fail unpredictably on real websites
- Priority: Low (feature is county-specific anyway)

---

*Concerns audit: 2026-01-18*
