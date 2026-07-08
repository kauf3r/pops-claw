#!/bin/bash
# Sync research briefs from EC2 to local Mac, then bridge to LLM-context KB
# Run manually or via launchd: ~/Library/LaunchAgents/com.andykaufman.research-sync.plist
set -euo pipefail

LOCAL_DIR="$HOME/dev/pops-claw/research-briefs"
REMOTE_DIR="ubuntu@100.72.143.9:/home/ubuntu/clawd/research-briefs/"
SSH_KEY="$HOME/.ssh/clawdbot-key.pem"
KB_DIR="$HOME/Desktop/Projects/claude-life-os/LLM-context/sources"
LOG="$HOME/dev/pops-claw/scripts/sync-research-briefs.log"

mkdir -p "$LOCAL_DIR"

# --- Step 1: Rsync EC2 → local (new files only) ---
echo "[$(date '+%Y-%m-%d %H:%M')] Starting sync..." >> "$LOG"

rsync -avz --ignore-existing \
  -e "ssh -i $SSH_KEY -o ConnectTimeout=10 -o BatchMode=yes" \
  "$REMOTE_DIR" "$LOCAL_DIR/" 2>/dev/null || {
  echo "[$(date '+%Y-%m-%d %H:%M')] rsync failed (EC2 unreachable?)" >> "$LOG"
  exit 1
}

BRIEF_COUNT=$(ls "$LOCAL_DIR"/*.md 2>/dev/null | grep -cv INDEX || true)
echo "[$(date '+%Y-%m-%d %H:%M')] Synced $BRIEF_COUNT briefs from EC2" >> "$LOG"

# --- Step 2: Bridge briefs → LLM-context with YAML frontmatter ---

# Track-to-domain mapping
track_to_domain() {
  local track="$1"
  case "$track" in
    uas)       echo "uas" ;;
    land)      echo "land-investing" ;;
    ai_coding) echo "productivity" ;;
    business)  echo "productivity" ;;
    content)   echo "productivity" ;;
    *)         echo "productivity" ;;
  esac
}

# Extract track from brief header line: > **Source** · Type · `track` · date
extract_track() {
  local file="$1"
  sed -n 's/.*`\([a-z_]*\)`.*/\1/p' "$file" 2>/dev/null | head -1
  # Returns empty if no backtick-delimited track found
}

# Extract date from filename: 2026-03-22-title.md → 2026-03-22
extract_date() {
  local filename
  filename=$(basename "$1")
  echo "$filename" | sed -n 's/^\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p'
}

BRIDGED=0
for brief in "$LOCAL_DIR"/2026-*.md; do
  [ -f "$brief" ] || continue

  filename=$(basename "$brief")
  # Target filename: research-brief-{original-name}
  target="$KB_DIR/research-brief-${filename}"

  # Skip if already bridged
  [ -f "$target" ] && continue

  track=$(extract_track "$brief")
  [ -z "$track" ] && track="ai_coding"
  domain=$(track_to_domain "$track")
  created=$(extract_date "$brief")

  # Build YAML frontmatter + original content
  {
    echo "---"
    echo "kb_type: source-summary"
    echo "confidence: high"
    echo "provenance: pops-claw-research"
    echo "sources: [research.db]"
    echo "domain: $domain"
    echo "type: research-brief"
    echo "created: $created"
    echo "updated: $created"
    echo "tags: [kb, source-summary, research-brief, $track]"
    echo "---"
    echo ""
    cat "$brief"
  } > "$target"

  BRIDGED=$((BRIDGED + 1))
  echo "  Bridged: $filename → research-brief-${filename}" >> "$LOG"
done

echo "[$(date '+%Y-%m-%d %H:%M')] Bridged $BRIDGED new briefs to LLM-context" >> "$LOG"
echo "Sync complete: $BRIEF_COUNT briefs, $BRIDGED newly bridged to KB"
