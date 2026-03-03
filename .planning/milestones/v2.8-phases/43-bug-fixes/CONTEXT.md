# Phase 43: Bug Fixes - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix two known bugs: (1) Ezra's publish-check cron fails to create WordPress drafts for approved articles because content.db shows 0 bytes in the Docker sandbox, and (2) AeroVironment fly_status is null for all storage entries, breaking billing accuracy. Morning briefing should reflect accurate data after fixes.

</domain>

<decisions>
## Implementation Decisions

### Ezra Recovery
- Claude's discretion on recovery approach for article #16 (re-run cron, manual publish, or simplest path)
- Query content.db during execution to find ALL approved articles missing wp_post_id (not just #16)
- Verify sandbox mounts for ALL content agents (Quill, Sage, Ezra), not just Ezra
- Claude's discretion on mount fix approach (fix Docker mount ordering vs. relocate content.db vs. agent-specific config)

### AeroVironment fly_status
- fly_status inferred from compliance_flights table: if AV logged compliance flights that day, status = fly
- AeroVironment-specific tracking only (not all tenants)
- Backfill historical fly_status values from compliance_flights data
- Claude's discretion on calculation approach (cron backfill vs. computed at query time)
- Claude's discretion on value set (binary fly/no-fly vs. three-state with unknown)

### Briefing Accuracy
- Investigate whether morning briefing template needs changes or if fixing the bugs is sufficient
- Claude's discretion on what content pipeline info to show in briefing
- Claude's discretion on whether AV fly_status appears in daily briefing vs. weekly audit only

### Regression Prevention
- Slack alert to #content-pipeline when publish-check finds approved articles but can't create WP drafts (DB read error, 0-byte file, WP API failure)
- Add content.db mount verification to nightly health check script on EC2
- Claude's discretion on AV fly_status null alerting approach

### Claude's Discretion
- Ezra recovery method (re-run vs manual publish)
- Mount fix approach (ordering vs relocation)
- fly_status calculation approach and value set
- Briefing template changes (if any)
- AV fly_status reporting cadence (daily vs weekly)
- AV fly_status null alerting approach

</decisions>

<specifics>
## Specific Ideas

- Root cause for BUG-01 is identified: Docker workspace volume mount shadows the content.db bind-mount, resulting in 0-byte file visible at /workspace/content.db inside Ezra's sandbox. Host file ~/clawd/content.db is 114KB and healthy.
- Quill and Sage successfully read/wrote content.db but Ezra cannot — suggests agent-specific mount behavior differences worth investigating.
- The bead (pops-claw-jpt) has detailed investigation steps including Docker inspect comparison between Ezra and Quill containers.
- Existing workaround: Bob can query content.db via host-side sqlite3 and publish directly to WordPress.
- Established pattern from retrospective: "Explicit bind-mounts in openclaw.json required for any sandbox file access" (verified across v2.0, v2.6, v2.7).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `openclaw.json` agents.defaults.sandbox.docker.binds — existing bind-mount config pattern
- `nightly-health-check.sh` (~/.ssh/scripts/) — existing health check to extend with mount verification
- Content pipeline cron chain: topic-research -> writing-check -> review-check -> publish-check -> Slack delivery
- `compliance_flights` table in AirSpace DB — source for fly_status inference

### Established Patterns
- Explicit bind-mount pattern in openclaw.json for sandbox file access (verified v2.0, v2.6, v2.7)
- Health-check cron -> JSON -> API -> SWR pattern for observability
- Channel:ID format for Slack cron delivery (both payload messages and session instruction files)
- Protocol docs over skills for complex agent behavior

### Integration Points
- `openclaw.json` sandbox config — mount fix lives here
- `content.db` at ~/clawd/content.db — shared across content pipeline agents
- `publish-check` cron — needs error alerting added
- Morning briefing template — may need content pipeline section update
- Weekly ops audit — already reports AV fly_status (currently null)
- Nightly health check — needs mount verification added

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 43-bug-fixes*
*Context gathered: 2026-03-01*
