#!/usr/bin/env python3
"""
Check whether the peer pane is busy.

Capture the last few lines of the peer pane via `tmux capture-pane` and use
spinner glyph detection to decide whether Claude Code is thinking / running
tools / producing output.

Detection logic:
  - Scan upward from the bottom through at most 20 non-empty lines
  - Skip status bar / separator / user prompt / task checklist lines
  - If a line starts with a spinner glyph and contains '…' → busy

Usage:
  python3 tmux-idle-peer.py [-S socket] <peer_target>
  # peer_target format: session:window.pane (e.g. 0:4.1)

Output:
  idle    — peer is free, safe to send
  busy    — peer is busy, should wait
  unknown — cannot determine (pane missing, etc.)
"""
import argparse
import os
import subprocess
import sys

SPINNER_CHARS = set('✻✢✳✶✽')
DOT_SPINNERS = set('·•∙')
THINKING = '∴'

# Line types to skip
STATUS_BAR_CHARS = set('➜⏵')
USER_PROMPT = '❯'
TASK_CHECKLIST_CHARS = set('◻✔☐☒')


def get_socket_from_env():
    """Parse the socket path from $TMUX. Format: socket,session,pane"""
    tmux_env = os.environ.get("TMUX", "")
    if tmux_env:
        return tmux_env.split(",")[0]
    return None


def is_separator_line(trimmed: str) -> bool:
    """Pure dash line or titled separator (──── label ──)."""
    dash_count = sum(1 for c in trimmed if c in ('─', '━'))
    if dash_count == len(trimmed) and dash_count > 0:
        return True
    return dash_count >= 10 and trimmed[0] in ('─', '━') and trimmed[-1] in ('─', '━')


def is_active_spinner(trimmed: str) -> bool:
    """Line starts with a spinner glyph and contains '…' → busy."""
    if not trimmed:
        return False
    first = trimmed[0]
    is_spinner = first in SPINNER_CHARS or first in DOT_SPINNERS or first == THINKING
    return is_spinner and '…' in trimmed


def should_skip(trimmed: str) -> bool:
    """Status bar / separator / user prompt / task checklist — not part of the busy check."""
    if not trimmed:
        return True
    first = trimmed[0]
    if first in STATUS_BAR_CHARS:
        return True
    if first == USER_PROMPT:
        return True
    if first in TASK_CHECKLIST_CHARS:
        return True
    if is_separator_line(trimmed):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Check if peer pane is busy")
    parser.add_argument("-S", "--socket", help="tmux socket path (default: from $TMUX)")
    parser.add_argument("peer_target", help="target pane: session:window.pane")
    args = parser.parse_args()

    socket = args.socket or get_socket_from_env()
    if not socket:
        print("unknown")
        print("# no socket specified and $TMUX not set")
        return

    result = subprocess.run(
        ["tmux", "-S", socket, "capture-pane", "-t", args.peer_target, "-p", "-S", "-50"],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print("unknown")
        print(f"# capture-pane failed: {result.stderr.strip()}")
        return

    lines = result.stdout.rstrip("\n").split("\n")

    # Scan upward from the bottom through at most 20 non-empty lines
    tail_seen = 0
    for raw in reversed(lines):
        trimmed = raw.strip()
        if not trimmed:
            continue
        if tail_seen >= 20:
            break
        if not should_skip(trimmed) and is_active_spinner(trimmed):
            print("busy")
            return
        tail_seen += 1

    print("idle")


if __name__ == "__main__":
    main()
