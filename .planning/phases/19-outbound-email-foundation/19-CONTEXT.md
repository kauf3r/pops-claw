# Phase 19: Outbound Email Foundation - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Bob sends email via Resend REST API using a custom SKILL.md + curl from Docker sandbox. Includes domain verification, morning briefing delivery via email, and alert/notification emails as Slack backup. Inbound email receiving, reply threading, and conversation tracking are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Sending identity
- Domain: `mail.andykaufman.net` (subdomain on personal domain, protects business MX)
- From address: `bob@mail.andykaufman.net`
- Display name: `Bob` (matches Slack agent name)
- Resend account under Andy's personal domain, not AirSpace

### Email formatting
- Minimal HTML with Practical Typography principles (not branded, not plain text)
- Static HTML template stored in Bob's workspace (`/workspace/email-template.html`)
- Inline CSS for email client compatibility (Gmail strips `<style>` tags)
- Typography rules adapted for email: line-height 1.5, subtle heading hierarchy (h1: 1.5rem, h2: 1.35rem, h3: 1.15rem), heading spacing binds to content
- Unicode smart quotes, en/em dashes, proper ellipsis (not CSS — actual characters)
- Properties that don't work in email (text-wrap, hanging-punctuation, font-kerning) are skipped
- Minimal footer: "Sent by Bob" or similar — one line, subtle

### Briefing delivery
- Supplements Slack briefing (both channels, same content)
- Same content as Slack, reformatted into HTML email template
- Piggybacks on existing morning briefing cron (generate content once, send to Slack then email)
- Configurable recipient list stored in workspace config file (start with theandykaufman@gmail.com)

### Alert/notification emails
- Triggers on important + critical events (failed crons, health anomalies, pipeline stalls, system-down, security)
- Bob's judgment decides when to escalate to email (skill instructions define what's email-worthy)
- No separate alert crons — Bob sends email alerts from any session when warranted
- Soft cap: 5 alert emails per day (6th+ stays Slack-only, protects quota)
- Same recipient list as briefings (one config for all email)

### Claude's Discretion
- Email template HTML/CSS implementation details
- Exact alert threshold descriptions in skill instructions
- Config file format for recipient list (JSON, YAML, or plain text)
- Subject line conventions for briefings vs alerts

</decisions>

<specifics>
## Specific Ideas

- Typography guidelines from Practical Typography: line-height 1.5, subtle heading sizes, more top margin / less bottom on headings, blockquote at 0.95em with 1.5rem left padding
- Smart typography: curly quotes, en/em dashes, proper ellipsis (use Unicode characters, not CSS properties)
- Email should feel like a well-typeset personal email, not a marketing newsletter

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-outbound-email-foundation*
*Context gathered: 2026-02-16*
