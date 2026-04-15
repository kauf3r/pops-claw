---
phase: 58
slug: gbrain-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-15
---

# Phase 58 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual SSH verification (infrastructure config phase — no local test framework) |
| **Config file** | none — remote EC2 instance |
| **Quick run command** | `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 'gbrain doctor --json'` |
| **Full suite command** | `ssh -i ~/.ssh/clawdbot-key.pem ubuntu@100.72.143.9 'gbrain --version && gbrain doctor --json && echo "test" \| gbrain put test-verification && gbrain search "test" && gbrain embed test-verification'` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `gbrain --version` via SSH
- **After every plan wave:** Run full suite command via SSH
- **Before `/gsd:verify-work`:** Full suite must pass
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 58-01-01 | 01 | 1 | INFRA-01 | smoke | `gbrain --version` via SSH | N/A | ⬜ pending |
| 58-01-02 | 01 | 1 | INFRA-01 | smoke | `gbrain doctor --fast` on host | N/A | ⬜ pending |
| 58-02-01 | 02 | 2 | INFRA-02 | smoke | `gbrain --version` from inside sandbox | N/A | ⬜ pending |
| 58-02-02 | 02 | 2 | INFRA-03 | smoke | `gbrain doctor --json` from inside sandbox | N/A | ⬜ pending |
| 58-02-03 | 02 | 2 | INFRA-04 | smoke | `gbrain embed test-verification` from sandbox | N/A | ⬜ pending |
| 58-02-04 | 02 | 2 | HEALTH-02 | smoke | `gbrain doctor --json` health score check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. No test framework install needed — verification is via SSH commands.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| gbrain accessible in sandbox | INFRA-02 | Sandbox access requires gateway restart and manual exec | SSH to EC2, restart gateway, exec into sandbox, run `gbrain --version` |
| PGLite data persists across sandbox restarts | INFRA-03 | Requires gateway restart cycle | Add page, restart gateway, verify page still exists |
| Compiled binary vs Bun fallback | INFRA-01 | Depends on runtime WASM compatibility test | Try compiled binary first; if ENOENT on postgres.data, switch to Bun runtime |

---

## Validation Sign-Off

- [ ] All tasks have SSH-based verify commands
- [ ] Sampling continuity: every task verifiable via SSH
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
