## 1. Config and Rule Loading

- [x] 1.1 Add rule parsing to config.py - parse `[classification.rules]` table from TOML and convert to Rule objects, verify with test that user rules are loaded and combined with defaults
- [x] 1.2 Add rule validation in config.py - validate regex patterns on config load, verify invalid patterns raise clear errors
- [x] 1.3 Update _write_default_config to include commented examples of user rules, verify default config includes examples
- [x] 1.4 Add Rule.to_dict() and Rule.from_dict() methods for serialization, verify round-trip conversion works

## 2. Classifier Enhancements

- [x] 2.1 Update Classifier.__init__ to accept rule loading from config, verify Classifier can be instantiated with user rules
- [x] 2.2 Modify Rule.matches() to track which specific patterns matched, verify matched patterns are recorded
- [x] 2.3 Update ClassificationResult to include matched_rules field, verify rules are tracked in results
- [x] 2.4 Add primary category selection logic - first matched rule or first user category, verify with test that primary is selected correctly
- [x] 2.5 Update classifier.classify() to separate rule matching from inference, verify deterministic rules run before inference

## 3. Database Schema Updates

- [ ] 3.1 Add user_category_overrides table migration to db.py, verify table is created on new database
- [ ] 3.2 Add learned_rule_suggestions table migration to db.py, verify table is created on new database
- [ ] 3.3 Add Database methods: get_user_override(), set_user_override(), delete_user_override(), verify with tests
- [ ] 3.4 Add Database methods: get_rule_suggestions(), add_rule_suggestion(), update_rule_suggestion_status(), verify with tests
- [ ] 3.5 Update seed_categories to handle new tables gracefully, verify existing databases work

## 4. User Override Application

- [ ] 4.1 Add override application logic in sync.py - apply user overrides after classification, verify overrides replace rule-based categories
- [ ] 4.2 Update scan() to store both original and override classifications, verify both are persisted
- [ ] 4.3 Add fingerprint tracking for overrides, verify reclassification happens when rules change
- [ ] 4.4 Update cached_classification() to check for overrides, verify overrides are applied from cache

## 5. TUI Category Editing

- [ ] 5.1 Add 'c' key binding to BrowseApp for category edit mode, verify key opens edit dialog
- [ ] 5.2 Create CategoryEditModal widget with checkbox list of all categories, verify modal displays all categories
- [ ] 5.3 Implement toggle logic for categories in modal, verify checkboxes can be toggled
- [ ] 5.4 Add save/cancel functionality to modal, verify changes are persisted on save and discarded on cancel
- [x] 5.5 Update categorized_messages() query to include user overrides, verify TUI displays user categories
- [x] 5.6 Update tree display to show primary category with secondary badges, verify visual distinction
- [x] 5.7 Add multi-select support for batch editing, verify multiple emails can be edited together
- [x] 5.8 Add visual feedback (notifications) for category changes, verify user sees confirmation

## 6. Multi-Category Display

- [x] 6.1 Create helper function to determine primary category, verify correct selection
- [x] 6.2 Create helper function to format category badges, verify badges render correctly
- [x] 6.3 Update Tree node rendering to show primary + badges, verify display in TUI
- [x] 6.4 Add truncation logic for many categories, verify "+N more" indicator shows
- [x] 6.5 Add tooltip/hover for full category list, verify full list accessible

## 7. Rule Learning System

- [ ] 7.1 Implement stop word list (English, ~100 words), verify common words are filtered
- [ ] 7.2 Implement pattern extraction from email content, verify words are extracted correctly
- [ ] 7.3 Implement frequency counting per category, verify counts are accurate
- [ ] 7.4 Implement suggestion generation with minimum threshold (default: 3), verify suggestions only appear at threshold
- [ ] 7.5 Add suggestion presentation to TUI, verify user can see and confirm suggestions
- [ ] 7.6 Add accepted suggestions to user config, verify new rules appear in config.toml
- [ ] 7.7 Add suggestion status tracking (pending/accepted/rejected), verify status updates correctly

## 8. Integration and Testing

- [ ] 8.1 Add integration test: user adds rule to config, verifies email is classified correctly
- [ ] 8.2 Add integration test: user overrides category in TUI, verifies change persists
- [ ] 8.3 Add integration test: rule learning suggests pattern from corrections, verifies suggestion is accurate
- [ ] 8.4 Add integration test: multi-category display shows primary + badges, verifies rendering
- [ ] 8.5 Add test: system works with inference disabled, verify no errors
- [ ] 8.6 Add test: database migration for existing users, verify no data loss

## 9. Documentation Updates

- [ ] 9.1 Update README.md with user rules configuration examples, verify documentation is clear
- [ ] 9.2 Add TUI category editing documentation to README.md, verify keyboard shortcuts documented
- [ ] 9.3 Update default config.toml comments with rule examples, verify examples are helpful
- [ ] 9.4 Add documentation for rule learning feature, verify user understands the flow
