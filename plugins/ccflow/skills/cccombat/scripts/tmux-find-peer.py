#!/usr/bin/env python3
"""
cccombat peer finder — find another Claude pane for the same project in the current tmux window.

Output format:
  socket=/tmp/tmux-501/default
  my_pane=main-2.4
  peer_pane=main-2.3
  peer_target=main:2.3

Prints no_peer_found if no peer can be found.
"""
import argparse
import os
import subprocess


def get_socket_from_env():
    """Parse the socket path from $TMUX. Format: socket,session,pane"""
    tmux_env = os.environ.get("TMUX", "")
    if tmux_env:
        return tmux_env.split(",")[0]
    return None


def pane_loc_to_label(session, window, pane):
    """session-window.pane format (filename-safe, no colons)"""
    return f"{session}-{window}.{pane}"


def pane_loc_to_target(session, window, pane):
    """Format used by `tmux send-keys -t`: session:window.pane"""
    return f"{session}:{window}.{pane}"


def main():
    parser = argparse.ArgumentParser(description="Find peer Claude pane in current tmux window")
    parser.add_argument("-S", "--socket", help="tmux socket path (default: from $TMUX)")
    args = parser.parse_args()

    socket = args.socket or get_socket_from_env()
    if not socket:
        print("no_peer_found")
        print("# no socket specified and $TMUX not set")
        return

    print(f"socket={socket}")

    # Get our own pane_id (e.g. %74) from the TMUX_PANE environment variable.
    my_pane_id = os.environ.get("TMUX_PANE", "").strip()

    if not my_pane_id:
        print("no_peer_found")
        print("# TMUX_PANE not set, not in a tmux session")
        return

    # Get info for all panes: pane_id, session, window, pane_index, path
    cmd = ["tmux", "-S", socket, "list-panes", "-a", "-F",
           "#{pane_id} #{session_name} #{window_index} #{pane_index} #{pane_current_path}"]
    lines = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split("\n")

    my_label = None
    my_session = None
    my_window = None
    my_cwd = None

    # Find ourselves
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        pane_id, session, window, pane_idx = parts[0], parts[1], parts[2], parts[3]
        pane_path = " ".join(parts[4:])

        if pane_id == my_pane_id:
            my_label = pane_loc_to_label(session, window, pane_idx)
            my_session = session
            my_window = window
            my_cwd = pane_path
            break

    if not my_label:
        print("no_peer_found")
        print(f"# pane_id {my_pane_id} not found in tmux list-panes")
        return

    print(f"my_pane={my_label}")

    # Look for another pane in the same window to be the peer
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        pane_id, session, window, pane_idx = parts[0], parts[1], parts[2], parts[3]
        pane_path = " ".join(parts[4:])

        peer_label = pane_loc_to_label(session, window, pane_idx)

        # Exclude ourselves
        if peer_label == my_label:
            continue

        # Must be in the same session and window
        if session != my_session or window != my_window:
            continue

        # cwd must match
        if pane_path != my_cwd:
            continue

        peer_target = pane_loc_to_target(session, window, pane_idx)
        print(f"peer_pane={peer_label}")
        print(f"peer_target={peer_target}")
        return

    print("no_peer_found")


if __name__ == "__main__":
    main()
