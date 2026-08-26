---
name: openspec-x-tdd-shared
description: Shared utilities and contracts for the openspec-x-tdd skill family. Do not invoke directly; other TDD skills import from here. Defines common state structures, error codes, and utility functions used across all automated TDD workflows.
allowed-tools: Bash(openspec:*), Bash(git:*)
license: MIT
compatibility: Requires openspec CLI and git.
metadata:
  author: project
  version: "1.0.0"
---

# OpenSpec TDD Shared Contracts and Utilities

**This is a library skill.** Do not invoke it directly. Other skills in the `openspec-x-tdd-*` family import and use the definitions here.

## Purpose

Provide a single source of truth for:
- Common state structures passed between TDD skills
- Error codes and pause signals
- Utility functions (base branch detection, working tree reconciliation)
- Guardrails that all TDD skills must enforce

This ensures consistency and reduces duplication across the skill family.

---

## State Structures

### RunState

The complete state of a TDD workflow run. Passed as JSON between skills.

```typescript
interface RunState {
  // Identification
  runId: string;              // UUID for this run
  
  // Environment
  baseBranch: string;        // Detected base branch (e.g., "main", "master", "develop")
  storeId?: string;          // OpenSpec store ID if using a registered store
  repoRoot: string;          // Absolute path to the repo root
  
  // Progress tracking
  changesProcessed: string[]; // Names of changes already processed in this run
  changesDeferred: string[];  // Names of changes deferred by user
  changesArchived: string[];  // Names of changes archived in this run
  
  // Authorization
  pushPreAuthorized: boolean; // true if user pre-authorized pushes for this run
  remoteTarget?: string;      // The remote branch to push to (defaults to baseBranch)
  
  // Current context
  currentChange?: string;     // The change being worked on
  currentBranch?: string;     // The current git branch
  
  // Error/Control flow
  pauseReason?: PauseReason;  // If set, the run is paused
  lastError?: WorkflowError; // Last error encountered
}
```

### PauseReason

Why a skill paused execution.

```typescript
type PauseReason = 
  | { type: "user-input-required", prompt: string }
  | { type: "ambiguity", details: string }
  | { type: "blocker", error: string }
  | { type: "scope-growth", details: string }
  | { type: "verify-contradiction", clause: string, evidence: string }
  | { type: "conflict", file: string, details: string };
```

### WorkflowError

Structured error information.

```typescript
interface WorkflowError {
  code: ErrorCode;
  message: string;
  details?: string;
  recoverable: boolean;
}
```

### ErrorCode

Standard error codes across all TDD skills.

```typescript
type ErrorCode =
  // Preflight errors
  | "no-openspec-root"
  | "no-changes-pending"
  | "cannot-detect-base-branch"
  | "dirty-working-tree"
  | "unresolved-conflicts"
  
  // Change selection errors
  | "no-candidate-changes"
  | "change-not-found"
  | "change-already-archived"
  | "incomplete-planning"
  
  // Task implementation errors
  | "no-pending-tasks"
  | "task-not-found"
  | "test-failed"
  | "build-failed"
  | "gates-failed"
  | "verify-failed"
  
  // Archive/merge errors
  | "archive-failed"
  | "merge-conflict"
  | "push-failed"
  | "sync-failed"
  
  // Sub-skill errors
  | "subskill-paused"
  | "subskill-failed"
  | "subskill-error";
```

### TaskResult

Result of implementing a single task.

```typescript
interface TaskResult {
  taskId: string;
  taskDescription: string;
  status: "completed" | "skipped" | "failed" | "paused";
  commits: string[];          // Commit SHAs produced
  verifyVerdict?: string;     // From openspec-x-verify-implementation-phrase
  gatesPassed: boolean;
  error?: WorkflowError;
  pauseReason?: PauseReason;
}
```

### ChangeResult

Result of implementing a complete change.

```typescript
interface ChangeResult {
  changeName: string;
  tasks: TaskResult[];
  status: "completed" | "partial" | "failed" | "paused";
  archived: boolean;
  archivePath?: string;
  merged: boolean;
  pushed: boolean;
  branch?: string;
  errors: WorkflowError[];
}
```

---

## Utility Functions

### detectBaseBranch(repoRoot: string, currentBranch?: string): BaseBranchResult

Detects the base branch for this workflow run.

**Algorithm:**
1. If `currentBranch` starts with `change/`, find its parent branch
2. If on detached HEAD, use the local counterpart of `origin/HEAD`
3. Otherwise, use the current branch
4. Confirm with user if derived (not explicit)

**Returns:**
```typescript
interface BaseBranchResult {
  baseBranch: string;
  derived: boolean;  // true if we had to derive it
  confirmed: boolean; // true if user confirmed
}
```

### reconcileWorkingTree(repoRoot: string): WorkingTreeResult

Handles dirty working tree before branching.

**Returns:**
```typescript
type WorkingTreeAction = "clean" | "commit" | "stash" | "discard";

interface WorkingTreeResult {
  action: WorkingTreeAction;
  files: string[];           // List of dirty files
  commitHash?: string;      // If action was "commit"
  stashIndex?: number;      // If action was "stash"
}
```

### selectNextChange(state: RunState): ChangeSelection

Selects the next change to process based on triage and scoring.

**Returns:**
```typescript
interface ChangeSelection {
  changeName: string;
  reason: "resumed" | "explicit" | "scored";
  triageOutcome: TriageOutcome;
  needsBranch: boolean;
}

interface TriageOutcome {
  flagged: FlaggedChange[];
  deferred: string[];
  toFleshOut: string[];
  toArchive: string[];
}

interface FlaggedChange {
  name: string;
  category: "no-tasks" | "incomplete-planning" | "stale-drifted";
  evidence: string;
  userDecision?: "flesh-out" | "defer" | "archive";
}
```

---

## Guardrails (All TDD Skills Must Enforce)

1. **Never push without authorization**: Push only when `pushPreAuthorized` is true OR explicitly confirmed
2. **Never force-push**: Always use regular push; never `--force` or `--force-with-lease`
3. **Never implement incomplete planning**: If `isPlanningComplete: false`, route to planning first
4. **Never skip verification**: Every task must pass verification before completion
5. **Never bundle unrelated changes**: Commits must be focused and scoped to the task
6. **Never hand-edit change directories**: Always use `openspec` CLI for change operations
7. **Never archive with incomplete artifacts**: Check artifacts and tasks before archiving
8. **Never continue on pause**: If a sub-skill returns a pause, propagate it up immediately
9. **Always use change/ prefix**: Spec branches must be named `change/<name>`
10. **Always verify freshness**: Check if files changed since the change was last modified

---

## Shared Commands

### Gate Commands

Standard gate commands that all projects should adapt:

```bash
# Build with warnings-as-errors
{{BUILD_COMMAND}}

# Full test run with coverage
{{TEST_COMMAND}}

# Coverage ratchet
{{COVERAGE_COMMAND}}

# Spec validation
openspec validate --all

# E2E/smoke tests (when contract touched)
{{E2E_COMMAND}}
```

### Git Operations

```bash
# Check current branch
git branch --show-current

# List ancestor branches
git branch --merged <branch>

# Check working tree status
git status --porcelain

# Fetch from origin
git fetch origin

# Switch to branch
git switch <branch>

# Create new branch
git switch -c <branch> <start-point>

# Merge branch
git merge --no-ff <branch>

# Rebase branch
git rebase <base-branch>

# Push
git push origin <branch>

# Delete branch
git branch -d <branch>
```

---

## Project-Specific Configuration

Each project using these skills should provide a `.openspec-tdd-config.json`:

```json
{
  "buildCommand": "dotnet build MySolution.slnx",
  "testCommand": "dotnet test MySolution.slnx --collect:\"XPlat Code Coverage\"",
  "coverageCommand": "bash scripts/check-coverage.sh",
  "e2eCommand": "dotnet test tests/E2E/MySolution.E2E.Tests.csproj",
  "docsConvention": {
    "readmePath": "README.md",
    "docsPath": "docs/",
    "tocPath": "docs/toc.yml"
  },
  "branchPrefix": "change/",
  "remote": "origin"
}
```

---

## Conventions

### Branch Naming
- All spec branches: `change/<change-name>`
- Base branch: typically `main`, `master`, or `develop`
- Never use bare change names as branches

### Commit Messages
Follow the project's convention, typically:
```
<type>(<scope>): <subject>

<body>

<footer>
```

For TDD tasks, include the task identifier in the subject.

### Task Checkbox Convention
- Pending: `- [ ] Task description`
- Complete: `- [x] Task description`
- Never use other markers

### Verification Phrases
- Extract THE_PHRASE from task text or spec anchors
- Use `openspec-x-verify-implementation-phrase` for verification
- Verdicts: `aligned`, `mostly-aligned-with-noted-deviations`, `contradicted`, `not-implemented`

---

## Version History

- **1.0.0**: Initial shared contracts definition
