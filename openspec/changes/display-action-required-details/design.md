## Context

The current `render_human` function in `maily/cli.py` only displays category counts. The scan result already contains all message data via the `categories` dictionary in the payload, which maps category names to lists of message dicts. The EmailMessage model includes `subject` and `sender_email` fields that can be used directly.

## Goals / Non-Goals

**Goals:**
- Extend human-readable output to show subject and sender for Action Required emails
- Maintain backward compatibility - JSON output and existing behavior for other categories unchanged
- Use existing data structures without new database queries or API calls

**Non-Goals:**
- Changing JSON output format
- Adding new CLI flags or options
- Modifying TUI behavior
- Changing classification or scan logic

## Decisions

### Modify render_human function in cli.py
The change will be localized to the `render_human` function. This function already receives the full payload with categorized messages. We will:
1. Iterate through categories in sorted order (existing behavior)
2. When we encounter "Action Required" category, after displaying the count, iterate through its messages
3. For each message, display subject and sender_email on a new indented line
4. Handle empty subjects by displaying "(no subject)"

**Alternatives considered:**
- Adding a new CLI flag like `--show-details`: Rejected because the requirement is for default behavior
- Creating a new output format: Rejected as it would add complexity without clear benefit
- Modifying the ScanResult model: Not needed as all required data is already available

### Format for email details
Each Action Required email will be displayed as: `  - <subject> (<sender_email>)`
- Two-space indent to visually nest under the category line
- Dash prefix for bullet-point style consistency
- Parentheses around sender email for clarity

**Rationale:** This format is clear, compact, and consistent with typical CLI output patterns. It doesn't require color or complex formatting that might break in different terminals.

## Risks / Trade-offs

**[Long output for many Action Required emails]** → This is acceptable because: (1) Action Required should be a small subset of emails by design, (2) users can still use `--json-format` for scripting if they need to process many emails, (3) the TUI remains available for interactive browsing

**[Case sensitivity of category name]** → The category name "Action Required" is used as-is from the config. The implementation will match the exact category name, which is defined in `DEFAULT_CATEGORIES` in `maily/config.py`. The code will check for the exact string match.

**[Empty sender_email]** → If sender_email is empty or None, we will display only the subject with a fallback for sender. Based on the EmailMessage model, sender_email should always be present.
