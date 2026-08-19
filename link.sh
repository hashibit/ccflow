#!/bin/bash
# Symlink each skill in this repo into a skills directory.
# Usage:
#   ./link.sh                  link into ~/.claude/skills (default)
#   ./link.sh <skills_dir>     link into any skills dir, e.g. /path/to/project/.claude/skills
#   -f, --force                replace existing non-symlink directories
set -euo pipefail

usage() {
    echo "Usage: ./link.sh [skills_dir] [-f|--force]"
    echo "  skills_dir  target skills directory (default: ~/.claude/skills)"
    echo "  -f          replace existing non-symlink directories"
}

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
FORCE=0

for arg in "$@"; do
    case "$arg" in
        -f|--force) FORCE=1 ;;
        -h|--help) usage; exit 0 ;;
        *) SKILLS_DIR="$arg" ;;
    esac
done

mkdir -p "$SKILLS_DIR"

# Discover skills: plugin skill dirs containing SKILL.md (case-insensitive).
for skill_dir in "$REPO_ROOT"/plugins/*/skills/*/; do
    if [[ ! -f "$skill_dir/SKILL.md" && ! -f "$skill_dir/skill.md" ]]; then
        continue
    fi
    name="$(basename "$skill_dir")"
    link="$SKILLS_DIR/$name"

    if [[ -L "$link" ]]; then
        if [[ "$(readlink "$link")" == "$skill_dir" ]]; then
            echo "ok      $link (already linked)"
            continue
        fi
        rm "$link"
    elif [[ -e "$link" ]]; then
        if [[ $FORCE -eq 1 ]]; then
            rm -rf "$link"
        else
            echo "skip    $link (exists, not a symlink; use -f to replace)"
            continue
        fi
    fi

    ln -s "$skill_dir" "$link"
    echo "linked  $link -> $skill_dir"
done
