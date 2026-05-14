# Resend + OpenClaw Integration — Unified Agent Email Platform

> **Resend / GitHub** · Technical Brief · `ai_coding` · 2026-03-26

---

## TL;DR

Resend CEO disabled bot detection to enable direct agent access, signaling enterprise-level support for AI agent email. Dual integration paths (AgentSkills + MCP server) provide flexibility. Security-first design with 5 protection levels makes it a safer alternative to connecting agents directly to Gmail.

## Key Insights

- **CEO-endorsed agent support.** Zeno Rocha personally disabled bot detection on Resend's login flow (Feb 2026) to enable AI agent access — this is strategic positioning, not a side feature.
- **Dual integration paths.** AgentSkills format (resend/resend-skills) and MCP server (resend/resend-mcp) support stdio, HTTP transport, and multi-client mode (Claude Code, Cursor, Desktop).
- **Security-first design.** The agent-email-inbox skill includes 5 security levels: strict allowlist, domain allowlist, content filtering, sandboxed processing, and human-in-the-loop — addressing known prompt injection risks.
- **Replaces dual-service approach.** Current setup uses Resend outbound + AgentMail inbound. Resend's native inbound webhooks could unify both under one platform with real-time processing.
- **Free tier covers development.** 3,000 emails/month, no credit card, verified domain only for external recipients.

## Action Plan

- [ ] Audit current email workflow — document all outbound/inbound patterns Bob uses
- [ ] Test Resend inbound webhooks — compare latency/reliability vs. AgentMail polling
- [ ] Evaluate security model — review 5-level protection against Bob's threat model
- [ ] Cost analysis — AgentMail + Resend vs. Resend-only at current/projected volume

## The One Thing

**Resend is betting on AI agents as a core market. Their unified email platform (outbound + inbound + security) could replace the current dual-service setup and eliminate the prompt injection risks of direct Gmail access.**

---
*Sources: resend.com/blog, github.com/resend/resend-skills, github.com/resend/resend-mcp*
