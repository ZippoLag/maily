## Context

The original `maily.md` specification requires comprehensive spam handling including scanning spam folder, user confirmation workflows, Gmail filter creation, and email movement. This was not included in the v1 foundation which focused on read-only operations.

## Goals / Non-Goals

**Goals:**
- Capture the original spam handling requirements
- Document the architectural impact (write scopes, mutations)
- Provide a foundation for future implementation

**Non-Goals:**
- Implement anything (explicitly deferred)
- Define detailed implementation approach (will be redefined later)

## Decisions

### Decision: Deferred Implementation

**Chosen:** Explicitly defer all spam handling implementation until core triage is complete

**Rationale:**
- v1 foundation is read-only
- Adding mutations introduces significant complexity
- Core triage (static-analysis, TUI) needs to be stable first
- OAuth scope changes require careful handling

**Revisit After:**
1. `static-analysis-category-learning` is implemented
2. TUI email expansion (sender/body) is implemented
3. TUI summary hotkey is implemented

## Risks / Trade-offs

**[Risk]** Spam handling is a major user need from the original spec → **Mitigation:** Deferring with clear tracking ensures we don't forget it

**[Risk]** Gmail write scopes are a significant architectural change → **Mitigation:** This will be addressed when the change is redefined for implementation

## Migration Plan

**Not applicable** - Implementation is deferred. When revisited, this section will be populated with a proper migration plan.

## Open Questions

To be answered when this change is redefined for implementation:
- Should spam handling be a separate CLI command or integrated into scan?
- How should spam messages be displayed in TUI?
- Should filter creation be automatic or always require user confirmation?
- How to handle rate limits on Gmail write operations?
