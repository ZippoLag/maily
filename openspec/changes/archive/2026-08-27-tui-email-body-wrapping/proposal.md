## Why

Expanded email bodies in the TUI render as a single unwrapped line: `_add_email_node` flattens newlines to spaces, truncates to 1000 characters, and adds the result as a Tree node label. Textual's Tree renders exactly one line per node and never wraps text, so long bodies overflow the terminal and are unreadable. The archived email-expansion spec already promised "wraps the text and allows scrolling to view all content," but the implementation never delivered it — the wrapping contract was never actually met.

## What Changes

- Add a reading pane below the category tree that shows the selected/expanded email's sender, subject, and full body
- Body text wraps to the pane's width — the available terminal width — and reflows automatically when the terminal is resized
- Paragraph breaks in the stored body are preserved (no more newline flattening)
- Long bodies scroll within the pane instead of being truncated to 1000 characters
- "(no body)" still appears only for emails that genuinely have no body content
- No breaking changes to scan, classification, config, or the CLI

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `tui/email-expansion`: Expanded email details move from single-line tree rows to a wrapping reading pane; the body content formatting requirement is tightened to wrap-to-available-width, preserve paragraph structure, and reflow on terminal resize

## Impact

- `maily/tui.py`: layout (tree + reading pane), `_add_email_node` body handling, email selection wiring, pane scroll behavior
- `tests/test_tui.py`: pane text/wrapping helper tests
- README TUI section
