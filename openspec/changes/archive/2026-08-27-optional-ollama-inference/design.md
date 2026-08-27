## Context

Currently, `Classifier.classify()` in `maily/classifier.py` automatically falls back to the Ollama provider when deterministic rules don't match a message. The provider is passed to the classifier constructor and used unconditionally when available. This leads to unnecessary inference calls for messages that could remain in `Other` without computational overhead.

## Goals / Non-Goals

**Goals:**
- Add a configuration flag to control when inference is invoked
- Default to inference disabled to minimize resource usage
- Maintain backward compatibility where possible (existing behavior when enabled)
- Ensure deterministic rules always run first regardless of inference mode
- Preserve caching behavior for both deterministic and inference-based classifications

**Non-Goals:**
- Adding new inference features (summarization, etc.) - this change only controls existing classification inference
- Modifying the inference provider interface
- Adding rate limiting or retry logic for inference calls
- Changing the caching mechanism

## Decisions

### Inference Mode as Boolean Configuration

**Decision:** Add a simple `inference_enabled: bool` configuration option in `config.toml` under a new `[classification]` section.

**Rationale:** A boolean is sufficient for the current use case (on/off for classification fallback). More granular modes (e.g., "only for specific categories") can be added later without breaking existing behavior. Keeping it simple reduces complexity and configuration surface area.

**Alternatives considered:**
- Enum with multiple modes (disabled/auto/manual): Overkill for current needs
- Per-category inference toggle: Adds complexity without clear immediate benefit
- Environment variable only: Less discoverable than config file option

### Default to Disabled

**Decision:** Default `inference_enabled` to `false`.

**Rationale:** The user's explicit requirement is to avoid slow/expensive inference when not needed. An opt-in model ensures users explicitly choose to incur the cost. This also aligns with the principle of least surprise - users who don't configure inference won't be affected by its performance characteristics.

**Alternatives considered:**
- Default to enabled (current implicit behavior): Would break the user's requirement
- No default, require explicit setting: Would block first-time users from scanning

### Pass Inference Mode to Classifier

**Decision:** Pass the inference mode flag through the `Classifier` constructor alongside the provider.

**Rationale:** The `Classifier` is the single point where the inference decision is made, so it should have all the information it needs. This keeps the change localized and maintains the existing pattern of passing dependencies through constructors.

**Alternatives considered:**
- Check configuration directly in `Classifier.classify()`: Would create a dependency on the config module and make the classifier less testable
- Add a separate method for inference-only classification: Would complicate the API without clear benefit

### Preserve Cached Inference Results

**Decision:** When inference is disabled, still honor cached inference results from previous scans (when inference was enabled).

**Rationale:** Cached results represent classifications the user has already paid the computational cost for. Discarding them would mean re-classifying messages as `Other` that were previously categorized, which could be confusing. The cache fingerprint already includes the message content and rules, so the results remain valid.

**Alternatives considered:**
- Clear inference cache when disabled: Would cause classification regressions
- Always ignore inference cache when disabled: Would waste stored results

## Risks / Trade-offs

[Risk: Users may not realize inference is disabled] → Mitigation: Log a warning when a message would have been passed to inference but inference is disabled (first occurrence only to avoid spam)

[Risk: Users with inference disabled see more messages in `Other`] → Mitigation: This is expected and desired behavior per the requirement; documentation will clarify the trade-off

[Risk: Breaking existing users who rely on automatic inference] → Mitigation: This is a behavioral change but aligns with the explicit requirement. The change can be documented as a new feature with the old behavior available via configuration.

## Migration Plan

No migration needed for existing state. On upgrade:
- New installations: `inference_enabled` defaults to `false`
- Existing installations: `inference_enabled` will not exist in config, which should be treated as `false` (disabled)
- Users who want the old behavior: Set `inference_enabled = true` in `[classification]` section of config

## Open Questions

- Should we add a CLI flag to temporarily enable inference for a single scan (e.g., `maily scan --inference`)? This could be useful for testing without changing config.
- Should inference mode be a per-scan override or only a persistent configuration?
