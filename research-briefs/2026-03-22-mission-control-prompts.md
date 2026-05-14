# Mission Control Prompts — Calendar, Memory, Office, Task Board

> **Alex Finn** · X Thread · `ai_coding` · 2026-02-20
> https://x.com/alexfinn/status/2024169334344679783

---

## TL;DR

Four prompts for building out a Mission Control dashboard: (1) calendar view for cron jobs and scheduled tasks, (2) memory screen with search across all agent memories, (3) digital office with agent avatars showing who's working, (4) task board with assignment tracking. We've built most of this — the gaps are the digital office and the real-time task board.

## Key Insights

- Calendar should be the single source of truth for all scheduled work — anything scheduled goes here
- Memory screen needs search as first-class feature, not just a file listing
- Digital office concept: agents as avatars at virtual desks, visual status at a glance
- Task board should track both human and agent tasks with real-time status updates
- All four screens create a complete operational picture — no blind spots

## Quotes Worth Saving

> "Please build me a digital office screen where I can view each agent working. They should be represented by individual avatars and have their own work areas."

> "Moving forward please put all tasks you work on into this board and update it in real time."

## Action Plan

- [ ] Compare MC pages vs. these 4 prompts — we have /calendar, /memory, /agents already. Gap: real-time task board
- [ ] Evaluate adding agent avatar/status visualization to /agents page (currently table-based)
- [ ] Add task board feature to MC backlog — track agent_tasks from coordination.db with Kanban view

## The One Thing

**Build the task board — it's the one MC screen we're missing that would close the operational visibility loop.**

Calendar, memory, and agents pages exist. A Kanban-style task board showing what Bob/Sage/Quill are working on (from coordination.db agent_tasks) would complete the picture.

---
*Source: Readwise highlights (4) from @alexfinn X thread*
