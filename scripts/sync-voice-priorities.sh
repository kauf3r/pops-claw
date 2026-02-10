#!/usr/bin/env bash
# sync-voice-priorities.sh — Pull voice-memory priorities into Bob's workspace
# Runs via system cron every 5 minutes on EC2
set -euo pipefail

# Load env vars (VOICE_MEMORY_SUPABASE_URL, VOICE_MEMORY_SERVICE_ROLE_KEY, VOICE_MEMORY_USER_ID)
if [[ -f "$HOME/.openclaw/.env" ]]; then
  set -a; source "$HOME/.openclaw/.env"; set +a
fi

SUPABASE_URL="${VOICE_MEMORY_SUPABASE_URL:?missing VOICE_MEMORY_SUPABASE_URL}"
SERVICE_KEY="${VOICE_MEMORY_SERVICE_ROLE_KEY:?missing VOICE_MEMORY_SERVICE_ROLE_KEY}"
USER_ID="${VOICE_MEMORY_USER_ID:?missing VOICE_MEMORY_USER_ID}"
OUTPUT_FILE="/home/ubuntu/clawd/agents/main/PRIORITIES.md"
LAST_SYNC_FILE="/home/ubuntu/clawd/scripts/.last-priority-sync"

# Auth headers for Supabase REST API
AUTH=(-H "Authorization: Bearer $SERVICE_KEY" -H "apikey: $SERVICE_KEY" -H "Content-Type: application/json")

# Fetch open tasks
TASKS=$(curl -s "${SUPABASE_URL}/rest/v1/tasks?user_id=eq.${USER_ID}&status=eq.open&order=is_pinned.desc,created_at.desc&limit=50" "${AUTH[@]}")

# Fetch recent analyses (last 7 days, current version only)
WEEK_AGO=$(date -u -d '7 days ago' '+%Y-%m-%dT00:00:00Z' 2>/dev/null || date -u -v-7d '+%Y-%m-%dT00:00:00Z')
ANALYSES=$(curl -s "${SUPABASE_URL}/rest/v1/analyses?user_id=eq.${USER_ID}&is_current=eq.true&created_at=gte.${WEEK_AGO}&order=created_at.desc&limit=10" "${AUTH[@]}")

# Check if we got valid responses
if ! echo "$TASKS" | jq -e '.' >/dev/null 2>&1; then
  echo "ERROR: Failed to fetch tasks from Supabase" >&2
  exit 1
fi

NOW=$(date '+%Y-%m-%d %H:%M %Z')
TASK_COUNT=$(echo "$TASKS" | jq 'length')

# Build PRIORITIES.md
{
  echo "# Voice Priorities"
  echo "_Last synced: ${NOW}_"
  echo ""

  # Pinned tasks first
  PINNED=$(echo "$TASKS" | jq '[.[] | select(.is_pinned == true)]')
  PINNED_COUNT=$(echo "$PINNED" | jq 'length')
  if [[ "$PINNED_COUNT" -gt 0 ]]; then
    echo "## Pinned (Top Priority)"
    echo "$PINNED" | jq -r '.[] | "- **\(.priority // "unset" | ascii_upcase)**: \(.description)\(if .due_date then " — due: \(.due_date)" else "" end)"'
    echo ""
  fi

  # Tasks by priority
  for PRIO in high medium low; do
    PRIO_TASKS=$(echo "$TASKS" | jq --arg p "$PRIO" '[.[] | select(.priority == $p and .is_pinned != true)]')
    PRIO_COUNT=$(echo "$PRIO_TASKS" | jq 'length')
    if [[ "$PRIO_COUNT" -gt 0 ]]; then
      echo "## $(echo "$PRIO" | sed 's/.*/\u&/') Priority"
      echo "$PRIO_TASKS" | jq -r '.[] | "- \(.description)\(if .due_date then " — due: \(.due_date)" else "" end)"'
      echo ""
    fi
  done

  # Unset priority tasks
  UNSET_TASKS=$(echo "$TASKS" | jq '[.[] | select(.priority == null and .is_pinned != true)]')
  UNSET_COUNT=$(echo "$UNSET_TASKS" | jq 'length')
  if [[ "$UNSET_COUNT" -gt 0 ]]; then
    echo "## Other Tasks"
    echo "$UNSET_TASKS" | jq -r '.[] | "- \(.description)\(if .due_date then " — due: \(.due_date)" else "" end)"'
    echo ""
  fi

  # Recent voice note context
  ANALYSIS_COUNT=$(echo "$ANALYSES" | jq 'length' 2>/dev/null || echo "0")
  if [[ "$ANALYSIS_COUNT" -gt 0 ]]; then
    echo "## Recent Voice Context"
    echo "$ANALYSES" | jq -r '.[] | "- **\(.topics_primary)** (\(.sentiment)): \(.summary | split(". ")[0])."'
    echo ""

    # Extract themes
    ALL_TOPICS=$(echo "$ANALYSES" | jq -r '[.[] | .topics_primary, (.topics_secondary // [] | .[])] | unique | join(", ")')
    if [[ -n "$ALL_TOPICS" ]]; then
      echo "## Active Themes"
      echo "$ALL_TOPICS"
      echo ""
    fi
  fi

  # Summary line
  echo "---"
  echo "_${TASK_COUNT} open tasks from voice notes. Check voice.andykaufman.net for full details._"

} > "$OUTPUT_FILE"

# Record sync timestamp
date -Iseconds > "$LAST_SYNC_FILE"
echo "Synced ${TASK_COUNT} tasks to ${OUTPUT_FILE}"
