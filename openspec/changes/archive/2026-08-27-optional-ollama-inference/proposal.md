## Why

Local Ollama inference is slow and computationally expensive. Currently, when deterministic rules fail to classify a message, maily automatically falls back to Ollama if available. This change makes inference opt-in, ensuring it is only used when static analysis is insufficient AND the user has explicitly enabled it, or when explicit inference features (like email summarization) are requested.

## What Changes

- Add configuration option to enable/disable Ollama inference for classification fallback
- When inference is disabled, messages that don't match deterministic rules go directly to `Other` without calling Ollama
- Maintain existing behavior: deterministic rules always run first, caching still works, degraded mode still reported when provider unavailable
- Future: enable inference explicitly for specific features like email summarization

## Capabilities

### New Capabilities
- `classification/inference-mode` : Control when inference is invoked for message classification

### Modified Capabilities
- `email-triage`: Modify requirement to make inference provider usage conditional on configuration, not just availability

## Impact

- `maily/classifier.py`: Add inference mode check before invoking provider
- `maily/config.py`: Add new configuration option (e.g., `inference_enabled`)
- `maily.egg-info/`: Will be regenerated on next build
- Tests in `tests/test_classifier.py`: Add tests for disabled inference mode
- Documentation: Update to explain new configuration option
