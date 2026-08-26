---
name: openspec-x-tdd-apply-all
description: Drive every pending OpenSpec change to completion in one pass — orchestrating openspec-x-tdd-select-next-spec (triage, selection, branching) and openspec-x-tdd-implement-spec (test-first implementation, archive, merge, push) until none remain. Returns structured summary.
allowed-tools: Bash(openspec:*), Bash(git:*)
license: MIT
compatibility: Requires openspec CLI and git.
metadata:
  author: project
  version: "2.0.0"
---

Drive every pending OpenSpec change to completion, one change per branch, until none remain. This is the **orchestrator** for the `openspec-x-tdd-*` family. It manages the end-to-end workflow and coordinates between the specialized skills.

This is an improved version of `openspec-x-tdd-apply-all` with:
- Structured state management across the entire run
- Better error and pause propagation
- Explicit contracts with sub-skills
- Comprehensive summary reporting

**Store selection:** If the user names a store (a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on all openspec commands that read or write specs and changes (`list`, `status`, `instructions`, `validate`, `archive`). Treat `--store <id>` as sticky for the rest of the run. Without a store, commands act on the nearest local `openspec/` root.

**Input:** JSON with these fields (all optional):
```json
{
  "changeName": "start-with-this-change",
  "baseBranch": "main",
  "storeId": "my-store",
  "deferred": ["change-to-skip"],
  "config": { ... },
  "dryRun": true
}
```

If no JSON input, start with full auto-detection and prompts.

## Overview

The workflow has three phases:

1. **Preflight** — Detect environment, confirm authorizations (once)
2. **Main Loop** — For each change: select → implement → archive → merge → push
3. **Summary** — Report what happened to every change

Each phase has explicit contracts with the next, and errors/pauses propagate upward immediately.

---

## Phase 1: Preflight (Once per Run)

### Step 1.1: Generate Run ID

Create a unique run identifier:
```bash
# Generate UUID for this run
date +%s-%N | sha256sum | head -c 16
```

### Step 1.2: Detect Repository Root

```bash
# Find the repo root (has .git/ or is a git worktree)
git rev-parse --show-toplevel
```

### Step 1.3: Detect Base Branch

**Algorithm:**
1. Check current branch: `git branch --show-current`
2. If starts with `change/`: this is a resume
   - Find parent branch: `git branch --merged <current> | grep -v <current> | head -1`
   - Confirm with user: "Resuming on base branch <parent>?"
3. Else if detached HEAD: use local counterpart of `git symbolic-ref refs/remotes/origin/HEAD`
   - Confirm with user
4. Else: use current branch as base

**Announce**: "Base branch: <base-branch>"

### Step 1.4: Store Detection

If `--store <id>` passed, use it. Otherwise:
```bash
openspec store list --json
```
If exactly one store and it's not the local `openspec/`, ask user to confirm or specify.

### Step 1.5: Confirm Push Authorization

**This is a one-time authorization for the entire run.**

Ask: "This run will push to <remote>/<base-branch> after each change. Confirm push authorization for this run? (yes/no)"

- If **yes**: Set `pushPreAuthorized: true`, `remoteTarget: <base-branch>` (or user-specified)
- If **no**: Set `pushPreAuthorized: false`, will ask before each push

### Step 1.6: Reconcile Working Tree

```bash
git status --porcelain
```

- **Clean**: Proceed
- **Dirty**: List files, ask user: "Dirty working tree. How to resolve? (commit/stash/discard)"
  - **commit**: Add and commit on current branch (or resumed change branch)
  - **stash**: `git stash push -m "WIP before TDD run"`
  - **discard**: `git restore .`

### Step 1.7: Initialize Run State

Create the initial `RunState`:
```json
{
  "runId": "<uuid>",
  "baseBranch": "<base>",
  "storeId": "<store>" or null,
  "repoRoot": "<path>",
  "changesProcessed": [],
  "changesDeferred": ["..."],  // From input or empty
  "changesArchived": [],
  "pushPreAuthorized": true/false,
  "remoteTarget": "<branch>",
  "currentChange": null,
  "currentBranch": "<current-branch>",
  "pauseReason": null,
  "lastError": null
}
```

---

## Phase 2: Main Loop

**While** `openspec list --json` returns non-archived changes NOT in `changesDeferred`:

### Step 2.1: Select Next Change

Invoke `openspec-x-tdd-select-next-spec` with:
```json
{
  "baseBranch": "<base-branch>",
  "deferred": <changesDeferred>,
  "storeId": "<store-id>",
  "runState": <current-run-state>
}
```

**Process result**:
- **changeName**: The selected change
- **triageOutcome**: Updates to `changesDeferred`, `changesToFleshOut`, `changesToArchive`
- **needsBranch**: Whether we need to create a branch

**Update run state**:
- Add to `changesDeferred` as reported
- Remove from `changesDeferred` any that were fleshed out
- Track `changesToArchive` separately

**If no candidates remain**: Exit with summary

**If user defers all changes**: Exit with summary showing all deferred

### Step 2.2: Implement the Change

Invoke `openspec-x-tdd-implement-spec` with:
```json
{
  "changeName": "<selected-change>",
  "baseBranch": "<base-branch>",
  "storeId": "<store-id>",
  "pushPreAuthorized": <pushPreAuthorized>,
  "config": <config>,
  "runState": <current-run-state>
}
```

**Process result**:

1. **status: "completed"**
   - Add to `changesProcessed`
   - If `archived: true`: Add to `changesArchived`
   - If `merged: true` and `pushed: true`: Record success
   - Continue to next iteration

2. **status: "paused"**
   - **Immediately stop the entire run**
   - Set `runState.pauseReason` = result's `pauseReason`
   - Return to user with pause context
   - **Do not continue the loop**

3. **status: "failed"**
   - **Immediately stop the entire run**
   - Set `runState.lastError` = result's `error`
   - Return to user with error context
   - **Do not continue the loop**

4. **status: "partial"**
   - Record partial progress
   - **Stop the run** (partial completion means something went wrong)
   - Return to user

### Step 2.3: Update State and Loop

After successful completion:
- Re-run `openspec list --json` to get fresh state
- Continue loop

---

## Phase 3: Summary

When loop exits (no more candidates or pause/error):

### Step 3.1: Generate Summary

For every change that was in `openspec list --json` at the start:

**Categorize**:
- **Implemented + Merged + Pushed**: changes in `changesProcessed` that completed fully
- **Implemented + Archived**: changes that were completed and archived
- **Fleshed out at triage**: changes from `triageOutcome.toFleshOut`
- **Deferred**: changes in `changesDeferred`
- **Archived as obsolete**: changes from `triageOutcome.toArchive`
- **Failed**: changes where implementation failed
- **Paused**: the change where we stopped (if applicable)

### Step 3.2: Display Summary

```markdown
## TDD Apply-All Run Summary

**Run ID:** <run-id>
**Base Branch:** <base-branch>
**Start Time:** <start-time>
**End Time:** <end-time>

### Completed (Implemented, Archived, Merged, Pushed)
- [x] change-1
- [x] change-2

### Fleshed Out at Triage
- [ ] change-3 (needed planning completion)

### Deferred
- [ ] change-4 (external resources needed)
- [ ] change-5 (user deferred)

### Archived as Obsolete
- [ ] change-6 (stale)

### Failed
- [ ] change-7 (error: <error-message>)

### Paused
- [ ] change-8 (reason: <pause-reason>)

### Statistics
- Total changes at start: N
- Completed: X
- Deferred: Y
- Failed: Z
```

### Step 3.3: Return Structured Result

```json
{
  "runId": "<uuid>",
  "status": "completed" | "paused" | "failed",
  "baseBranch": "<branch>",
  "summary": {
    "totalChanges": 10,
    "completed": ["change-1", "change-2"],
    "fleshedOut": ["change-3"],
    "deferred": ["change-4", "change-5"],
    "archivedAsObsolete": ["change-6"],
    "failed": ["change-7"],
    "paused": "change-8" or null
  },
  "changes": {
    "change-1": {
      "status": "completed",
      "tasks": [...],
      "archived": true,
      "merged": true,
      "pushed": true
    },
    "change-8": {
      "status": "paused",
      "pauseReason": { ... },
      "tasksCompleted": 3,
      "totalTasks": 5
    }
  },
  "pauseReason": null | { ... },
  "error": null | { ... },
  "startTime": "<ISO8601>",
  "endTime": "<ISO8601>"
}
```

---

## Guardrails (Strictly Enforced)

1. **Never implement changes needing external resources** without explicit user go-ahead — select step auto-defers and reports them
2. **Never push without authorization** — confirmed once in preflight OR per-push; never assume
3. **Never force-push** — always use regular push
4. **Use openspec CLI for change metadata** — never hand-edit or hand-move change directories
5. **A task is done only when** `openspec-x-tdd-implement-task` marked it complete after verification
6. **Pause propagation** — if any sub-skill pauses, stop the whole loop immediately and surface the prompt
7. **Resume, don't recreate** — existing `change/<name>` branch or `- [x]` tasks are progress, not errors
8. **Loop exit condition** — machine-checked: no non-archived, non-deferred changes in `openspec list --json`
9. **Triage evidence** — shown per change (category + why); never batch-flag silently
10. **State integrity** — run state is never mutated except through explicit updates; always pass fresh state to sub-skills

---

## Input/Output Contract

### Input
```json
{
  "changeName": "string",           // Optional: change to start with
  "baseBranch": "string",           // Optional: override base detection
  "storeId": "string",              // Optional: OpenSpec store ID
  "deferred": ["string"],           // Optional: changes to skip
  "config": {},                     // Optional: project config
  "dryRun": boolean                // Optional: report without changes
}
```

### Output
Always returns JSON:
```json
{
  "runId": "string",
  "status": "completed" | "paused" | "failed",
  "baseBranch": "string",
  "storeId": "string" or null,
  "summary": {
    "totalChanges": 0,
    "completed": ["string"],
    "fleshedOut": ["string"],
    "deferred": ["string"],
    "archivedAsObsolete": ["string"],
    "failed": ["string"],
    "paused": "string" or null
  },
  "changes": {
    "string": { ... }  // Per-change details
  },
  "pauseReason": null | { ... },
  "error": null | { ... },
  "startTime": "ISO8601",
  "endTime": "ISO8601"
}
```

---

## Error Codes

- `no-openspec-root` — No OpenSpec root found
- `no-changes-pending` — No non-archived changes to process
- `cannot-detect-base-branch` — Could not determine base branch
- `dirty-working-tree` — Working tree had uncommitted changes (user chose discard)
- `subskill-paused` — A sub-skill paused
- `subskill-failed` — A sub-skill failed
- `push-not-authorized` — Push attempted without authorization

---

## Example Invocations

```
# Full auto mode
/openspec-x-tdd-apply-all

# Start with specific change
/openspec-x-tdd-apply-all {"changeName": "add-auth"}

# Skip some changes
/openspec-x-tdd-apply-all {"deferred": ["external-integration", "aws-setup"]}

# With explicit store
/openspec-x-tdd-apply-all {"storeId": "my-project-store"}

# Dry run (report only)
/openspec-x-tdd-apply-all {"dryRun": true}
```

---

## Compatibility

- Works with `openspec` CLI 1.x
- Requires git 2.x+
- Coordinates with `openspec-x-tdd-select-next-spec` and `openspec-x-tdd-implement-spec`

---

## Version History

- **2.0.0**: Structured state, explicit contracts, comprehensive summary, improved pause/propagation
- **1.0.0**: Initial version (as openspec-x-tdd-apply-all)
