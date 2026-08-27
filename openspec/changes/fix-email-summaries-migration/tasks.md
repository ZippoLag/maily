## 1. Migration fix

- [x] 1.1 Bump `SCHEMA_VERSION` to 3 and add the v3 migration block creating `email_summaries` and its index with `IF NOT EXISTS`, updating `schema_version`
- [x] 1.2 Add a regression test: build a v1 database from the original foundation schema (without `email_summaries`), seed data, migrate, and assert the table and index exist, the version is 3, and existing data is preserved; update any existing test that asserts `schema_version == 2`

## 2. Degraded fallback

- [x] 2.1 Move the summary cache read and write inside `_generate_summary`'s degraded-fallback path so cache failures yield the deterministic preview instead of raising
- [x] 2.2 Add a test: when the summary cache fails (e.g., the table is missing), `_generate_summary` returns the preview rather than raising

## 3. Verification

- [x] 3.1 Run the full test suite and all quality gates (pre-commit hook: ruff, mypy, coverage) green
