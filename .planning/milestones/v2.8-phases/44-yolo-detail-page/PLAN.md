# Phase 44: YOLO Detail Page — Plan

**Created:** 2026-03-01
**Goal:** Polish the existing YOLO detail page beyond MVP — make builds easy to access, use, and iterate on.

## Situation

All 5 requirements (YOLO-01 through YOLO-05) already exist at MVP level. This phase focuses on polish and usability improvements that make the page genuinely useful for accessing and iterating on YOLO builds.

## Plan 1: Navigation & Access Polish

1. Fix NavBar active state: `pathname === link.href` → `pathname.startsWith(link.href)` so /yolo/{slug} highlights YOLO nav
2. Add prev/next build navigation on detail page (arrow buttons or links)
3. Add breadcrumb: YOLO > {build name}

## Plan 2: File Viewer Enhancement

4. Add syntax highlighting for code files (Python, JS, HTML, CSS, JSON, MD) — use a lightweight approach (CSS classes or a small lib if already available, NOT a heavy dependency)
5. Add copy-to-clipboard button on code blocks
6. Add file size display next to filename
7. For HTML builds: make the iframe preview taller/resizable, add "Open in new tab" link
8. For CLI builds: show a "How to run" hint (e.g., `python main.py`)

## Plan 3: Build Detail Improvements

9. Format duration nicely (handle nulls, show "Xm Ys" format)
10. Add timestamps to build log entries (if structured) or at minimum show started_at/completed_at clearly
11. Make self-evaluation more prominent — it's the most interesting part
12. Add a "status timeline" showing idea → building → testing → success progression with timestamps

## Execution

All changes in ~/clawd/mission-control/ on EC2 via SSH. Build and test after each wave.
Restart mission-control service after changes.

## Success Criteria

- [x] YOLO-01: Build cards link to detail page (already done)
- [x] YOLO-02: Build log with timestamps (already done, enhancing)
- [x] YOLO-03: Error section (already done)
- [x] YOLO-04: Self-evaluation display (already done, making more prominent)
- [x] YOLO-05: File listing (already done, adding syntax highlight + copy)
- [ ] NavBar highlights on detail pages
- [ ] Prev/next navigation between builds
- [ ] Syntax-highlighted file viewer with copy button
- [ ] Polished duration/timestamp display
- [ ] HTML builds: "Open in new tab" + better iframe
- [ ] CLI builds: run hints

---
*Phase: 44-yolo-detail-page*
*Plan created: 2026-03-01*
