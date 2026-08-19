#!/bin/bash
# Find cccombat peer via tmux.
SCRIPTS="$(dirname "$0")"

if [[ -n "$TMUX_PANE" ]]; then
  python3 "$SCRIPTS/tmux-find-peer.py"
else
  echo "no_peer_found"
  echo "# TMUX_PANE is not set"
  exit 1
fi
