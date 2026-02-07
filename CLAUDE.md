# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Planning and documentation repository for "pops-claw" - a personal OpenClaw deployment on AWS EC2 with Tailscale-only access.

**Not a code repository.** Contains planning docs, progress tracking, and findings for configuring an existing EC2 instance.

## Architecture

- **Host:** Ubuntu EC2 with Tailscale (100.72.143.9)
- **Gateway:** Port 18789 (Tailscale-only, loopback bind)
- **Agent:** Claude-powered "Bob" running in Docker sandbox (network=bridge)
- **Browser:** agent-browser + Chromium in Docker
- **Binary:** `openclaw` (installed at `/home/ubuntu/.npm-global/bin/openclaw`)
- **Config:** `~/.openclaw/openclaw.json` on EC2
- **Service:** `openclaw-gateway.service` (systemd user service)
- **Workspace:** `~/clawd/` on EC2
- **Version:** v2026.2.3-1

## Key Files

| File | Purpose |
|------|---------|
| `task_plan.md` | Implementation phases, checklist, decisions |
| `progress.md` | Session log, test results, error tracking |
| `findings.md` | Requirements, research, technical decisions |

## Project Phases

1. Security Audit & Hardening ✅
2. Email/Calendar Integration (Gmail OAuth) ✅
3. Browser Control & Automation ✅
4. Cron/Scheduled Tasks ✅
5. Additional Messaging Integrations ✅
6. Production Hardening ✅

## Working With This Repo

When assisting with this project:
- Reference `task_plan.md` for current phase and remaining tasks
- Update `progress.md` after completing work or encountering errors
- Add research/decisions to `findings.md`
- EC2 operations require SSH via Tailscale to 100.72.143.9
- Use full path `/home/ubuntu/.npm-global/bin/openclaw` for non-interactive SSH commands
- Legacy paths (`~/.clawdbot/`) are symlinked to `~/.openclaw/`
