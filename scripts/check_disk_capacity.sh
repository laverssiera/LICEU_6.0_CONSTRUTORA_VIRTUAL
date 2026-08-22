#!/usr/bin/env bash
set -euo pipefail

TARGET_PATH="${1:-/workspaces}"
WARN_FREE_PERCENT="${WARN_FREE_PERCENT:-20}"
CRIT_FREE_PERCENT="${CRIT_FREE_PERCENT:-10}"
WARN_INODE_FREE_PERCENT="${WARN_INODE_FREE_PERCENT:-20}"
CRIT_INODE_FREE_PERCENT="${CRIT_INODE_FREE_PERCENT:-10}"
SHOW_TOP="${SHOW_TOP:-1}"

if [[ ! -d "$TARGET_PATH" ]]; then
  echo "ERROR: target path not found: $TARGET_PATH" >&2
  exit 1
fi

line=$(df -P "$TARGET_PATH" | awk 'NR==2')
itotal=$(df -Pi "$TARGET_PATH" | awk 'NR==2')

size_kb=$(awk '{print $2}' <<<"$line")
used_kb=$(awk '{print $3}' <<<"$line")
avail_kb=$(awk '{print $4}' <<<"$line")
use_pct=$(awk '{gsub("%","",$5); print $5}' <<<"$line")

inode_total=$(awk '{print $2}' <<<"$itotal")
inode_used=$(awk '{print $3}' <<<"$itotal")
inode_free=$(awk '{print $4}' <<<"$itotal")
inode_use_pct=$(awk '{gsub("%","",$5); print $5}' <<<"$itotal")

free_pct=$((100 - use_pct))
inode_free_pct=$((100 - inode_use_pct))

status="HEALTHY"
if (( free_pct < CRIT_FREE_PERCENT || inode_free_pct < CRIT_INODE_FREE_PERCENT )); then
  status="CRITICAL"
elif (( free_pct < WARN_FREE_PERCENT || inode_free_pct < WARN_INODE_FREE_PERCENT )); then
  status="WARNING"
fi

size_gb=$(awk -v kb="$size_kb" 'BEGIN {printf "%.2f", kb/1024/1024}')
used_gb=$(awk -v kb="$used_kb" 'BEGIN {printf "%.2f", kb/1024/1024}')
avail_gb=$(awk -v kb="$avail_kb" 'BEGIN {printf "%.2f", kb/1024/1024}')

docker_df=$(docker system df 2>/dev/null | tr '\n' ';' | sed 's/"/\\"/g' || true)

printf '{\n'
printf '  "path": "%s",\n' "$TARGET_PATH"
printf '  "status": "%s",\n' "$status"
printf '  "disk": {"total_gb": %s, "used_gb": %s, "free_gb": %s, "free_percent": %d},\n' "$size_gb" "$used_gb" "$avail_gb" "$free_pct"
printf '  "inodes": {"total": %s, "used": %s, "free": %s, "free_percent": %d},\n' "$inode_total" "$inode_used" "$inode_free" "$inode_free_pct"
printf '  "thresholds": {"warn_free_percent": %d, "crit_free_percent": %d, "warn_inode_free_percent": %d, "crit_inode_free_percent": %d},\n' "$WARN_FREE_PERCENT" "$CRIT_FREE_PERCENT" "$WARN_INODE_FREE_PERCENT" "$CRIT_INODE_FREE_PERCENT"
printf '  "docker_system_df": "%s"\n' "$docker_df"
printf '}\n'

if [[ "$SHOW_TOP" == "1" ]]; then
  {
    echo "Top workspace consumers (du -sh, top 10):"
    du -sh /workspaces/LICEU_6.0_CONSTRUTORA_VIRTUAL/* 2>/dev/null | sort -hr | head -n 10 || true
  } >&2
fi

if [[ "$status" == "CRITICAL" ]]; then
  exit 2
fi

exit 0
