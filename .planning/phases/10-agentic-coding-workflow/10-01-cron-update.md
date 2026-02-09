# Task 2: Morning Briefing GitHub Activity Section

## Change
Added Section 7 (GitHub Activity) to morning-briefing cron systemEvent.

## Cron Job
- ID: 863587f3-bb4e-409b-aee2-11fe2373e6e0
- Schedule: 0 7 * * * America/Los_Angeles
- Status: ok

## New Section Content
```
## 7. GitHub Activity (CW-03)
Run: gh pr list --state open --json number,title,author,createdAt --limit 20
List any open PRs with: PR number, title, author, and age (days since created).
Also run: gh pr list --state open --search "review-requested:kauf3r" --json number,title
If no open PRs, say "No open PRs."
```

## Verification
- GitHub in text: True
- Section 7 present: True
- gh pr list present: True
- All 7 sections (1-7) present: True
- Existing sections preserved: Calendar, Email, Health, Weather, Tasks, Home Environment
- Description updated: "Rich daily briefing at 7 AM PT -- calendar, email, health, weather, tasks, GitHub"
