## 1. Configuration Changes

- [x] 1.1 Add `inference_enabled` field to `MailyConfig` dataclass in `maily/config.py` with default `False` and verify config loads with the new field
- [x] 1.2 Add `[classification]` section with `inference_enabled` to default config generation in `maily/config.py` and verify default config file includes the new option
- [x] 1.3 Parse `inference_enabled` from config file in `load_config()` and verify it's correctly read from `config.toml`

## 2. Classifier Integration

- [x] 2.1 Add `inference_enabled` parameter to `Classifier.__init__()` in `maily/classifier.py` and verify classifier instantiates with the new parameter
- [x] 2.2 Modify `Classifier.classify()` to check `inference_enabled` before invoking provider and verify provider is only called when enabled
- [x] 2.3 Update `cli.py` to pass `config.inference_enabled` when creating the `Classifier` instance and verify the flag flows through correctly

## 3. Caching Behavior

- [x] 3.1 Ensure cached inference results are still returned when `inference_enabled=False` and verify cached classifications persist across scans
- [x] 3.2 Verify that new messages without cached results fall back to `Other` when inference is disabled

## 4. Testing

- [x] 4.1 Add test in `tests/test_classifier.py` for `inference_enabled=False` with no rule match resulting in `Other` classification and verify the test passes
- [x] 4.2 Add test in `tests/test_classifier.py` for `inference_enabled=True` restoring old behavior when provider available and verify the test passes
- [x] 4.3 Add test for config parsing of `inference_enabled` in `tests/test_local_state.py` and verify the test passes
- [x] 4.4 Run full test suite and verify all tests pass

## 5. Documentation

- [x] 5.1 Update `README.md` to document the new `[classification]` config section and `inference_enabled` option
- [x] 5.2 Add example of enabling inference in the setup or configuration section
