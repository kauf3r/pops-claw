# YOLO Overnight Builder Prompt

> **Miles Deutscher** · X Thread · `ai_coding` · 2026-02-24
> https://x.com/milesdeutscher/status/2026303639271494097

---

## TL;DR

The original YOLO prompt that inspired our overnight build system: agent picks a wild project idea based on your recent work, builds a working prototype while you sleep, and logs everything to a dashboard. "Shipped and ugly" over "planned and pretty." This is the DNA of our yolo-dev cron.

## Key Insights

- Agent generates the idea itself — based on recent conversations, projects, and interests
- Scope discipline: simplest possible version that proves the concept. No feature creep.
- 15-minute stuck rule: if one approach isn't working, try a completely different one
- Binary outcome: working prototype OR useful failure with clear next steps. Either way you're ahead.
- Dashboard logging: date, name, one-liner, status (working/partial/failed), key takeaway, project link

## Quotes Worth Saving

> "Bias toward 'shipped and ugly' over 'planned and pretty.'"

> "When I wake up I want one of two things: a working prototype, or a useful failure I can learn from."

## Action Plan

- [ ] Compare our yolo-dev implementation against this original spec — are we missing the "15-min pivot" rule?
- [ ] Add "key takeaway" field to yolo.db if not already tracked
- [ ] Consider adding "based on recent work" interest signal to the yolo-dev-overnight cron payload

## The One Thing

**Our YOLO dev is already running — validate it still matches this original vision.**

The core insight is the 15-minute pivot rule and the "useful failure" framing. If our overnight builds are getting stuck rather than pivoting, we're losing the magic of the original concept.

---
*Source: Readwise highlight from @milesdeutscher X thread*
