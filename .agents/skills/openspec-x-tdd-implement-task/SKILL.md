---
name: openspec-x-tdd-implement-task
description: Implement one OpenSpec task test-first with small green commits, verify with openspec-x-verify-implementation-phrase, then mark complete. Returns a structured result. Use when invoked by openspec-x-tdd-implement-spec or standalone.
allowed-tools: Bash(openspec:*), Bash(git:*)
license: MIT
compatibility: Requires openspec CLI and git.
metadata:
  author: project
  version: "2.0.0"
---

Implement a single OpenSpec task test-first, committing small green WIP advancements, then perform a thorough independent review (including `openspec-x-verify-implementation-phrase`), and finally mark the task complete. **Returns a structured JSON result** that the caller can use for control flow.

This is an improved version of `openspec-x-tdd-implement-task` with:
- Structured input/output contracts
- Better pause/continue signaling
- Explicit verification integration
- Cleaner separation from orchestrator concerns

**Store selection:** If the user names a store (a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on all openspec commands. Treat `--store <id>` as sticky for the workflow. Without a store, commands act on the nearest local `openspec/` root.

**Input:** JSON with these fields:
```json
{
  "changeName": "the-change-name",
  "taskIdentifier": "2.1", or task text to match,
  "baseBranch": "main",
  "storeId": "optional-store-id",
  "pushPreAuthorized": false,
  "config": { ... }  // Optional project-specific config
}
```

If no JSON input, fall back to: change from current branch (`change/<name>`), first pending task, with user confirmation.

## Steps

### 1. Parse Input and Load Context

- Parse JSON input if provided, otherwise infer from context
- Run `openspec instructions apply --change "<name>" --json` (with `--store <id>` if applicable)
- Read **every** file in `contextFiles` fresh from disk (proposal, specs, design, tasks)
- Extract the target task from `tasks.md` matching the identifier or text
- **If task not found**: return error with code `task-not-found`
- **If task already complete** (`- [x]`): return success with empty commits

### 2. Announce Task

Display:
```
==> Implementing Task: <task-id> - <task-description>
    Change: <change-name>
    Branch: <current-branch>
    Base: <base-branch>
```

### 3. Derive Expected Outcome and THE_PHRASE

From the task text plus the change's spec and design, derive:
- **Expected outcome**: What behavior or artifact change this task produces
- **How to verify it**: The verification method
- **THE_PHRASE**: The phrase-definition for verification, in order:
  1. If task text or spec names a spec anchor (e.g., "spec: <requirement>"): use that requirement's statement
  2. Else if task maps to a delta spec scenario: use that scenario's statement
  3. Else: use the task's own text

**Check**: If outcome cannot be derived, pause with `user-input-required` and ask for clarification.

### 4. TDD Red Phase (Code Tasks Only)

**For code tasks**:
- Write the failing test first (unit/integration test)
- A compile error because the API does not exist yet **counts as red**
- Confirm red by running the new test scoped to it
- If the test passes immediately (feature already exists): investigate and report

**For doc/spec/tooling tasks**:
- Skip red phase — the artifact itself is the deliverable
- Note this in the commit message

**Pause conditions**:
- Test environment not available
- Cannot determine how to test the task
- Task requires external resources not configured

### 5. Green WIP Implementation — Small Commits, Green-Only

Implement in small, coherent advancements following these rules:

1. **Before each commit**:
   - The project must compile (for code tasks)
   - The new test must pass (if it exists)
   - Scoped tests around the change must pass
   - **Red states are observed, never committed**

2. **Commit each advancement**:
   - Focused, conventional commit message
   - Include task identifier
   - Match the repo's commit convention (including footer)
   - **Never bundle unrelated changes**

3. **Review each commit**:
   - Review `git diff --cached` with fresh eyes before committing
   - Verify the commit does one thing well

4. **After each commit**:
   - Run the task's test (if applicable)
   - Verify green

**If any commit fails gates**: Fix immediately with another green commit.

### 6. Thorough Independent Review — Once, On Accumulated Diff

Before marking complete, perform a comprehensive review:

1. **Re-read fresh**: The task, THE_PHRASE, and relevant spec/design (not from memory)

2. **Review the whole task diff**:
   ```bash
   git diff <base-branch>...<current-branch> -- <task-related-files>
   ```
   - Does it do **exactly** what the task requires?
   - Any **gaps** (missing behavior)?
   - Any **overlaps** (unrelated or duplicated code)?

3. **Invoke verification**: Load `openspec-x-verify-implementation-phrase` with THE_PHRASE
   - Pass THE_PHRASE as a fenced block or delimited text
   - **Wait for and capture the full verdict**
   
4. **Act on verdict**:
   - `contradicted` or `not-implemented` clauses the task requires → **Pause** with `verify-contradiction`, fix with further green commits, re-verify
   - `gaps` or `overlaps` flagged → Address them before proceeding
   - `aligned` or `mostly-aligned-with-noted-deviations` with only benign deviations → Proceed
   - Any `unverified` finding → Mark as unverified, do not complete

5. **Document findings**: Note any deviations or assumptions in the commit or task notes

**Never mark complete on unresolved or unverified findings.**

### 7. Gates — Full Verification

Run the complete gate set adapted to the project:

```bash
# 1. Build with warnings-as-errors
{{BUILD_COMMAND}}

# 2. Full test run with coverage
{{TEST_COMMAND}}

# 3. Coverage ratchet (if project has one)
{{COVERAGE_COMMAND}}

# 4. Spec discipline
openspec validate --all

# 5. E2E/smoke suites (when change touches API contract)
{{E2E_COMMAND}}
```

**If any gate fails**: Fix with green commits and re-run all gates.

**Project adaptation**: Use config or detect project type to set actual commands.

### 8. Docs Update

Update documentation as the task requires:
- `README.md` — overall project changes
- `docs/**` — detailed documentation
- `docs/toc.yml` or index — when pages added/moved/removed
- XML comments — on classes/methods per project standards
- OpenAPI metadata — when APIs changed

Follow the project's docs conventions.

### 9. Mark Complete

- Flip `- [ ]` → `- [x]` in `tasks.md` for this task
- Fold the flip into the task's final commit (the last WIP commit carries it)
- If final state already committed, make one small final commit for the flip

**A task is complete only when**:
- Its specified behavior is fully implemented
- Verified through independent review
- All gates pass
- Documentation updated
- **Never when partially done or deferred**

### 10. Return Structured Result

Return JSON result:
```json
{
  "taskId": "<task-id>",
  "taskDescription": "<description>",
  "status": "completed",
  "commits": ["<sha1>", "<sha2>"],
  "verifyVerdict": "aligned",
  "gatesPassed": true,
  "docsUpdated": true,
  "pauseReason": null,
  "error": null
}
```

If paused:
```json
{
  "taskId": "<task-id>",
  "status": "paused",
  "pauseReason": {
    "type": "verify-contradiction",
    "clause": "<the-contradicted-clause>",
    "evidence": "<what-contradicts>"
  },
  "commits": ["<sha1>"],
  "error": null
}
```

If failed:
```json
{
  "taskId": "<task-id>",
  "status": "failed",
  "error": {
    "code": "gates-failed",
    "message": "Build failed",
    "details": "...",
    "recoverable": true
  },
  "commits": ["<sha1>"],
  "pauseReason": null
}
```

## Pause Rule (Strict)

**Pause immediately and return pauseReason** when:
- Task is ambiguous or unclear
- Implementation reveals a design issue or scope beyond the task's spec
- A blocker or error occurs
- The verify verdict is `contradicted` and cannot be reconciled
- External resources needed (secrets, AWS, infrastructure)
- User interrupts or asks for clarification

**Do not**:
- Guess at unclear requirements
- Silently narrow, defer, or simplify away specified behavior
- Continue on a contradiction
- Absorb scope growth without user approval

## Guardrails

- **Never mark `- [ ]` → `- [x]`** until independent review, verify-phrase verdict, and gates pass
- **Green-only commits**: Red states are observed, never committed
- **Never push** during a task — only the orchestrator pushes
- **Keep commits small, scoped, per-advancement** — a commit must not bundle unrelated changes
- **The verify skill is read-only** — it never edits; you do the fixing
- **Ground every review finding** in evidence (file + line, or verbatim quote)
- **Doc/spec/tooling tasks have no red phase** — their deliverable is the artifact itself
- **Never copy context or operation guidance** into implementation files or planning artifacts

## Input/Output Contract

### Input
Accepts JSON with these fields (all optional, will prompt if missing):
```json
{
  "changeName": "string",           // Change to work on
  "taskIdentifier": "string",      // Task number or text (e.g., "2.1", "Add auth middleware")
  "baseBranch": "string",           // Base branch (default: auto-detect)
  "storeId": "string",              // OpenSpec store ID
  "config": {},                     // Project-specific configuration
  "dryRun": boolean                // If true, report what would happen without changes
}
```

### Output
Always returns JSON with this structure:
```json
{
  "status": "completed" | "paused" | "failed" | "skipped",
  "taskId": "string",
  "taskDescription": "string",
  "changeName": "string",
  "commits": ["string"],            // Array of commit SHAs
  "verifyVerdict": "string",        // From verify-phrase skill
  "gatesPassed": boolean,
  "docsUpdated": boolean,
  "pauseReason": null | {           // Only if status is "paused"
    "type": "string",
    "prompt": "string",              // For user-input-required
    "details": "string",             // For ambiguity, scope-growth
    "error": "string",               // For blocker
    "clause": "string",              // For verify-contradiction
    "evidence": "string"
  },
  "error": null | {                // Only if status is "failed"
    "code": "string",
    "message": "string",
    "details": "string",
    "recoverable": boolean
  },
  "startTime": "ISO8601",
  "endTime": "ISO8601"
}
```

## Error Codes

Uses error codes from `openspec-x-tdd-shared`:
- `task-not-found` — Task identifier doesn't match any pending task
- `no-pending-tasks` — All tasks already complete
- `incomplete-planning` — Planning artifacts not done
- `test-failed` — Cannot get to red or green state
- `build-failed` — Build errors
- `gates-failed` — Any gate fails
- `verify-failed` — Verification found contradictions
- `ambiguity` — Task requirements unclear
- `blocker` — External dependency or blocker

## Example Invocations

```
/openspec-x-tdd-implement-task {"changeName": "add-auth", "taskIdentifier": "2.1"}

/openspec-x-tdd-implement-task {"changeName": "add-auth", "taskIdentifier": "Implement JWT validation"}

/openspec-x-tdd-implement-task
```

## Compatibility

- Works with `openspec` CLI 1.x
- Requires git 2.x+
- Designed for use with `openspec-x-tdd-implement-spec` orchestrator
- Can also be used standalone

## Version History

- **2.0.0**: Structured I/O, explicit verification, improved pause handling
- **1.0.0**: Initial version (as openspec-x-tdd-implement-task)
