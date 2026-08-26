## Why

Users need immediate visibility into action-required emails without opening the TUI or parsing JSON. Currently, the human-readable scan output only shows category counts, requiring users to switch to TUI or JSON format to see which specific emails need attention. Displaying email titles and senders for the "Action Required" category by default makes the CLI immediately actionable for the most urgent messages.

## What Changes

- **CLI human-readable output**: Extend `render_human` to display the subject (title) and sender of each email in the "Action Required" category by default
- **No breaking changes**: The change is additive - existing JSON output and TUI remain unchanged
- **Category-specific**: Only "Action Required" emails get expanded detail; other categories continue to show counts only

## Capabilities

### New Capabilities
- `email-presentation/action-required-details`: Display title and sender for Action Required emails in human-readable scan output

### Modified Capabilities
- `email-presentation`: Extend the human-readable scan output requirement to include message details for the Action Required category

## Impact

- `maily/cli.py`: Modify `render_human` function to include message details for Action Required category
- No changes to `maily/sync.py` or `maily/models.py` - the data is already available in the scan result
- No changes to database or classification logic
