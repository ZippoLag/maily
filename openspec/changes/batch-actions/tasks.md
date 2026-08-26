## 1. Model Updates

- [ ] 1.1 Add labels field to EmailMessage model in models.py, verify field is added
- [ ] 1.2 Update EmailMessage.as_dict() to include labels, verify serialization works
- [ ] 1.3 Update database schema to store labels, verify labels are persisted

## 2. Gmail Client Updates

- [ ] 2.1 Update parse_message() in gmail.py to extract labels from Gmail response, verify labels are parsed
- [ ] 2.2 Add labels to GoogleGmailClient.today_unread() return, verify labels are included
- [ ] 2.3 Handle missing labels field in old data, verify backward compatibility

## 3. TUI Multi-Select

- [ ] 3.1 Add selection set to BrowseApp state, verify selection is tracked
- [ ] 3.2 Add Space key binding to toggle selection, verify Space selects/deselects email
- [ ] 3.3 Add Ctrl+A binding for select all visible, verify all visible are selected
- [ ] 3.4 Add Ctrl+D binding for deselect all, verify all are deselected
- [ ] 3.5 Add Escape binding to clear selection, verify selection clears
- [ ] 3.6 Add visual selection indicators (checkboxes), verify selected emails are visible
- [ ] 3.7 Add selection count display in status bar, verify count updates correctly
- [ ] 3.8 Implement selection persistence across scroll/sort, verify selection stays on emails

## 4. Label Badges

- [ ] 4.1 Create LabelBadge widget for TUI, verify badge renders correctly
- [ ] 4.2 Add label badges to email display in tree, verify badges appear next to emails
- [ ] 4.3 Implement label badge styling (colors), verify different labels have different colors
- [ ] 4.4 Add label truncation with "+N more" indicator, verify long label lists are truncated
- [ ] 4.5 Add label badge tooltips, verify full label name shows on hover
- [ ] 4.6 Add click-to-filter by label, verify clicking badge filters view

## 5. Batch Categorization

- [ ] 5.1 Update 'c' hotkey to detect selection state, verify it opens batch mode when selected
- [ ] 5.2 Create BatchCategoryModal widget, verify modal shows selection count
- [ ] 5.3 Implement batch category application logic, verify categories apply to all selected
- [ ] 5.4 Add confirmation dialog for batch categorization, verify user must confirm
- [ ] 5.5 Add batch operation notification, verify feedback shows count
- [ ] 5.6 Handle partial failures in batch operations, verify errors are reported

## 6. Batch Action Suggestions

- [ ] 6.1 Create suggestion analysis function, verify patterns are detected
- [ ] 6.2 Implement deterministic suggestion generation, verify suggestions work without inference
- [ ] 6.3 Implement confidence scoring, verify scores are reasonable
- [ ] 6.4 Add inference-based suggestions (optional), verify AI suggestions work when enabled
- [ ] 6.5 Create SuggestionPanel widget for TUI, verify suggestions display correctly
- [ ] 6.6 Add suggestion caching per selection, verify same selection uses cache
- [ ] 6.7 Add suggestion acceptance flow, verify user can accept suggestions
- [ ] 6.8 Handle read-only vs mutation suggestions differently, verify categorization works, mutations show as unavailable

## 7. Integration and Testing

- [ ] 7.1 Add test: multi-select with Space key, verify selection works
- [ ] 7.2 Add test: select all/deselect all, verify shortcuts work
- [ ] 7.3 Add test: selection persistence across sort, verify selection stays with emails
- [ ] 7.4 Add test: label badges display, verify labels are visible
- [ ] 7.5 Add test: click label to filter, verify filter works
- [ ] 7.6 Add test: batch categorization, verify categories apply to all selected
- [ ] 7.7 Add test: batch categorization confirmation, verify user must confirm
- [ ] 7.8 Add test: suggestion generation, verify suggestions are generated
- [ ] 7.9 Add test: inference suggestions, verify AI suggestions work
- [ ] 7.10 Add test: read-only safety, verify no Gmail mutations occur

## 8. Documentation

- [ ] 8.1 Update README.md with multi-select usage, verify keyboard shortcuts documented
- [ ] 8.2 Add batch categorization docs to README.md, verify workflow documented
- [ ] 8.3 Add Gmail label badges documentation to README.md, verify feature documented
- [ ] 8.4 Add batch action suggestions documentation, verify usage is clear
