# Protocol-First Public SDK v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce the v0.2 public surface reset for TypedStore by making `Model.bind(store)` the primary model API, adding explicit lifecycle APIs, and deprecating implicit-store paths without breaking current consumers.

**Architecture:** This plan intentionally covers `v0.2` only. It keeps the existing SQLAlchemy-backed implementation largely intact, adds a new bound-model public path on top, and introduces lifecycle/deprecation primitives that realign the SDK's public surface before the deeper protocol/spec split planned for `v0.3`.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.x, pytest, pytest-asyncio, ruff, ty

---

## Scope

This plan implements only the `v0.2` slice from the approved design spec:

- Add pure functional `Model.bind(store)` as the new primary model path
- Add bound-model view objects for sync and async stores
- Add explicit `dispose()` / `close()` / `aclose()` lifecycle APIs
- Deprecate global default store APIs and `TypedStore` sync delegate usage
- Update docs/examples/tests so new users learn the new path first

The following are explicitly deferred to later plans:

- Capability protocol extraction
- `QuerySpec` split into smaller request objects
- Bulk SQL-level update/delete redesign
- Full `v1.0` removal of compatibility APIs

## File Structure

### Create

- `typed_store/bound_model.py`
- `tests/test_bound_model.py`

### Modify

- `typed_store/model.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/store.py`
- `typed_store/__init__.py`
- `tests/test_shortcuts.py`
- `tests/test_error_boundaries.py`
- `README.md`
- `docs/api-surface.md`
- `docs/design-spec.md`
- `docs/internal/progress.md`
- `examples/model_mixin.py`

### Responsibilities

- `typed_store/bound_model.py`: bound-model public objects for sync/async model operations
- `typed_store/model.py`: `TypedStoreModel.bind(store)` implementation, compatibility shims, deprecation warnings
- `typed_store/sync.py` and `typed_store/async_store.py`: lifecycle APIs and any helper hooks needed by bound views
- `typed_store/store.py`: composition root lifecycle support and sync delegate deprecations
- `tests/test_bound_model.py`: new main-path coverage for `Model.bind(store)`
- `tests/test_shortcuts.py` / `tests/test_error_boundaries.py`: deprecation and compatibility coverage
- docs/examples: move primary teaching path to `Model.bind(store)`

### Task 1: Add Sync Bound Model Views

**Files:**
- Create: `typed_store/bound_model.py`
- Modify: `typed_store/model.py`
- Modify: `typed_store/__init__.py`
- Test: `tests/test_bound_model.py`

- [ ] **Step 1: Write the failing sync bind tests**

```python
from __future__ import annotations

from tests.conftest import Widget
from typed_store.bound_model import SyncBoundModelView


def test_bind_returns_sync_bound_model_view(store):
    bound = Widget.bind(store.sync)

    assert isinstance(bound, SyncBoundModelView)


def test_sync_bound_model_view_insert_find_and_get(store):
    widgets = Widget.bind(store.sync)

    created = widgets.insert(Widget(name="bind-alpha", category="bind"))
    rows = widgets.find_many(Widget.category == "bind")
    found = widgets.get(created.id)

    assert [row.name for row in rows] == ["bind-alpha"]
    assert found is not None
    assert found.name == "bind-alpha"
```

- [ ] **Step 2: Run the sync bind tests to verify they fail**

Run: `uv run pytest tests/test_bound_model.py -q`
Expected: FAIL with import or attribute errors for `typed_store.bound_model` and `Widget.bind`

- [ ] **Step 3: Write the minimal sync bound-model implementation**

```python
# typed_store/bound_model.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from typed_store.query_spec import FilterClause, OrderClause, QuerySpec
from typed_store.results import Page
from typed_store.sync import SyncTypedStore

TModel = TypeVar("TModel")


class SyncBoundModelView(Generic[TModel]):
    def __init__(self, model: type[TModel], store: SyncTypedStore[object]):
        self._model = model
        self._store = store

    def insert(
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return self._store.insert(entity, session=session, commit=commit, refresh=refresh)

    def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return self._store.insert_many(entities, session=session, commit=commit)

    def get(self, ident: object, *, session: Session | None = None) -> TModel | None:
        return self._store.get(self._model, ident, session=session)

    def find_one(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        session: Session | None = None,
    ) -> TModel | None:
        return self._store.find_one(self._model, *filters, spec=spec, order=order, session=session)

    def find_many(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> list[TModel]:
        return self._store.find_many(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    def paginate(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> Page[TModel]:
        return self._store.paginate(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    def update_fields(
        self,
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.update_fields(
            self._model, values, *filters, spec=spec, session=session, commit=commit
        )

    def delete_where(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.delete_where(
            self._model, *filters, spec=spec, session=session, commit=commit
        )
```

```python
# typed_store/model.py
from typing import overload

from typed_store.bound_model import SyncBoundModelView
from typed_store.sync import SyncTypedStore


class TypedStoreModel:
    @classmethod
    @overload
    def bind(cls: type[Self], store: SyncTypedStore[object]) -> SyncBoundModelView[Self]: ...

    @classmethod
    def bind(cls: type[Self], store: SyncTypedStore[object]) -> SyncBoundModelView[Self]:
        return SyncBoundModelView(cls, store)
```

```python
# typed_store/__init__.py
from typed_store.bound_model import SyncBoundModelView

__all__ = [
    "SyncBoundModelView",
]
```

- [ ] **Step 4: Run the sync bind tests to verify they pass**

Run: `uv run pytest tests/test_bound_model.py -q`
Expected: PASS for the new sync bind tests

- [ ] **Step 5: Commit**

```bash
git add typed_store/bound_model.py typed_store/model.py typed_store/__init__.py tests/test_bound_model.py
git commit -m "feat: add sync bound model views"
```

### Task 2: Add Async Bound Model Views And Pure Functional `bind()`

**Files:**
- Modify: `typed_store/bound_model.py`
- Modify: `typed_store/model.py`
- Test: `tests/test_bound_model.py`

- [ ] **Step 1: Write the failing async bind tests**

```python
import pytest

from tests.conftest import Widget
from typed_store.bound_model import AsyncBoundModelView


@pytest.mark.asyncio
async def test_bind_returns_async_bound_model_view(store):
    bound = Widget.bind(store.async_)

    assert isinstance(bound, AsyncBoundModelView)


@pytest.mark.asyncio
async def test_async_bound_model_view_insert_find_and_get(store):
    widgets = Widget.bind(store.async_)

    created = await widgets.insert(Widget(name="bind-beta", category="bind"))
    rows = await widgets.find_many(Widget.category == "bind")
    found = await widgets.get(created.id)

    assert [row.name for row in rows if row.name == "bind-beta"] == ["bind-beta"]
    assert found is not None
    assert found.name == "bind-beta"
```

- [ ] **Step 2: Run the async bind tests to verify they fail**

Run: `uv run pytest tests/test_bound_model.py -q`
Expected: FAIL with missing `AsyncBoundModelView` support or incorrect `bind()` dispatch

- [ ] **Step 3: Extend bound-model support to async stores without storing class state**

```python
# typed_store/bound_model.py
from sqlalchemy.ext.asyncio import AsyncSession

from typed_store.async_store import AsyncTypedStore


class AsyncBoundModelView(Generic[TModel]):
    def __init__(self, model: type[TModel], store: AsyncTypedStore[object]):
        self._model = model
        self._store = store

    async def insert(
        self,
        entity: TModel,
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return await self._store.insert(entity, session=session, commit=commit, refresh=refresh)

    async def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return await self._store.insert_many(entities, session=session, commit=commit)

    async def get(
        self, ident: object, *, session: AsyncSession | None = None
    ) -> TModel | None:
        return await self._store.get(self._model, ident, session=session)

    async def find_many(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: AsyncSession | None = None,
    ) -> list[TModel]:
        return await self._store.find_many(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )
```

```python
# typed_store/model.py
from typed_store.async_store import AsyncTypedStore
from typed_store.bound_model import AsyncBoundModelView, SyncBoundModelView


class TypedStoreModel:
    @classmethod
    @overload
    def bind(cls: type[Self], store: AsyncTypedStore[object]) -> AsyncBoundModelView[Self]: ...

    @classmethod
    @overload
    def bind(cls: type[Self], store: SyncTypedStore[object]) -> SyncBoundModelView[Self]: ...

    @classmethod
    def bind(
        cls: type[Self], store: SyncTypedStore[object] | AsyncTypedStore[object]
    ) -> SyncBoundModelView[Self] | AsyncBoundModelView[Self]:
        if isinstance(store, AsyncTypedStore):
            return AsyncBoundModelView(cls, store)
        if isinstance(store, SyncTypedStore):
            return SyncBoundModelView(cls, store)
        raise InvalidStoreBindingError(
            "bind() requires a SyncTypedStore or AsyncTypedStore instance."
        )
```

- [ ] **Step 4: Run the bound-model tests to verify both sync and async paths pass**

Run: `uv run pytest tests/test_bound_model.py -q`
Expected: PASS for sync and async `bind()` coverage

- [ ] **Step 5: Commit**

```bash
git add typed_store/bound_model.py typed_store/model.py tests/test_bound_model.py
git commit -m "feat: add async bind support for typed models"
```

### Task 3: Add Explicit Store Lifecycle APIs

**Files:**
- Modify: `typed_store/sync.py`
- Modify: `typed_store/async_store.py`
- Modify: `typed_store/store.py`
- Test: `tests/test_shortcuts.py`

- [ ] **Step 1: Write failing lifecycle tests**

```python
import pytest

from typed_store import AsyncTypedStore, SyncTypedStore, TypedStore


class TestLifecycleApis:
    def test_sync_store_close_is_idempotent(self, tmp_path):
        db = tmp_path / "lifecycle.sqlite"
        store = SyncTypedStore.from_url(f"sqlite:///{db}")

        store.close()
        store.dispose()

        assert store.engine is not None

    @pytest.mark.asyncio
    async def test_async_store_aclose_is_idempotent(self, tmp_path):
        db = tmp_path / "lifecycle.sqlite"
        store = AsyncTypedStore.from_url(f"sqlite+aiosqlite:///{db}")

        await store.aclose()
        await store.dispose()

        assert store.engine is not None

    @pytest.mark.asyncio
    async def test_typed_store_closes_both_engines(self, tmp_path):
        db = tmp_path / "typed-store.sqlite"
        store = TypedStore.from_url(
            f"sqlite:///{db}",
            async_url=f"sqlite+aiosqlite:///{db}",
        )

        store.close()
        await store.aclose()

        assert store.engine is not None
        assert store.async_engine is not None
```

- [ ] **Step 2: Run the lifecycle tests to verify they fail**

Run: `uv run pytest tests/test_shortcuts.py::TestLifecycleApis -q`
Expected: FAIL with missing `close`, `dispose`, or `aclose` methods

- [ ] **Step 3: Add explicit lifecycle methods to sync, async, and bundled stores**

```python
# typed_store/sync.py
class SyncTypedStore[TModel]:
    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()

    def close(self) -> None:
        self.dispose()
```

```python
# typed_store/async_store.py
class AsyncTypedStore[TModel]:
    async def dispose(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()

    async def aclose(self) -> None:
        await self.dispose()
```

```python
# typed_store/store.py
class TypedStore:
    def close(self) -> None:
        self.sync.close()

    def dispose(self) -> None:
        self.sync.dispose()

    async def aclose(self) -> None:
        await self.async_.aclose()
```

- [ ] **Step 4: Run lifecycle tests and the existing shortcut suite**

Run: `uv run pytest tests/test_shortcuts.py::TestLifecycleApis tests/test_shortcuts.py -q`
Expected: PASS with the new lifecycle coverage and no regressions in existing shortcut tests

- [ ] **Step 5: Commit**

```bash
git add typed_store/sync.py typed_store/async_store.py typed_store/store.py tests/test_shortcuts.py
git commit -m "feat: add explicit lifecycle APIs for stores"
```

### Task 4: Deprecate Implicit Store Paths

**Files:**
- Modify: `typed_store/model.py`
- Modify: `typed_store/store.py`
- Test: `tests/test_error_boundaries.py`
- Test: `tests/test_shortcuts.py`

- [ ] **Step 1: Write failing deprecation tests**

```python
import pytest

from tests.conftest import Widget
from typed_store.model import clear_default_store, set_default_store


def test_global_default_store_helpers_emit_deprecation_warning(store):
    with pytest.deprecated_call():
        set_default_store(store)

    with pytest.deprecated_call():
        clear_default_store()


def test_typed_store_sync_delegate_emits_deprecation_warning(store):
    with pytest.deprecated_call():
        store.find_many(Widget)
```

- [ ] **Step 2: Run the deprecation tests to verify they fail**

Run: `uv run pytest tests/test_error_boundaries.py tests/test_shortcuts.py -q`
Expected: FAIL because the deprecated paths do not yet emit warnings

- [ ] **Step 3: Add deprecation warnings while keeping compatibility**

```python
# typed_store/model.py
import warnings


def set_default_store(store: StoreBinding) -> None:
    warnings.warn(
        "set_default_store() is deprecated; prefer Model.bind(store).",
        DeprecationWarning,
        stacklevel=2,
    )
    global _default_store
    _default_store = store


def clear_default_store() -> None:
    warnings.warn(
        "clear_default_store() is deprecated; prefer explicit bound model views.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _default_store
    _default_store = None
```

```python
# typed_store/store.py
import warnings


class TypedStore:
    def _warn_sync_delegate(self, method_name: str) -> None:
        warnings.warn(
            f"TypedStore.{method_name}() is deprecated; use SyncTypedStore directly or Model.bind(sync_store).",
            DeprecationWarning,
            stacklevel=2,
        )

    def find_many[TModel](self, model: type[TModel], *filters: FilterClause, **kwargs: object) -> list[TModel]:
        self._warn_sync_delegate("find_many")
        return cast(
            list[TModel],
            self.sync.find_many(model, *filters, **kwargs),
        )
```

- [ ] **Step 4: Run the targeted deprecation tests**

Run: `uv run pytest tests/test_error_boundaries.py tests/test_shortcuts.py -q`
Expected: PASS with deprecation warnings emitted and existing behavior preserved

- [ ] **Step 5: Commit**

```bash
git add typed_store/model.py typed_store/store.py tests/test_error_boundaries.py tests/test_shortcuts.py
git commit -m "refactor: deprecate implicit store access paths"
```

### Task 5: Move Docs And Examples To The Bind-First Path

**Files:**
- Modify: `README.md`
- Modify: `docs/api-surface.md`
- Modify: `docs/design-spec.md`
- Modify: `docs/internal/progress.md`
- Modify: `examples/model_mixin.py`
- Test: `tests/test_examples.py`

- [ ] **Step 1: Write failing docs/example expectation tests**

```python
from pathlib import Path


def test_readme_recommends_bind_first_path():
    readme = Path("README.md").read_text()

    assert "User.bind(store)" in readme
    assert "set_default_store(" not in readme


def test_model_example_uses_bind_path():
    example = Path("examples/model_mixin.py").read_text()

    assert ".bind(store)" in example
```

- [ ] **Step 2: Run the documentation expectation tests to verify they fail**

Run: `uv run pytest tests/test_examples.py -q`
Expected: FAIL because current docs/examples still teach the old primary path

- [ ] **Step 3: Rewrite the public teaching path around `Model.bind(store)`**

```markdown
<!-- README.md -->
### Model Binding

```python
from typed_store import SyncTypedStore, TypedStoreModel

store = SyncTypedStore.from_url("sqlite:///app.db")

class User(Base, TypedStoreModel):
    ...

users = User.bind(store)
users.find_many(User.role == "admin")
users.get(1)
```
```

```markdown
<!-- docs/api-surface.md -->
## 1. Primary entry points

- `SyncTypedStore` — sync primary store implementation
- `AsyncTypedStore` — async primary store implementation
- `TypedStoreModel.bind(store)` — primary model-first entry point

## 5. Bound model views

`User.bind(store)` returns a bound model view that exposes typed model operations without implicit global store state.
```

```markdown
<!-- docs/design-spec.md -->
## Implementation Status

- `v0.2` primary path: `Model.bind(store)`
- `TypedStore` retains compatibility status only and is no longer the recommended sync facade
- global default store APIs are deprecated compatibility paths
```

```python
# examples/model_mixin.py
from typed_store import SyncTypedStore, TypedStoreModel

store = SyncTypedStore.from_url("sqlite:///model_bind.sqlite3")


class User(Base, TypedStoreModel):
    __tablename__ = "users"


bound_users = User.bind(store)
bound_users.insert(User(name="alice"))
print([user.name for user in bound_users.find_many()])
```

```markdown
<!-- docs/internal/progress.md -->
## Next

- 实现 `Model.bind(store)` 作为主公开路径并为旧全局绑定 API 增加弃用策略
- 为 `SyncTypedStore` / `AsyncTypedStore` 补生命周期 API
```

- [ ] **Step 4: Run smoke tests and the full quality gate**

Run: `uv run pytest tests/test_examples.py -q`
Expected: PASS for updated docs/example expectations and example smoke coverage

Run: `uv run pytest`
Expected: PASS for the full suite

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run ruff format --check .`
Expected: PASS

Run: `uv run ty check`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/api-surface.md docs/design-spec.md docs/internal/progress.md examples/model_mixin.py tests/test_examples.py
git commit -m "docs: teach bind-first public SDK path"
```

## Self-Review Checklist

- Every `v0.2` requirement from the design spec maps to at least one task above
- No task depends on capability protocol extraction or `QuerySpec` replacement
- `Model.bind(store)` is the only new model-first primary path in the plan
- Global default store behavior is deprecated but not removed in `v0.2`
- `TypedStore` remains a composition root but stops being taught as the main sync facade

## Follow-Up Plans

After this plan is implemented and validated, create separate plans for:

- `v0.3` capability protocol extraction and spec split
- `v1.0` compatibility cleanup and final public API stabilization
