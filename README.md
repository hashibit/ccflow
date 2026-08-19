# ccflow

Two Claude Code skills for cross-instance collaboration inside one tmux window:

- **cccombat** — two peer Claude sessions verify, challenge, or approve each other's conclusions (code review, bug verification, design review). The exchange is written to the project's `.ccflow/cccombat/` directory.
- **ccissue** — records bugs, design flaws, or technical debt from the current discussion as a structured issue document in the project's `.ccflow/ccissue/` directory.

## Requirements

- Claude Code
- tmux — both skills assume you run **inside a tmux session**. Outside tmux, `$TMUX_PANE` is unset: peer discovery returns `no_peer_found` and `whoami.sh` prints `unknown`.
- python3 (cccombat peer scripts)
- bash
- Two Claude Code sessions in the **same tmux window** and the **same project directory** — messages are exchanged as files under the project's `.ccflow/`, so both instances must share that working directory.

## Install

### Via plugin marketplace (recommended)

Both skills ship in a single plugin `ccflow`, served by this repo's marketplace. Once per machine:

```
/plugin marketplace add <this-repo-url>   # e.g. owner/ccflow (GitHub shorthand) or a full git URL
/plugin install ccflow@ccflow
```

- Skills are invoked as `/ccflow:cccombat` and `/ccflow:ccissue` (namespaced); bare `/cccombat` / `/ccissue` also resolve unless a same-named command already exists (requires Claude Code v2.1.216+).
- Updates: bump `version` in `plugins/ccflow/.claude-plugin/plugin.json`, push, then teammates run `/plugin marketplace update ccflow` — or enable auto-update for the marketplace in `/plugin` (off by default for non-Anthropic marketplaces).
- Private repo note: teammates need `gh auth setup-git` (or another git credential helper) so background updates can `git pull`. If the GitHub shorthand clones over SSH and that fails, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.

### Via symlink (offline / non-git fallback)

Skills resolve their own scripts relative to the SKILL.md location, so they work from any skills directory (user level, project level, or custom):

```bash
./link.sh                                  # user level: ~/.claude/skills
./link.sh /path/to/project/.claude/skills  # project level
./link.sh -f                               # replace existing real dirs with symlinks
```

`link.sh` symlinks `cccombat/` and `ccissue/` into the target directory. To uninstall, delete the symlinks from the skills directory.

## Usage

Start two Claude Code sessions in two panes of the same tmux window, then invoke `/cccombat` (or say "ccissue") in either pane and follow the skill's instructions.
