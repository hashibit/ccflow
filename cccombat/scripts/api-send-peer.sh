#!/bin/bash
# Send message to peer via tmux.
# Usage: api-send-peer.sh <peer_target> <message>
SCRIPTS="$(dirname "$0")"

if [[ -n "$TMUX_PANE" ]]; then
  python3 "$SCRIPTS/tmux-send-peer.py" "$@"
else
  echo "error: TMUX_PANE not set: $1" >&2
  exit 1
fi
