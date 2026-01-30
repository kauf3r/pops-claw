# Phase 2: Gmail/Calendar Config Changes

## 1. OAuth Scopes Needed

For andy@andykaufman.net with read+send email and read+write calendar:

```
gmail.readonly
gmail.send
gmail.modify
calendar
```

## 2. gog Auth Commands (run on EC2)

```bash
# Upload client_secret.json to EC2 first
scp client_secret.json ubuntu@100.72.143.9:~/.config/gogcli/

# Then on EC2:
gog auth add andy@andykaufman.net \
  --client-id-file ~/.config/gogcli/client_secret.json \
  --scopes gmail.readonly,gmail.send,gmail.modify,calendar
```

This will open a browser URL for OAuth consent.

## 3. clawdbot.json Additions

Add to existing config (merge, don't replace):

```json
{
  "hooks": {
    "enabled": true,
    "path": "/hooks",
    "token": "GENERATE_RANDOM_TOKEN_HERE",
    "presets": ["gmail"],
    "gmail": {
      "account": "andy@andykaufman.net",
      "label": "INBOX",
      "topic": "projects/pops-claw-gmail/topics/pops-claw-gmail-watch",
      "hookUrl": "http://127.0.0.1:18789/hooks/gmail",
      "includeBody": true,
      "maxBytes": 20000,
      "renewEveryMinutes": 720
    },
    "mappings": [
      {
        "id": "gmail-hook",
        "match": { "path": "gmail" },
        "action": "agent",
        "wakeMode": "now",
        "name": "Gmail Notification",
        "sessionKey": "hook:gmail:{{messages[0].id}}",
        "messageTemplate": "New email from {{messages[0].from}}\nSubject: {{messages[0].subject}}",
        "textTemplate": "{{messages[0].snippet}}",
        "deliver": true,
        "channel": "last"
      }
    ]
  }
}
```

## 4. Pub/Sub Setup (GCP)

Topic: `pops-claw-gmail-watch`
IAM binding: `gmail-api-push@system.gserviceaccount.com` → Publisher role

## 5. Start Gmail Watch (after auth)

```bash
# On EC2
gog gmail watch start \
  --account andy@andykaufman.net \
  --label INBOX \
  --topic projects/pops-claw-gmail/topics/pops-claw-gmail-watch
```

## 6. Test Commands

```bash
# List recent emails
gog gmail messages list --account andy@andykaufman.net --max 5

# List calendars
gog calendar calendars --account andy@andykaufman.net

# List upcoming events
gog calendar events list --account andy@andykaufman.net --max 10
```
