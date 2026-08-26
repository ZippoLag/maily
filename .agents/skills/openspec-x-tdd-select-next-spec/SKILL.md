---
name: openspec-x-tdd-select-next-spec
description: Triage pending OpenSpec changes, pick the next one to implement, and land on its branch. Returns structured selection result. Use as step 1 of openspec-x-tdd-apply-all loop or standalone.
allowed-tools: Bash(openspec:*), Bash(git:*)
license: MIT
compatibility: Requires openspec CLI and git.
metadata:
  author: project
  version: "2.0.0"
---

Triage the pending OpenSpec changes, choose the next one to implement based on scoring, and land on its branch. **Returns a structured JSON result** for the orchestrator.

This is an improved version of `openspec-x-tdd-select-next-spec` with:
- Structured input/output contracts
- Better triage outcome tracking
- Explicit pause/continue signaling
- Cleaner integration with orchestrator

**Store selection:** If the user names a store (a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on all openspec commands that read or write specs and changes (`list`, `status`, `instructions`, `validate`, `archive`, `doctor`). Treat `--store <id>` as sticky for the workflow. Without a store, commands act on the nearest local `openspec/` root.

**Input:** JSON with these fields (all optional):
```json
{
  "changeName": "pick-this-change",
  "baseBranch": "main",
  "deferred": ["skip-these"],
  "storeId": "my-store",
  "runState": { ... }
}
```

If no JSON input, start with full auto-detection.

## Steps

### 1. Parse Input

- Parse JSON if provided, otherwise use defaults
- Extract: `changeName`, `baseBranch`, `deferred`, `storeId`, `runState`

### 2. Detect Base Branch

If `baseBranch` provided, use it. Otherwise:

1. Check current branch: `git branch --show-current`
2. If starts with `change/`: derive parent via `git branch --merged <current> | grep -v <current> | head -1`
   - Confirm with user if not already confirmed in `runState`
3. Else if detached HEAD: use local counterpart of `git symbolic-ref refs/remotes/origin/HEAD`
   - Confirm with user
4. Else: use current branch

**Announce**: "Base branch: <base-branch>"

### 3. Working Tree Check

```bash
git status --porcelain
```

- **Clean**: Continue
- **Dirty** AND branch switch needed: Ask user: "Dirty working tree. How to resolve before switching branches? (commit/stash/discard)"
  - Execute the chosen action
  - **Never switch branches with uncommitted work whose fate the user has not chosen**

### 4. Triage: Audit Pending Changes

**Never silently archive, implement, or skip a flagged change.**

#### 4.1 Inventory

```bash
openspec list --json
```

For each non-archived change NOT in the `deferred` input list:
- Run `openspec status --change "<name>" --json`
- Read `tasks.md` (and `proposal.md`/`design.md` when present)

#### 4.2 Flag Changes

Categorize each change:

**Category: No tasks** (`totalTasks: 0`, status `no-tasks`)
- Nothing to implement
- Needs flesh-out or archiving

**Category: Incomplete planning**
- Any planning artifact not `done`/`skipped` (from status JSON)
- `tasks.md` references behavior not described in specs/design
- Tasks with no verifiable outcome

**Category: Stale / drifted**
- Change was last modified before commits landed on files it touches
- Run `git log --oneline -- <files named in the change's tasks/design>`
- Compare against the change's `lastModified` (from `openspec list --json`)
- Also run `openspec doctor --json` and investigate any issues

#### 4.3 Prompt User per Flagged Change

For each flagged change, present:
- Change name
- Category
- Evidence (why it was flagged)

Offer options:
- **Flesh out now** — Plan or refresh the change before selecting (use `openspec-update-change` or `openspec-propose`)
- **Defer** — Exclude from this run; will be reported in outcome
- **Archive as obsolete** — Only when genuinely stale or irrelevant; use `openspec-archive-change`

**Record the user's decision** for each flagged change.

**Do not** implement, skip, or archive a flagged change without explicit user answer.

### 5. Determine Active Change

Precedence chain (first match wins):

1. **Explicit input** — `changeName` passed in invocation
   - If not in `openspec list --json`: Report and ask

2. **Branch-derived** — Current branch is `change/<name>`
   - That change is active

3. **Single in-progress change** — Exactly one change in `openspec list --json` has status `in-progress`

4. **None** — Skip to scoring (step 6)

For the active change:
- If current branch matches `change/<name>`: Continue in place (resume)
- Else if `change/<name>` exists: `git switch change/<name>` (resume)
- Else: Will branch it fresh from base (step 7)

**Re-verify** the active change passes triage (if it was flagged, go back to step 4 prompt instead of resuming silently).

### 6. Auto-Defer External Resource Changes

Never select autonomously any change that requires:
- External resources (AWS, secrets, credentials, infrastructure)
- An unresolved human decision

**Auto-defer** these changes and report them with their reason.

### 7. Score Candidates

When there is no active change, score all candidates (non-archived, non-deferred, unflagged):

For each candidate:
- Read `proposal.md`, `design.md`, `tasks.md`
- Note `completedTasks`/`totalTasks`, touched files, whether foundational

**Scoring criteria (pay-off-first, first discriminator that separates decides)**:

1. **Foundational / unblocks others**
   - Changes that add/modify specs, schemas, or shared infrastructure
   - Changes that other pending changes build on
   - Completion unlocks other candidates

2. **Closest to done**
   - Highest `completedTasks / totalTasks` ratio

3. **Least merge friction**
   - Tasks touch files no other pending change touches
   - Compare file paths named in each change's tasks/docs

4. **Least recently touched**
   - Oldest `lastModified` timestamp

**Pick the winner** and state the evidence for the discriminator that decided it.

**Re-verify freshness** before branching: if a merge earlier in the run touched files the candidate references (git log vs `lastModified`), return it to the triage prompt instead of proceeding.

**If zero-task changes** somehow reach scoring: Apply the same triage prompt instead of picking it.

### 8. Branch

For the selected change:
- If `change/<name>` branch exists: `git switch change/<name>` (resume)
- Else: `git switch -c change/<name> <base-branch>`

Announce: "Using change: <name> on branch change/<name>, based on <base-branch>."

### 9. Return Structured Result

```json
{
  "changeName": "<selected-change>",
  "baseBranch": "<base-branch>",
  "branch": "change/<name>",
  "reason": "resumed" | "explicit" | "scored",
  "resumed": true | false,
  "triageOutcome": {
    "flagged": [
      {
        "name": "<change>",
        "category": "no-tasks" | "incomplete-planning" | "stale-drifted",
        "evidence": "<why>",
        "userDecision": "flesh-out" | "defer" | "archive" | null
      }
    ],
    "deferred": ["<change-names>"],
    "toFleshOut": ["<change-names>"],
    "toArchive": ["<change-names>"],
    "autoDeferred": [
      {
        "name": "<change>",
        "reason": "external-resources" | "human-decision",
        "details": "<why>"
      }
    ]
  },
  "scoring": {
    "candidates": ["<names>"],
    "winner": "<name>",
    "discriminator": "foundational" | "closest-to-done" | "least-friction" | "oldest",
    "evidence": "<why-this-won>"
  },
  "needsBranch": false,
  "status": "selected" | "no-candidates",
  "error": null | { ... }
}
```

If no candidates:
```json
{
  "status": "no-candidates",
  "triageOutcome": { ... },
  "message": "No candidates remain after triage and filtering"
}
```

## Guardrails

- **Selection only**: Never implement, archive, sync, or merge — those are other skills' jobs
- **Never pick flagged change** without user's explicit choice; show per-change evidence
- **Resume, don't recreate**: Existing `change/<name>` branch or `- [x]` tasks are progress
- **Reconcile working tree** before switching branches
- **Deferred and auto-deferred** changes are reported, never silently dropped
- **External-resource changes** are auto-deferred and reported, never selected autonomously
- **Triage evidence** is shown per change (category + why), not batch-flagged

## Input/Output Contract

### Input
```json
{
  "changeName": "string",           // Optional: explicit change to select
  "baseBranch": "string",           // Optional: override base detection
  "deferred": ["string"],           // Optional: changes to skip
  "storeId": "string",              // Optional: OpenSpec store ID
  "runState": {}                    // Optional: current run state
}
```

### Output
Always returns JSON:
```json
{
  "changeName": "string" or null,
  "baseBranch": "string",
  "branch": "string",
  "reason": "resumed" | "explicit" | "scored" | null,
  "resumed": boolean,
  "triageOutcome": {
    "flagged": [],
    "deferred": ["string"],
    "toFleshOut": ["string"],
    "toArchive": ["string"],
    "autoDeferred": [
      {
        "name": "string",
        "reason": "string",
        "details": "string"
      }
    ]
  },
  "scoring": {
    "candidates": ["string"],
    "winner": "string",
    "discriminator": "string",
    "evidence": "string"
  },
  "needsBranch": boolean,
  "status": "selected" | "no-candidates",
  "error": null | { ... }
}
```

## Error Codes

- `no-non-deferred-changes` — All changes were deferred
- `change-not-found` — Explicit change name doesn't exist
- `cannot-switch-branch` — Could not switch to the change branch
- `triage-conflict` — User decisions conflict with auto-deferrals

## Example Invocations

```
# Auto mode
/openspec-x-tdd-select-next-spec

# With deferred changes
/openspec-x-tdd-select-next-spec {"deferred": ["aws-setup", "secrets"]}

# Pick specific change
/openspec-x-tdd-select-next-spec {"changeName": "add-auth"}

# With run state
/openspec-x-tdd-select-next-spec {"runState": {...}}
```

## Compatibility

- Works with `openspec` CLI 1.x
- Requires git 2.x+
- Designed for use with `openspec-x-tdd-apply-all` orchestrator
- Can also be used standalone

## Version History

- **2.0.0**: Structured I/O, explicit triage outcomes, improved auto-defer
- **1.0.0**: Initial version (as openspec-x-tdd-select-next-spec)
