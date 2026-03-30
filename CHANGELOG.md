# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog, but kept intentionally lightweight for the current alpha stage.

## [1.0.0] - 2026-03-30

### Added

- Added protocol-first bulk mutation APIs for stores and bound model views.
- Added release-ready public API docs, packaging marker, and publishing workflow inputs.

### Changed

- Promoted TypedStore from alpha facade toolkit to a stable public SDK surface.
- Split ORM object mutation and SQL bulk mutation into separate public methods.

### Verified

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run ty check`
- `uv run pytest`
- `uv build`
- `uv run --with twine twine check dist/*`

## [0.1.0] - 2026-03-13

### Added

- Initialized the `TypedStore` SDK workspace with `AGENTS.md`, `workflow.md`, docs, todo tracking, and project packaging.
- Implemented `SyncTypedStore`, `AsyncTypedStore`, and `TypedStore` bundle.
- Implemented engine/session helpers, `UnitOfWork` / `AsyncUnitOfWork`, `QuerySpec`, `Page`, and `TypedStoreModel`.
- Added sync/async examples, repository-pattern examples, and example smoke tests.
- Added error boundary tests covering missing session factories, invalid store bindings, and projection pagination misuse.
- Added `ruff` + `ty` + `pytest` toolchain integration.
- Added GitHub Actions CI and release workflows.
- Added release preparation docs for TestPyPI / PyPI Trusted Publisher.

### Changed

- Explicitly removed the old DBORM compatibility direction and converged on the new typed facade API.
- Split sync and async access into dedicated facades instead of keeping a single mixed-behavior surface.
- Tightened typing around `QuerySpec`, model store bindings, and SQLAlchemy-facing inputs.

### Verified

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run ty check`
- `uv run pytest`
- `uv build`
- `uv run --with twine twine check dist/*`
