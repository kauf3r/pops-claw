# Phase 44: YOLO Detail Page — Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

## Key Finding

The YOLO detail page already exists at `src/app/yolo/[slug]/page.tsx` with:
- Live HTML preview iframe (sandboxed, 600px)
- Expandable source file viewer (fetches via API)
- Build/error log cards
- Self-evaluation display
- Tech stack badges, metadata row

API layer is complete: list, detail (with file listing + hasHtml), and raw file serving endpoints.

All 5 requirements (YOLO-01 through YOLO-05) are met at MVP level. This phase is about **polishing beyond MVP** and making builds easy to access and iterate on.

## Current State

- 8 builds total, all success/score 4, no failed/partial builds to test against
- NavBar uses exact match (detail pages don't highlight YOLO nav item)
- Build artifacts vary: HTML apps (index.html) vs Python CLI (main.py)
- Duration is null for some builds
- No syntax highlighting in file viewer
- No way to download or quickly launch builds
- No prev/next navigation between builds

## Infrastructure

- Next.js 14.2.15 + Tailwind + SWR + better-sqlite3
- Code on EC2: ~/clawd/mission-control/
- YOLO DB: ~/clawd/agents/main/yolo-dev/yolo.db (readonly from dashboard)
- Build artifacts: ~/clawd/agents/main/yolo-dev/{slug}/
- Service: mission-control.service (port 3001, SSH tunnel access)
