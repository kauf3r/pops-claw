# Phase 42: CLI Tools Dashboard - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Mission Control gets a /tools page showing all EC2 CLI tools, plugins, scripts, and cron jobs with health status, versions, and copy-paste quick actions. Data comes from a cached periodic health-check script, not live SSH. No executable remote actions from the browser.

</domain>

<decisions>
## Implementation Decisions

### Tool Inventory
- EC2 tools only (no Mac-side tools) — this is Bob's operations dashboard
- Four sections: CLI Tools, Plugins, Scripts, Scheduled Jobs
- CLI Tools: openclaw, gog, bd, node/npm, whisper
- Plugins: camofox-browser, secureclaw (separate section, not mixed with CLIs)
- Scripts: prune-sessions.sh, process-voice-notes.py, collect_verified.sh (own section)
- Cron jobs: separate section with last-run and next-run times

### Health Indicators
- CLI tools: version + reachability — green (responds + current), yellow (responds + outdated >7 days), red (not responding or missing)
- Cron jobs: last-run recency — green (ran within expected interval), yellow (missed 1 run), red (missed 2+ runs or never ran)
- Plugins: enabled + version — green (directory exists + in openclaw.json), yellow (exists but not in config), red (in config but directory missing)
- Data source: cached via periodic script on EC2 (every 5-10 min), writes to DB/JSON — dashboard reads cached data, no live SSH

### Layout & Grouping
- Compact table rows within each section (not cards) — ops dashboard feel like a status page
- Section order: CLI Tools → Plugins → Scripts → Scheduled Jobs (priority order)
- Health summary banner at top: total tools count + green/yellow/red breakdown
- Sections collapsible, all expanded by default

### Quick Actions
- Copy-paste commands (clipboard icon per row) — not executable buttons
- 1 primary diagnostic command shown per tool, expandable to 2-3 more
- Cron quick action: copy `openclaw cron trigger <id>` for manual firing
- Manual refresh icon next to "Last checked" timestamp — triggers health-check script via API, SWR auto-refreshes

### Claude's Discretion
- Exact health-check script implementation (shell script vs Python)
- DB schema for cached health data (tools.db vs JSON file)
- Refresh interval for periodic script (5 vs 10 min)
- Table column widths and responsive breakpoints
- Clipboard toast/feedback UX

</decisions>

<specifics>
## Specific Ideas

- Summary banner should feel like an uptime status page header — instant "is everything OK?" answer
- Table rows should be dense and scannable — think ops dashboard, not marketing page
- The refresh icon is a lightweight "check now" — it just triggers the EC2 script, doesn't bypass caching

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 42-cli-tools-dashboard*
*Context gathered: 2026-02-26*
