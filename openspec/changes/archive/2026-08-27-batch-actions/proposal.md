## Why

Users need to perform actions on multiple emails at once, particularly for large-scale triage of backlog emails. The current TUI is read-only with no multi-select capability. This change adds **batch selection and action suggestions** while maintaining the read-only nature for safety (AI suggests, user confirms).

This addresses the need to efficiently process large email volumes (5000+ unread) where individual actions would be impractical.

**Prerequisite:** `keyboard-only-tui` — establishes implicit selection of the focused email and keyboard-driven action flow. This change builds on that foundation by adding explicit multi-select (Space toggle), batch operations, and AI-assisted suggestions.

## What Changes

- **New**: Multi-select in TUI (select multiple emails via keyboard or mouse)
- **New**: Visual selection indicators (checked checkboxes or highlighted rows)
- **New**: Batch categorization (apply category to all selected emails)
- **New**: Display Gmail labels/tags/folders as badges on emails
- **New**: AI-assisted batch action suggestions after digesting selected emails
- **New**: Confirmation dialog for batch actions (shows count, action type, affected emails)
- **New**: Selection count display (e.g., "3 of 10 emails selected")
- **Modified**: TUI keyboard bindings to support selection mode
- **Modified**: Email display to include Gmail label badges

**BREAKING**: This introduces Gmail label/tag visibility, which may expose data not previously shown.

## Capabilities

### New Capabilities
- `tui/multi-select`: Select multiple emails for batch operations
- `tui/batch-categorization`: Apply category to all selected emails
- `tui/gmail-label-badges`: Display Gmail labels/tags as visual badges
- `tui/batch-action-suggestions`: AI suggests actions (delete, archive, mark read) based on selected emails
- `email-presentation/gmail-labels`: Parse and display Gmail label information

### Modified Capabilities
- `email-presentation`: Extended to include Gmail label badges in display
- `tui/category-editing`: Extended to support batch operations

## Impact

**Affected code:**
- `maily/tui.py` - Add multi-select, batch categorization, label badges, action suggestions
- `maily/gmail.py` - Expose label data in EmailMessage model
- `maily/models.py` - Add labels field to EmailMessage
- `maily/classifier.py` or new module - Batch action suggestion logic

**New data:**
- EmailMessage.labels: list of Gmail label names

**Dependencies:**
- For AI suggestions: Ollama (optional, fallback to no suggestions)

## Safety Note

**This change maintains read-only safety**:
- Batch **categorization** is allowed (stored locally, no Gmail mutation)
- AI **suggests** actions but does NOT perform them
- Actual Gmail mutations (delete, archive, mark read) remain **out of scope** for this change
- Future change needed for actual mutations (would require write scopes)
