## 1. Reading pane layout

- [x] 1.1 Add a wrap-enabled `Static` reading pane below the `CategoryTree` in `compose()` (tree + pane in a height-split layout) so the pane exists at the current terminal width
- [x] 1.2 Wire email selection/expansion (`on_tree_node_selected` and the expansion gesture) to populate the pane with the selected email's sender, subject, and body

## 2. Body rendering

- [x] 2.1 Add a pure helper (e.g., `email_pane_text(item, width)`) that composes sender/subject/body, preserves stored paragraph breaks, and wraps lines to the given width
- [x] 2.2 Remove the newline-flattening and 1000-char truncation from `_add_email_node`; render "(no body)" only when the stored body is empty
- [x] 2.3 Verify the pane reflows when the terminal is resized (Textual re-renders `Static` at the new width)

## 3. Tests

- [x] 3.1 Unit-test the pane-text helper: long lines wrap to width; paragraph breaks are preserved; empty body yields "(no body)"; sender and subject are included
- [x] 3.2 Run the full test suite (`pytest`) and confirm all tests pass with no regressions in tree rendering

## 4. Documentation

- [x] 4.1 Update the README TUI section to describe the reading pane and body wrapping
