---
name: cccombat
description: Cross-Claude collaboration verification — two peer LLM instances discuss and verify each other's conclusions on code reviews, bug verification, and design reviews, then commit the consensus to disk.
---

# cccombat — Cross-Claude Collaboration Verification

## Purpose

Two peer Claude instances verify, discuss, or challenge each other on a technical conclusion; once consensus is reached, they write it up and commit it to disk.

**Typical scenarios:**
- **E2E bug verification** — one side lists bug conclusions, the other reads the code and verifies each one
- **Code review** — one side lists review findings, the other cross-checks
- **Design review** — one side proposes an approach, the other assesses risks
- **Execution plan confirmation** — one side lists the changes to be made, the other reviews and approves

## Document storage

All documents live in `.ccflow/cccombat/`.

Filename format:

```
.ccflow/cccombat/<topic>-<YYYY-MM-DD>-seq-<N>-<author>.md
```

| Field | Description |
|------|------|
| `topic` | Topic, e.g. `bug-verification`, `code-review`, `design-review` |
| `YYYY-MM-DD` | Date |
| `seq-1` | First message; the peer's reply uses `seq-2`; the next reply `seq-3`, and so on |
| `author` | Author pane index, format `tmux-<session>-<window>.<pane>`, e.g. `tmux-main-2.4` |

Messages in the same thread are chained by seq number. Before writing, run `ls .ccflow/cccombat/<topic>-<date>-seq-*-*.md` to find the latest seq.

## Document format

Must include front-matter:

```yaml
---
title: "Document title"
date: YYYY-MM-DD
author: "tmux-<session>-<window>.<pane>"   # e.g. tmux-main-2.4
recipient: "The other Claude"
source_document: "Path to the referenced source file (if any)"
summary: "One-line statement of this document's position"
purpose: >
  The purpose of this document. For example:
  - Ask the peer to verify whether this document's conclusions are correct
  - Accept the peer's conclusions and add the plan I will execute
  - Dispute a conclusion, raise objections and reasons
  - Confirm receipt of approval; protocol ends
---
```

Body content is free-form, but should include:
- Which files were referenced
- Code is the source of truth — not docs and not the other party's claims
- If disagreeing, point out exactly which item is wrong and why

## Workflow

All scripts live in `scripts/` next to this SKILL.md. Resolve `<skill_dir>` — the directory containing this SKILL.md — from your context, or from the project root with:

```bash
find ~/.claude .claude -path '*cccombat/SKILL.md' -not -path '*/.git/*' 2>/dev/null | head -1 | xargs dirname
```

Invoke scripts as `bash <skill_dir>/scripts/api-*.sh`.

### Step 1: Find the peer

**Search in real time before every send** (never from cache or docs):

```bash
bash <skill_dir>/scripts/api-find-peer.sh
```

Output:
```
my_pane=<my identifier>
peer_pane=<peer identifier>
peer_target=<target to pass to the send/idle scripts>
```

- `my_pane` / `peer_pane` — filename-safe identifiers, used in document filenames and the front-matter `author` field
- `peer_target` — passed directly to `api-idle-peer.sh` and `api-send-peer.sh`; no need to parse its format

If no peer is found, the output is `no_peer_found`; fall back to:

1. **Infer from the current thread's documents**: `ls .ccflow/cccombat/<topic>-<date>-seq-*-*.md`, read the latest document's front-matter, and take the `author` field (a document from the peer) or `recipient` field (your own document) as `peer_pane`.
2. **Infer from a received `/cccombat` message**: the sender's document filename contains the identifier; use it directly as `peer_pane`.
3. **Derive `peer_target`**: replace the first `-` in `peer_pane` with `:` (e.g. `main-5.1` → `main:5.1`).

The protocol terminates only when both the script and the fallbacks fail to determine a peer.

### Step 1.5: Wait for the peer to be idle

After finding the peer and before sending, **check whether the peer is busy**. If the peer is thinking / running tools / producing output, sending anyway would interrupt their workflow and the message may be swallowed or mixed into their output.

```bash
bash <skill_dir>/scripts/api-idle-peer.sh <peer_target>
```

Output:
- `idle` — peer is free; proceed to Step 2
- `busy` — peer is busy; **wait 5 minutes and retry**
- `unknown` — cannot determine; treat as idle and proceed to Step 2

**Wait-and-retry rules (exponential backoff):**
1. On `busy`, retry at these intervals:
   `10s → 20s → 40s → 80s → 160s → 320s → 320s → 320s → 320s → 320s`
2. Retry at most **10 times** (= up to ~19 minutes of waiting)
3. Report status to the user on each retry: `Peer is busy, waiting… (retry N/10, next attempt in Xs)`
4. If all 10 attempts return `busy`, give up waiting and **send anyway** (with a note: the peer may be busy for a long time; the message was force-sent)
5. The document should already be on disk during the wait (Step 2's first step runs first); only the notification is delayed

### Step 2: Write and send

1. Write the document to `.ccflow/cccombat/<topic>-<date>-seq-<N>-<author>.md`
2. **Run the Step 1.5 idle wait** (the document is already on disk; this is just waiting for the right moment to send)
3. When notifying the peer, **don't send just the file path** — summarize the point in one line so the peer knows what to do at a glance:

```bash
bash <skill_dir>/scripts/api-send-peer.sh <peer_target> "/cccombat <notification message>"
```

**Send semantics**: exit 0 **guarantees the message was submitted** (not just typed into the peer's input box). The underlying `tmux-send-peer.py` runs `capture-pane` after sending to verify the prompt has cleared; if the Enter was swallowed by the peer's TUI (common at 100% context), it re-sends Enter, up to 3 times.

- Exit code `0` → submitted; continue.
- Exit code `2` → not submitted after 3 retries; stderr says the peer's input box is occupied and `/clear` may be needed. **Do not pretend the send succeeded** — report the status to the user.
- Exit code `1` → tmux command failed (target pane missing, etc.).

#### Notification message templates (choose by document purpose)

| Scenario | Example message |
|------|----------|
| **Initiate review** | `Just reviewed the diff, found X passes + Y suspicious points, in <filename>, please take a look.` |
| **Verification reply** | `Verification done, X correct + Y need fixing. In <filename>, please decide next steps.` |
| **Propose fix plan** | `Issues confirmed, I will fix X issues, plan in <filename>, please approve.` |
| **Approve execution** | `Fix plan is reasonable, approved, in <filename>, go ahead.` |
| **Raise objection** | `X conclusions not accepted, details in <filename>, please confirm.` |
| **Fix completed** | `Done, all X patches applied, report in <filename>, please verify.` |
| **Protocol ends** | `Received, confirmed, protocol ends. In <filename>.` |

### Step 3: The recipient writes

After receiving a `/cccombat` notification:
1. Read the peer's document
2. Verify each conclusion **with code as the source of truth**
3. Write the reply as seq-<N+1> to disk
4. Notify the peer (likewise summarize in one line; see the templates above)

### Step 4: Next steps by reply type

After the recipient writes, there are three cases:

**Important convention**:
- **A combat participant performs only one action at a time**: either sending a document to advance the negotiation, or modifying code — never both at once.

#### Case A: Discussion over (consensus reached, nothing to execute)

If the verification result is "all conclusions correct, no fix needed":
- The original sender writes seq-<N+1> to acknowledge receipt
- Protocol ends

**Example chain**:
```
seq-1 (initiate): "Please review the code, found issues A, B, C"
seq-2 (verify): "Verified, A, B, C all correct, but all minor, no fix needed"
seq-3 (ack): "Received, protocol ends"
→ done in 3 rounds
```

#### Case B: Fix needed (verification done, issues confirmed)

If the verification result is "issues confirmed, fix needed":
- **The verifier does not proactively propose a fix plan**; they only verify
- **The original initiator decides next steps in seq-<N+1>**:
  - Propose a fix plan: "I will fix issues #1 #2 #3" → enter Case C
  - Or decide not to fix: "Issues confirmed, not fixing for now" → protocol ends
- The verifier only says "verification done, issues confirmed, please decide next steps"

**Example chain**:
```
seq-1 (initiate): "Please review the code, found issues A, B"
seq-2 (verify): "Verified, A and B do exist, need fixing"
seq-3 (initiator): "I will fix issues A and B, plan as follows…"
→ enter Case C, awaiting approval
```

#### Case C: Approve execution (fix plan proposed)

After the original initiator proposes a fix plan:
- **Execution requires the verifier's review and approval**
- The verifier writes seq-<N+1>: approve, request changes, or reject
- Execute only after explicit approval

**Example chain**:
```
seq-1 (initiate): "Please review the code, found issues A, B"
seq-2 (verify): "Verified, issues confirmed, need fixing"
seq-3 (initiator): "I will fix issues A and B"
seq-4 (approve): "Approved"
→ after approval, start changing code
seq-5 (done): "Fixes complete, please verify"
```

### Step 5: Handling disagreement

If one side rejects the other's conclusion:
- Write up which item is wrong and why
- The peer replies in writing (correction or rebuttal)
- Continue with incrementing seq

**Discussion limit**: at most 10 rounds of seq-N discussion. If no consensus by round 10:
1. Both sides write a seq-10 reply consisting of a single sentence: "idiot."
2. After writing, stop the discussion — **no acting on your own**, **no continuing to seq-6**
3. Submit the dispute to the Boss for adjudication; wait for the Boss's decision before continuing

## Notes

- **Code is the source of truth** — don't blindly follow existing docs or the other party's claims; read the code yourself
- **Write before acting** — for execution plans, get the peer's approval before touching code
- **Prefix messages with `/cccombat`** — all sent messages start with `/cccombat`
- **Find the peer in real time** — always use `api-find-peer.sh`; on `no_peer_found`, fall back to document front-matter or filename inference
- **ls before writing** — avoid overwriting or duplicating an existing thread
- **Complete front-matter** — especially `author` and `purpose`
