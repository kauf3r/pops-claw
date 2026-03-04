---
created: 2026-03-04T19:09:41.280Z
title: Install top 5 ClawhHub skills on EC2
area: tooling
files: []
---

## Problem

Bob has 26/64 skills ready but is missing several high-value skills that directly support Andy's workflows (YouTube channel launch, content pipeline, land investing, image generation). The broken OpenAI quota means DALL-E/image skills are down, and there's no YouTube research capability.

## Solution

Install via `npx clawhub install` on EC2 (100.72.143.9):

1. **youtube-full** — YouTube transcripts, search, channel/playlist browsing (content engine)
2. **summarize** — URL/PDF/audio/YouTube summarization (briefings, research)
3. **nano-banana-pro** — Gemini image gen/edit (replaces broken DALL-E, uses existing GEMINI_API_KEY)
4. **blogwatcher** — RSS/blog monitoring (content pipeline, industry tracking)
5. **real-estate-lead-machine** — Motivated seller scraping + AI outreach (land investing)

After install: verify with `openclaw skills list`, restart gateway, test each skill.
