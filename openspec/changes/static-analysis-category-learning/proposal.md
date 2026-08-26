## Why

The current static analysis rules are hardcoded in source with only 3 of 8 categories covered, and users cannot customize them. This limits categorization accuracy and forces reliance on inference for many emails that could be deterministically classified. Users need a way to teach maily their personal email patterns without requiring LLM inference.

This change enables pure static-analysis categorization that improves over time through user feedback, while keeping the system fully functional without inference. It also creates a path for community-contributed rule improvements.

## What Changes

- **New**: User-configurable static analysis rules via config.toml with same format as default rules
- **New**: TUI category editing - users can add/remove categories per email with a simple interface
- **New**: Rule learning system - maily analyzes user category corrections and suggests new rules
- **New**: Multi-category display - emails show primary category with badges for additional categories
- **Modified**: Classification to prioritize static rules and track which rules matched which emails
- **Modified**: Database schema to store user category overrides and rule provenance

## Capabilities

### New Capabilities
- `classification/user-rules`: User-configurable static analysis rules in config.toml format
- `classification/rule-learning`: System that learns and suggests new rules from user category corrections
- `tui/category-editing`: TUI interface for viewing and editing email categories
- `email-presentation/multi-category-display`: Display primary category with badges for secondary categories

### Modified Capabilities
- `classification/static-analysis`: Enhanced to support user-defined rules and track rule matches per email
- `local-state`: Extended to store user category overrides and learned rule suggestions

## Impact

**Affected code:**
- `maily/classifier.py` - Rule loading from config, rule matching tracking
- `maily/config.py` - New rule configuration parsing
- `maily/db.py` - New tables for user overrides and learned rules
- `maily/tui.py` - Category editing interface, multi-category display
- `maily/sync.py` - Updated to handle user overrides during classification

**New data:**
- Config file: `[classification.rules]` section
- Database: `user_category_overrides` table, `learned_rule_suggestions` table

**Dependencies:** None new (pure Python, no LLM required for core functionality)
