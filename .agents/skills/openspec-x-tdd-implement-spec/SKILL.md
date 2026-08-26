---
name: openspec-x-tdd-implement-spec
description: Implement all pending tasks of one OpenSpec change test-first via openspec-x-tdd-implement-task, then archive, merge, and push. Returns structured result. Use when invoked by openspec-x-tdd-apply-all or standalone.
allowed-tools: Bash(openspec:*), Bash(git:*)
license: MIT
compatibility: Requires openspec CLI and git.
metadata:
  author: project
  version: "2.0.0"
---

Implement every pending task of one OpenSpec change test-first by delegating to `openspec-x-tdd-implement-task`, then finish the change (archive, merge, push). **Returns a structured JSON result** for orchestration.

This is an improved version of `openspec-x-tdd-implement-spec` with:
- Structured state passing with the orchestrator
- Better pause/continue propagation
- Explicit result contracts
- Cleaner error handling

**Store selection:** If the user names a store (a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on all openspec commands that read or write specs and changes. Treat `--store <id>` as sticky for the workflow. Without a store, commands act on the nearest local `openspec/` root.

**Input:** JSON with these fields:
```json
{
  "changeName": "the-change-name",
  "baseBranch": "main",
  "storeId": "optional-store-id",
  "pushPreAuthorized": true,
  "config": { ... },
  "runState": { ... }  // Optional: full run state from orchestrator
}
```

If no JSON input, fall back to: infer change from current branch (`change/<name>`), with user prompts for missing info.

## Steps

### 1. Parse Input and Resolve Change

- Parse JSON input if provided, otherwise infer from context
- Run `openspec list --json` / `openspec status --change "<name>" --json` (with `--store <id>`)
- **If change not found**: return error with code `change-not-found`
- **If already archived**: return error with code `change-already-archived`
- Announce: "Implementing change: <name>"

### 2. Planning Check

- Check `isPlanningComplete` from status JSON
- Check all required artifacts are `done` or `skipped`
- **If incomplete planning**: return error with code `incomplete-planning`, suggest using `openspec-propose` or `openspec-update-change`
- **Never implement from incomplete planning**

### 3. Branch Check and Setup

- Check current branch:
  - If on `change/<name>`: proceed in place (resume)
  - Else if `change/<name>` exists: `git switch change/<name>` (resume)
  - Else: derive base branch and create: `git switch -c change/<name> <base-branch>`
- Announce branch state

### 4. Per-Task Loop

List pending tasks via `openspec instructions apply --change "<name>" --json`:

```bash
# Get fresh task list each iteration
openspec instructions apply --change "<name>" --json
```

For each task still marked `- [ ]`:

1. **Invoke `openspec-x-tdd-implement-task`** for exactly that task:
   ```
   /openspec-x-tdd-implement-task {
     "changeName": "<name>",
     "taskIdentifier": "<task-id>",
     "baseBranch": "<base-branch>",
     "storeId": "<store-id>",
     "config": <config>
   }
   ```

2. **Process the result**:
   - **status: "completed"**: Continue to next task
   - **status: "paused"**: **Immediately stop**, propagate pauseReason to caller, do not continue
   - **status: "failed"**: **Immediately stop**, propagate error to caller, do not continue
   - **status: "skipped"**: Log and continue

3. **Re-check progress**: Re-read `tasks.md` to confirm the task was marked complete

4. **Pause rule**: If `openspec-x-tdd-implement-task` pauses or fails, **stop the whole loop immediately**, return the pause/error to the caller. Never guess or continue.

### 5. All Tasks Complete — Final Gates

When all tasks are `- [x]`:

1. **Re-run full gate set** once more:
   - Build with warnings-as-errors
   - Full test run with coverage
   - Coverage ratchet (if project has one)
   - Spec discipline: `openspec validate --all`
   - E2E/smoke suites when the change touches the API contract

2. **If any gate fails**: Report, do not proceed to archive

3. **Confirm docs alignment**: Verify `README.md` and `docs/**` reflect the change

### 6. Archive

Load the `openspec-archive-change` skill and follow it:

1. Run `openspec instructions archive --change "<name>" --json` for inputs
2. Check artifact/task completion
3. Assess delta-spec sync state:
   - If delta specs exist and need syncing: run inline `openspec-sync-specs`
   - Verify sync results before proceeding
4. Archive `openspec/changes/<name>` → `openspec/changes/archive/YYYY-MM-DD-<name>`

**Honor all archive prompts** — never hand-move or `rm` a change directory.

**If archive fails**: Return error, do not proceed to merge.

### 7. Merge, Push, Clean Up

1. **Refresh against base branch**:
   ```bash
   git fetch origin
   git switch <base-branch>
   git merge --ff-only origin/<base-branch>  # Only as far as user's state allows
   git switch change/<name>
   git rebase <base-branch>
   ```
   - Resolve any conflicts
   - Re-run gates if refresh changed anything

2. **Merge back into base branch**:
   ```bash
   git switch <base-branch>
   git merge --no-ff change/<name>
   ```

3. **Push** (if `pushPreAuthorized` is true OR user confirms):
   - **Confirm push** unless `pushPreAuthorized` is true
   - Push only when gates are green and working tree is clean
   - `git push origin <base-branch>`
   - **Never force-push**

4. **Delete the branch**:
   ```bash
   git branch -d change/<name>
   ```
   - Push deletion only if branch was pushed

### 8. Return Structured Result

Return JSON:
```json
{
  "changeName": "<name>",
  "status": "completed",
  "tasks": [
    {
      "taskId": "<id>",
      "status": "completed",
      "commits": ["<sha1>", ...]
    },
    ...
  ],
  "archived": true,
  "archivePath": "openspec/changes/archive/YYYY-MM-DD-<name>",
  "merged": true,
  "pushed": true,
  "branch": "change/<name>",
  "errors": [],
  "pauseReason": null,
  "gatesPassed": true
}
```

If paused:
```json
{
  "changeName": "<name>",
  "status": "paused",
  "tasks": [...],
  "pauseReason": { ... },
  "currentTask": "<task-id>"
}
```

If failed:
```json
{
  "changeName": "<name>",
  "status": "failed",
  "tasks": [...],
  "error": { ... }
}
```

## Guardrails

- **A task is done only when** `openspec-x-tdd-implement-task` marked it complete after verification
- **Never push without authorization**: Confirm unless `pushPreAuthorized` is true
- **Never force-push**: Always use regular push
- **Use `openspec-archive-change` for archiving**: Never hand-edit or hand-move change directories
- **Pause propagation**: If any sub-skill pauses, stop immediately and propagate the pause
- **Resume, don't recreate**: Existing `change/<name>` branch or `- [x]` tasks are progress, not errors
- **Never implement from incomplete planning**: Stop and route to planning first
- **Gates must pass**: Never archive or merge if gates fail

## Input/Output Contract

### Input
```json
{
  "changeName": "string",           // Required: change to implement
  "baseBranch": "string",           // Optional: defaults to auto-detect
  "storeId": "string",              // Optional: OpenSpec store ID
  "pushPreAuthorized": boolean,     // Optional: default false
  "config": {},                     // Optional: project-specific config
  "runState": {}                    // Optional: full run state for orchestrator
}
```

### Output
```json
{
  "changeName": "string",
  "status": "completed" | "partial" | "paused" | "failed",
  "tasks": [
    {
      "taskId": "string",
      "taskDescription": "string",
      "status": "completed" | "skipped" | "failed" | "paused",
      "commits": ["string"],
      "verifyVerdict": "string",
      "error": null | { ... }
    }
  ],
  "archived": boolean,
  "archivePath": "string",
  "merged": boolean,
  "pushed": boolean,
  "branch": "string",
  "errors": [],
  "pauseReason": null | { ... },
  "gatesPassed": boolean,
  "startTime": "ISO8601",
  "endTime": "ISO8601"
}
```

## Error Codes

- `change-not-found` — Change doesn't exist
- `change-already-archived` — Change was already archived
- `incomplete-planning` — Planning artifacts not complete
- `no-pending-tasks` — All tasks already complete
- `subskill-paused` — A sub-skill (implement-task) paused
- `subskill-failed` — A sub-skill failed
- `archive-failed` — Archiving failed
- `merge-conflict` — Merge had conflicts that couldn't be resolved
- `gates-failed` — Final gates failed

## Example Invocations

```
/openspec-x-tdd-implement-spec {"changeName": "add-auth", "pushPreAuthorized": true}

/openspec-x-tdd-implement-spec {"changeName": "add-auth", "baseBranch": "develop"}

/openspec-x-tdd-implement-spec
```

## Compatibility

- Works with `openspec` CLI 1.x
- Requires git 2.x+
- Designed for use with `openspec-x-tdd-apply-all` orchestrator
- Can also be used standalone

## Version History

- **2.0.0**: Structured I/O, explicit result contracts, improved pause handling
- **1.0.0**: Initial version (as openspec-x-tdd-implement-spec)
