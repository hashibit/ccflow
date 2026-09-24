---
name: ccticket
description: Record requirements, bugs, proposals, improvements, or technical debt from the current discussion as structured tickets in the project's .ccflow/ccticket/ directory.
---

# ccticket

Record work items from the current discussion as structured tickets, stored in the project's `.ccflow/ccticket/` directory (`mkdir -p` first if it doesn't exist).

`<skill_dir>` is the directory containing this SKILL.md. Resolve it from your context, or from the project root with:

```bash
find ~/.claude .claude -path '*ccticket/SKILL.md' -not -path '*/.git/*' 2>/dev/null | head -1 | xargs dirname
```

## Triggers

User says:
- "write a ticket" / "record a work item"
- "record this problem"
- "ccticket"
- "/ccticket"

## File naming

```
.ccflow/ccticket/ticket-{YYYY-MM-DD}-{author}-{slug}.md
```

- Date is today
- author: run `<skill_dir>/whoami.sh --file` (filename-safe format, `-` instead of `:`)
- slug: lowercase hyphenated English, capturing the essence of the issue (e.g. `zombie-interactive`, `scroll-position-conflict`)

## Ticket categories

Choose one `type` based on the ticket's primary goal:

- `requirement`: a requested new capability or explicit product/business need.
- `bug`: existing behavior is incorrect, broken, or regressed.
- `proposal`: an idea or design direction that still needs evaluation or a decision.
- `improvement`: an accepted change to improve existing usability, performance, or maintainability without fixing a defect.
- `tech-debt`: an implementation or architecture issue that raises future cost, even if there is no immediate user-facing failure.

A requirement remains `requirement` when its implementation is undecided; use `proposal` when whether to pursue the idea is undecided. Ask for clarification if the primary category cannot be determined.

## Priority

Set `priority` independently of `type`, using impact and urgency:

- `P0`: active outage, data loss/security exposure, or a critical path unusable for nearly everyone; immediate action required.
- `P1`: major user workflow broken or severe impact to an important group; should be addressed urgently.
- `P2`: moderate impact, workaround exists, or a normal planned requirement/improvement.
- `P3`: low impact, minor polish, or exploratory proposal with no near-term commitment.

Use the highest priority justified by evidence. Do not assign P0/P1 solely because a request is important to one person; note uncertainty when impact is unclear.

## Document structure

```markdown
---
title: "{one-line title}"
type: requirement | bug | proposal | improvement | tech-debt
priority: P0 | P1 | P2 | P3
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
