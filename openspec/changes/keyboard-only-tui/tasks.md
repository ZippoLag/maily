## 1. Core Implicit Selection

- [x] 1.1 Add `on_tree_node_highlighted` handler to BrowseApp that updates `self.selected_email` and `self.selected_emails` when the user navigates to an email node, verify the status bar updates on keyboard navigation
- [x] 1.2 Update `on_tree_node_selected` to also set `self.selected_email` (keep existing behavior), verify both mouse click and keyboard navigation set the same state

## 2. Action Handlers

- [x] 2.1 Modify `action_summarize` to use the focused email (from `on_tree_node_highlighted`) when no emails are marked, verify pressing 'S' on a focused email shows a summary without "Select an email first" error
- [x] 2.2 Modify `action_mark` to use the focused email when no emails are marked, verify pressing 'm' on a focused email toggles it in the marked set
- [x] 2.3 Modify `action_edit_categories` to use the focused email when no emails are marked, verify pressing 'c' on a focused email opens the category edit modal

## 3. Status Bar Feedback

- [x] 3.1 Update status bar display to show the focused email's sender, subject, and categories when navigating, verify status bar reflects the currently highlighted email
- [x] 3.2 Update status bar to show marked count when emails are marked, verify status shows "N marked | focused: ..." when emails are marked

## 4. Testing

- [x] 4.1 Add test: keyboard navigation sets selected_email (simulate NodeHighlighted), verify selected_email updates
- [x] 4.2 Add test: action_summarize works on focused email without explicit selection, verify summary is generated
- [x] 4.3 Add test: action_mark works on focused email without explicit selection, verify email is toggled
- [x] 4.4 Add test: bulk actions apply to all marked emails, verify action targets marked set
- [x] 4.5 Add test: single action targets focused email when no emails are marked, verify action targets single email
