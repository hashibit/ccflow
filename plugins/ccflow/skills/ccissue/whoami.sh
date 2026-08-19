#!/bin/bash
# Print the current tmux target in two formats:
#   --file   → filesystem-safe: "tmux-{session}-{window}.{pane}" (for filenames)
#   (default)→ canonical:       "tmux-{session}:{window}.{pane}" (for front-matter)
# Falls back to "unknown" if not inside tmux.
if [ -z "$TMUX_PANE" ]; then
  echo "unknown"
  exit 0
fi

session=$(tmux display-message -p '#{session_name}' 2>/dev/null)
window=$(tmux display-message -p '#{window_index}' 2>/dev/null)
pane=$(tmux display-message -p '#{pane_index}' 2>/dev/null)

if [ "$1" = "--file" ]; then
  echo "tmux-${session}-${window}.${pane}"
else
  echo "tmux-${session}:${window}.${pane}"
fi
