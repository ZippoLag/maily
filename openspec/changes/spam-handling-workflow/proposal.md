## Why

The original project spec (`maily.md`) explicitly requires spam handling workflows including: listing new spam emails, user confirmation for deletion/not-spam, creating Gmail filter rules, and moving emails between spam/inbox. This feature was **not included in v1 foundation** which focused on read-only operations.

This change **captures the requirement** but explicitly **defers implementation** until the core read-only triage workflow (static-analysis-category-learning, TUI improvements) is complete. This ensures we have a solid foundation before adding mutation operations.

## What Changes

- **New**: Spam folder scanning and listing
- **New**: User confirmation interface for spam handling
- **New**: Gmail filter rule creation (requires Gmail API mutations)
- **New**: Email movement between spam and inbox
- **New**: Inbox spam detection workflow

**BREAKING**: This change requires Gmail API write scopes, which is a significant architectural change from the current read-only design.

## Capabilities

### New Capabilities
- `gmail/spam-scanning`: Scan spam folder for new emails
- `gmail/spam-user-confirmation`: User interface for spam deletion/not-spam decisions
- `gmail/filter-creation`: Create Gmail filter rules based on user confirmations
- `gmail/email-movement`: Move emails between spam and inbox folders
- `classification/spam-detection`: Detect potential spam in inbox emails

### Modified Capabilities
- `gmail-account-access`: Extended to require write scopes for spam handling

## Impact

**Affected code:**
- `maily/gmail.py` - Add spam handling methods, write operations
- `maily/cli.py` - Add spam-related commands
- `maily/tui.py` - Add spam confirmation UI
- `maily/auth.py` - Extend to handle write scopes
- New OAuth client configuration with write permissions

**Dependencies:**
- Gmail API write scopes
- User confirmation for destructive operations

## Deferral Notice

**⚠️ THIS CHANGE IS EXPLICITLY DEFERRED**

Implementation of this change is **blocked** until the following are complete:
1. `static-analysis-category-learning` - User-configurable rules and category editing
2. TUI email expansion with sender/body display
3. TUI summary hotkey for selected email

Rationale: The v1 foundation is read-only. Adding Gmail mutations (deleting, moving, creating filters) introduces significant complexity around:
- OAuth scope changes (read-only → read/write)
- User confirmation for destructive actions
- Error handling for write operations
- Rollback strategies
- Testing infrastructure for mutations

Once core triage is stable, this change should be **revisited and re-defined** with a fresh proposal that accounts for the completed foundation.
