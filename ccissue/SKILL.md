---
name: ccissue
description: Write bugs, design flaws, or technical debt found in the current discussion into a structured issue document in the project's .ccbus/ccissue/ directory.
---

# ccissue

Write bugs, design flaws, or technical debt found in the current discussion into a structured issue document, stored in the project's `.ccbus/ccissue/` directory (`mkdir -p` first if it doesn't exist).

`<skill_dir>` is the directory containing this SKILL.md. Resolve it from your context, or from the project root with:

```bash
find ~/.claude .claude -path '*ccissue/SKILL.md' -not -path '*/.git/*' 2>/dev/null | head -1 | xargs dirname
```

## Triggers

User says:
- "write an issue"
- "record this problem"
- "ccissue"
- "/ccissue"

## File naming

```
.ccbus/ccissue/issue-{YYYY-MM-DD}-{author}-{slug}.md
```

- Date is today
- author: run `<skill_dir>/whoami.sh --file` (filename-safe format, `-` instead of `:`)
- slug: lowercase hyphenated English, capturing the essence of the issue (e.g. `zombie-interactive`, `scroll-position-conflict`)

## Document structure

```markdown
---
title: "{one-line title}"
type: bug | design-debt | enhancement
severity: critical | high | medium | low
component: {affected module path, e.g. daemon/hooks, mobile-ios/Views}
created: {YYYY-MM-DD}
reported_by: {run <skill_dir>/whoami.sh to get this value}
status: open
affects:
  - {key file path}
  - {key file path}
related:
  - {related function names, module names, or other issue slugs}
---

# {Title}

## Symptoms

User-observable external behavior. Include specific logs, screenshot descriptions, or reproduction steps.

## Root cause

Technical analysis of the cause. List each failure path separately:

### Failure path 1: {name} (primary/secondary)

Code-level explanation with key code snippets.

### Failure path 2: {name}

...

## Impact

List or table of which features are affected and which scenarios are unaffected.

## Fix plan

### Approach overview

One paragraph describing the fix strategy.

### Implementation steps

Numbered list of concrete changes. Each step includes:
- which file to change
- what method/logic to add
- key pseudocode or signatures

### Deliberately unchanged

Explicitly list existing behavior that is intentionally kept, to prevent scope creep.
```

## Writing principles

- Root-cause analysis must reach the code level, with filenames and key code snippets
- Distinguish "primary cause" from "secondary/edge causes"
- The fix plan gives concrete function signatures and call sites — no vague "just optimize it"
- If the issue spans multiple subsystems, use a table for the coverage matrix
- In front-matter, `affects` lists files that need changing; `related` lists modules that are related but unchanged
