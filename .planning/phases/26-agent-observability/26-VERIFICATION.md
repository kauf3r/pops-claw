---
phase: 26-agent-observability
verified: 2026-02-19T19:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 26: Agent Observability Verification Report

**Phase Goal:** Bob can see how all agents are using LLM resources and surfaces anomalies in the morning briefing
**Verified:** 2026-02-19
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | LLM hook payloads configured and firing on every agent turn | VERIFIED | 501 live rows in llm_calls (non-backfill), plugin logs show "Database initialized" on every gateway restart, hooks confirmed firing with real heartbeat cron data |
| 2 | Each LLM call writes a row with agent_id, model, tokens, cost | VERIFIED | `llm_calls` table schema confirmed; live rows show agent_id (main/ops/rangeos), model (claude-sonnet-4-5/claude-haiku-4-5), input_tokens, output_tokens, estimated_cost_usd |
| 3 | Each agent run writes a row with agent_id, duration, success/error | VERIFIED | `agent_runs` table present with 7,748 rows; recordAgentRun() in db.ts writes all fields |
| 4 | observability.db accessible from sandbox at /workspace/observability.db | VERIFIED | Bind mount confirmed in openclaw.json: `/home/ubuntu/clawd/agents/main/observability.db:/workspace/observability.db:ro` |
| 5 | Bob can report per-agent token usage, model distribution, turn counts, cost, latency, errors for last 24h | VERIFIED | OBSERVABILITY.md at /workspace/OBSERVABILITY.md has complete SQL for all 6 reporting sections; live 24h query returns 4 agents with turns/tokens/cost/models |
| 6 | Morning briefing includes Agent Observability section (Section 10) with anomaly detection | VERIFIED | Section 10 confirmed in both `message` and `text` fields of cron job 863587f3; latest briefing run status: ok |
| 7 | Anomaly detection uses 7-day rolling average with 2x warning / 4x critical thresholds | VERIFIED | Full CTE SQL in OBSERVABILITY.md confirmed with `collecting` (< 7 days), `zero_activity`, `warning` (2x), `critical` (4x) states |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `~/.openclaw/plugins/observability-hooks/src/index.ts` | Hook handlers for llm_output and agent_end | VERIFIED | Substantive: registers api.on('llm_output') and api.on('agent_end') with full recordLlmCall/recordAgentRun calls; wired via plugin registration |
| `~/.openclaw/plugins/observability-hooks/src/db.ts` | SQLite schema, insert functions, retention cleanup | VERIFIED | Substantive: initDb(), recordLlmCall(), recordAgentRun(), cleanup() all implemented with execSync sqlite3; 4 indexes created |
| `~/.openclaw/plugins/observability-hooks/src/pricing.ts` | Model cost map for Haiku/Sonnet/Opus | VERIFIED | Substantive: COST_PER_MILLION map with all 3 models, fuzzy matching via MODEL_KEYWORDS, estimateCost() exported |
| `~/.openclaw/plugins/observability-hooks/dist/index.js` | Compiled plugin entry point | VERIFIED | Exists at 1,867 bytes (compiled from tsc); plugin loads successfully at gateway start |
| `~/.openclaw/plugins/observability-hooks/package.json` | Plugin npm package definition | VERIFIED | Exists; ESM, tsc build, @openclaw/observability-hooks v1.0.0 |
| `~/.openclaw/plugins/observability-hooks/openclaw.plugin.json` | Plugin manifest for OpenClaw registration | VERIFIED | Exists with configSchema (required by OpenClaw v2026.2.17) |
| `~/clawd/agents/main/observability.db` | SQLite database with llm_calls and agent_runs tables | VERIFIED | 1,224,704 bytes; 1,044 llm_calls (543 backfill + 501 live), 7,748 agent_runs |
| `~/clawd/agents/main/OBSERVABILITY.md` | Reference doc with SQL queries for 6 reporting sections | VERIFIED | 4,924 bytes; all 6 sections present (summary, anomaly, errors, latency, rate-limit, retention) with complete SQL |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| observability-hooks plugin | openclaw.json plugins.load.paths | Plugin path registration | WIRED | Path `/home/ubuntu/.openclaw/plugins/observability-hooks` confirmed in load.paths; also in entries and installs |
| observability.db host path | /workspace/observability.db sandbox path | Docker bind mount (ro) | WIRED | Bind confirmed in agents.defaults.sandbox.docker.binds; OBSERVABILITY.md references /workspace/observability.db |
| llm_output event | llm_calls table INSERT | api.on('llm_output', ...) in index.ts | WIRED | Handler confirmed in source; 501 live rows prove it is firing |
| morning-briefing cron payload | OBSERVABILITY.md reference doc | Section 10 in cron message | WIRED | Section 10 confirmed present in both message and text fields of cron 863587f3; references /workspace/OBSERVABILITY.md |
| OBSERVABILITY.md SQL queries | /workspace/observability.db | sqlite3 CLI queries from sandbox | WIRED | Sandbox access verified (sqlite3 returns 1,040+ rows from container); Section 10 instructs `sqlite3 /workspace/observability.db` |
| anomaly detection | 7-day rolling average | SQL window function CTE in OBSERVABILITY.md | WIRED | Full CTE with daily/rolling/today CTEs confirmed in OBSERVABILITY.md; days_with_data < 7 triggers cold-start |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| OBS-01 | 26-01 | llm_input/llm_output hook payloads configured for agent monitoring | SATISFIED | Plugin registered and firing; gateway logs confirm "[observability-hooks] Database initialized"; 501 live hook rows in DB |
| OBS-02 | 26-01, 26-02 | Agent activity summary (token usage, model distribution, turn counts) available to Bob | SATISFIED | OBSERVABILITY.md Section 1 SQL returns per-agent turns/tokens/cost/models; backfilled baseline with 4 agents |
| OBS-03 | 26-02 | Morning briefing includes agent observability section (anomalous usage, errors, rate limit proximity) | SATISFIED | Section 10 in morning briefing cron; latest test run status: ok; section instructs anomaly detection, error summary, rate limit proximity |

No orphaned requirements — all three OBS-01/02/03 are claimed by plans and verified implemented. REQUIREMENTS.md shows all three marked complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/index.ts | 5 | `return null` in parseAgentFromSessionKey | Info | Legitimate guard — returns null when session key format does not match `agent:<id>:<rest>`. Falls back to "unknown" agent_id. Not a stub. |

No blockers or warnings found.

### Human Verification Required

#### 1. Morning Briefing Agent Observability Output Quality

**Test:** Trigger the morning briefing cron manually (`openclaw cron run 863587f3-bb4e-409b-aee2-11fe2373e6e0 --timeout 120000`) or wait for the next scheduled run. Review the Slack output in #popsclaw.
**Expected:** Section 10 shows a per-agent summary table (Agent | Turns | Input Tokens | Output Tokens | Est. Cost | Models), followed by anomaly status. During cold-start (< 7 days of continuous live data), should show "Observability data collecting — baselines available after 7 days." or similar cold-start message.
**Why human:** Cannot verify the formatting quality, table readability, or cold-start message rendering from log inspection alone. The first test run after 26-02 completed reported "observability.db not present" in its summary (noted as a transient issue in 26-02-SUMMARY.md). Human confirmation that the next scheduled run produces well-formatted output is the final confidence check.

#### 2. Anomaly Detection Baseline Accuracy (7-day window)

**Test:** After 7+ days of live data accumulation, review the morning briefing for an agent that has unusually high activity. Confirm it is flagged WARNING or CRITICAL.
**Expected:** Agent with > 2x daily average tokens is flagged WARNING; > 4x is flagged CRITICAL. Zero-activity agent with prior history flagged as WARNING.
**Why human:** The 7-day rolling average baseline needs real data to produce meaningful anomaly flags. The cold-start period ends after 7 days of continuous live data. Verifying the anomaly detection fires correctly requires waiting for the baseline to accumulate.

## Summary

Phase 26 goal is achieved. All three requirements (OBS-01, OBS-02, OBS-03) are fully implemented and wired:

- The observability-hooks plugin is installed, compiled, registered in openclaw.json, and confirmed firing — 501 live LLM call rows and 7,748 agent run rows are in observability.db as of verification time.
- OBSERVABILITY.md provides complete SQL for all 6 reporting sections (24h summary, anomaly detection, errors, latency, rate-limit proximity, data retention) and is accessible in the sandbox at /workspace/OBSERVABILITY.md.
- Section 10 (Agent Observability) is wired into the morning briefing cron payload with explicit instructions to query observability.db and format per OBSERVABILITY.md. The latest briefing run completed with status: ok.
- Backfill provides 543 historical rows from Jan 25 – Feb 19 covering 4 agents (main, landos, ops, rangeos), jumpstarting the rolling average baseline.
- All 6 commits documented in SUMMARYs are verified in git history. No stubs, placeholders, or disconnected wiring found.

Two items are flagged for human verification: (1) confirming the Slack briefing output is well-formatted on the next scheduled run, and (2) confirming anomaly detection produces meaningful flags after the 7-day cold-start window closes.

---

_Verified: 2026-02-19_
_Verifier: Claude (gsd-verifier)_
