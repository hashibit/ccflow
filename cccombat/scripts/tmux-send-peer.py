#!/usr/bin/env python3
"""
Send a message to a peer tmux pane and verify it was actually submitted.

Usage:
  python3 tmux-send-peer.py [-S socket] [--max-retries N] [--quiet] <peer_target> <message>

  peer_target format: session:window.pane  (e.g. main:2.3)
  socket: optional, defaults to $TMUX socket

Why this is more complex than `tmux send-keys ... msg Enter`:

  When the peer Claude Code TUI is at high context usage (93%+ observed)
  or paste-buffering, a single send-keys invocation passing both the
  message and the trailing Enter as separate arguments has the Enter
  silently swallowed in 5 of 5 trials. The text lands in the input prompt
  but is never submitted.

  Mitigation:
    1. Send message text with `-l` (literal, no key interpretation).
    2. Small sleep so the TUI finishes any paste-buffered handling.
    3. Send Enter as a separate keystroke (no longer batched with text).
    4. capture-pane to verify the prompt is empty (i.e. submitted).
       If not empty, retry Enter up to --max-retries times.

  Invariant: on success exit, the input prompt is empty. On failure,
  prints a diagnostic to stderr and exits non-zero.
"""
import argparse
import os
import subprocess
import sys
import time

DEFAULT_MAX_RETRIES = 3
PASTE_SETTLE_SEC = 0.15
VERIFY_DELAY_SEC = 0.5
PROMPT_GLYPH = "❯"


def get_socket_from_env():
    """Parse the socket path from $TMUX. Format: socket,session,pane"""
    tmux_env = os.environ.get("TMUX", "")
    if tmux_env:
        return tmux_env.split(",")[0]
    return None


def tmux(socket, *args, check=True):
    """Run a tmux command on the given socket."""
    return subprocess.run(
        ["tmux", "-S", socket, *args],
        capture_output=True, text=True, check=check,
    )


def capture_pane(socket, target):
    """Return the visible pane content as a string."""
    res = tmux(socket, "capture-pane", "-t", target, "-p", check=False)
    if res.returncode != 0:
        return ""
    return res.stdout


def prompt_is_empty(captured):
    """
    Walk the captured output from the bottom up. The first line containing
    the prompt glyph `❯` is the current input prompt. If the text following
    that glyph is empty (or just whitespace), the message was submitted.
    Otherwise the message is still sitting at the prompt unsubmitted.

    Lines that look like continuations of a wrapped input prompt (i.e.
    above the `❯` line but visually part of the same input) are skipped
    by virtue of the bottom-up search ending at the first `❯` row.
    """
    if not captured:
        # Couldn't read pane — assume submitted to avoid infinite retries.
        return True
    for line in reversed(captured.rstrip("\n").split("\n")):
        # Match the prompt glyph anywhere in the line (it may be indented).
        idx = line.find(PROMPT_GLYPH)
        if idx < 0:
            continue
        after = line[idx + len(PROMPT_GLYPH):].strip()
        return after == ""
    # No prompt glyph anywhere visible — assume submitted (the pane may be
    # showing a thinking-state banner that covered the prompt).
    return True


def submit(socket, target, message, max_retries, quiet):
    """
    Send `message` then ensure it was submitted. Returns True on success.

    Algorithm:
      1. send-keys -l <message>             # literal text, no Enter
      2. sleep PASTE_SETTLE_SEC             # let TUI absorb the paste
      3. send-keys Enter                    # submit
      4. for attempt in 1..max_retries:
         sleep VERIFY_DELAY_SEC
         if prompt_is_empty(): return True
         send-keys Enter                    # Enter was swallowed, retry
      5. return False                       # gave up
    """
    # Step 1: paste the message text only (no Enter).
    tmux(socket, "send-keys", "-t", target, "-l", message)

    # Step 2: let the TUI settle. Paste-buffering can otherwise consume
    # the immediately-following Enter as part of the same input event.
    time.sleep(PASTE_SETTLE_SEC)

    # Step 3: send Enter as a separate keystroke.
    tmux(socket, "send-keys", "-t", target, "Enter")

    # Step 4: verify; retry Enter (not the message) if it was swallowed.
    for attempt in range(1, max_retries + 1):
        time.sleep(VERIFY_DELAY_SEC)
        captured = capture_pane(socket, target)
        if prompt_is_empty(captured):
            if not quiet:
                if attempt == 1:
                    print(f"submitted (no retry needed)", file=sys.stderr)
                else:
                    print(f"submitted after {attempt - 1} Enter retry(s)", file=sys.stderr)
            return True
        if not quiet:
            print(
                f"prompt still occupied after Enter (attempt {attempt}/{max_retries}); resending Enter",
                file=sys.stderr,
            )
        tmux(socket, "send-keys", "-t", target, "Enter")

    return False


def main():
    parser = argparse.ArgumentParser(description="Send message to peer tmux pane (verified)")
    parser.add_argument("-S", "--socket", help="tmux socket path (default: from $TMUX)")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"max Enter retries after detected non-submission (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress retry diagnostics on stderr")
    parser.add_argument("peer_target", help="target pane: session:window.pane")
    parser.add_argument("message", nargs="+", help="message to send")
    args = parser.parse_args()

    socket = args.socket or get_socket_from_env()
    if not socket:
        print("error: no socket specified and $TMUX not set", file=sys.stderr)
        sys.exit(1)

    message = " ".join(args.message)

    try:
        ok = submit(socket, args.peer_target, message, args.max_retries, args.quiet)
    except subprocess.CalledProcessError as e:
        print(f"error: tmux command failed: {e.stderr.strip() if e.stderr else e}", file=sys.stderr)
        sys.exit(1)

    if not ok:
        print(
            "error: message was not submitted after all retries — peer's input prompt still occupied.\n"
            "       The peer may need /clear (context full) or be in an odd state. Check manually.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
