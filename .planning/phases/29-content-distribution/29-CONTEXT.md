# Phase 29: Content Distribution - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Published articles reach subscribers automatically via weekly digest emails sent through Resend Broadcasts. Covers: audience management (Resend Audiences API), digest compilation from content.db, sending via Broadcasts API, and delivery monitoring in morning briefing. Does NOT cover public signup forms, multiple audience segments, or custom analytics dashboards.

</domain>

<decisions>
## Implementation Decisions

### Audience Management
- Manually curated subscriber list — no public signup form
- Single Resend Audience named "AirSpace Weekly Digest"
- Store email, first name, last name per contact (enables personalized greeting)
- Bob manages via skill commands: `manage subscribers add jane@example.com "Jane Doe"`, `manage subscribers list`, `manage subscribers remove jane@example.com`
- Unsubscribe handled by Resend built-in (automatic link + platform-level opt-out)

### Digest Content & Format
- Include all articles published since last successful digest send (timestamp-tracked, not rolling window)
- Per-article card: title, 2-3 sentence summary from content.db, "Read more" link to airspaceintegration.com
- Reuse existing email-template.html branding — add repeating article card section
- Short standard intro: "Here's what we published this week at AirSpace Integration" (fixed/templated, not AI-generated each time)
- If zero articles since last send, skip the send entirely

### Send Schedule & Triggers
- Weekly cron: Wednesday 8 AM PT
- If no new articles: skip send, DM Andy on Slack that digest was skipped
- Track last successful send timestamp to determine article inclusion window (avoids duplicates on retry or schedule change)

### Delivery & Monitoring
- After send: Bob DMs Andy on Slack with summary (subscriber count, article count, send status)
- Morning briefing section for digest metrics: open rate, click rate, bounce count (data from Resend API)
- Bounce/complaint handling: rely on Resend auto-suppression, surface counts in briefing, flag warning if bounce rate > 5%
- Test send skill command: preview compiled digest to Andy's email before going live to audience

### Claude's Discretion
- Article card HTML/CSS design within existing template constraints
- Digest subject line format
- Exact Resend Broadcasts API integration pattern
- How to store last-send timestamp (content.db vs flat file)

</decisions>

<specifics>
## Specific Ideas

- Reuse the existing email-template.html that the resend-email skill already uses for branding consistency
- Subscriber management should feel like a natural skill command, similar to existing Bob skills
- Wednesday mid-week send avoids Monday inbox overload

</specifics>

<deferred>
## Deferred Ideas

- Public signup form on airspaceintegration.com — future phase
- Multiple audience segments (by topic, industry, etc.) — future phase
- A/B testing subject lines — future phase

</deferred>

---

*Phase: 29-content-distribution*
*Context gathered: 2026-02-21*
