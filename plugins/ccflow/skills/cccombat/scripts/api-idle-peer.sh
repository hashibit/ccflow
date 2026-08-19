#!/bin/bash
# Check if peer is idle.
# Usage: api-idle-peer.sh <peer_target>
SCRIPTS="$(dirname "$0")"

if [[ -n "$TMUX_PANE" ]]; then
  python3 "$SCRIPTS/tmux-idle-peer.py" "$1"
else
  echo "unknown"
  echo "# TMUX_PANE not set: $1" >&2
  exit 1
fi
