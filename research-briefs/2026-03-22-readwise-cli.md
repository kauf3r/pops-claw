# Readwise CLI Released

> **Readwise** · X Post · `ai_coding` · 2026-03-19
> https://x.com/readwise/status/2034302848805241282

---

## TL;DR

Readwise shipped an official npm CLI (`@readwise/cli`). Potential to replace our API-based polling in the research-scan cron with a native CLI tool. Low priority — current API approach works fine.

## Key Insights

- `npm install -g @readwise/cli` — official package
- Could simplify Readwise integration in research-scan if CLI has better pagination/filtering
- Our current API approach (highlights endpoint with updated__gt) works well already

## Action Plan

- [ ] Test `readwise --help` to see if CLI offers anything our API polling doesn't

## The One Thing

**Nice to know, not urgent. Current API integration works.**

---
*Source: Readwise highlight*
