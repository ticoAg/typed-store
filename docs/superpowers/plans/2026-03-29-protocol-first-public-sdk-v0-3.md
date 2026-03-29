# Protocol-First Public SDK v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the remaining facade-centric query surface with protocol-first store capabilities and explicit request objects by introducing capability protocols, `Query`/`PageRequest`/`Patch`/`ProjectionQuery`, and removing `QuerySpec` entirely.

**Architecture:** This plan assumes the `v0.2` bind-first API is already merged. `v0.3` keeps the current SQLAlchemy adapters but changes their public contracts: stores implement explicit capability protocols, bound model views route through those protocols, and every query or mutation is driven by dedicated immutable request objects rather than inline filters or `QuerySpec`.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.x, pytest, pytest-asyncio, ruff, ty

---

## Scope

This plan covers the approved `v0.3` slice only:

- Add capability protocols for read/write/update/delete/transaction/statement execution
- Add explicit spec objects: `Query[T]`, `PageRequest`, `Patch[T]`, `ProjectionQuery[R]`
- Move sync/async store APIs and bound model APIs to the new spec-driven contracts
- Remove `QuerySpec` and all inline-filter public method signatures
- Update examples, docs, and tests to teach only the new protocol-first API

This plan explicitly does **not** include:

- `v1.0` cleanup of any future transitional names that survive `v0.3`
- New backend adapters beyond SQLAlchemy
- SQL cursor pagination
- SQL-level bulk mutation optimization beyond what is needed to preserve current behavior

Because the user explicitly requested “只保留当前设计的最佳的实现”, this plan does **not** introduce a compatibility layer for `QuerySpec` or inline filters.

## File Structure

### Create

- `typed_store/specs.py`
- `typed_store/protocols.py`
- `tests/test_specs.py`
- `tests/test_protocols.py`

### Delete

- `typed_store/query_spec.py`

### Modify

- `typed_store/__init__.py`
- `typed_store/bound_model.py`
- `typed_store/sync.py`
- `typed_store/async_store.py`
- `typed_store/store.py`
- `typed_store/model_store.py`
- `tests/test_sync_store.py`
- `tests/test_async_store.py`
- `tests/test_shortcuts.py`
- `tests/test_error_boundaries.py`
- `tests/test_examples.py`
- `examples/sync_basic.py`
- `examples/async_basic.py`
- `examples/repository_pattern.py`
- `examples/async_repository_pattern.py`
- `examples/model_mixin.py`
- `examples/model_store_view.py`
- `README.md`
- `docs/api-surface.md`
- `docs/design-spec.md`
- `docs/internal/progress.md`

### Responsibilities

- `typed_store/specs.py`: immutable request objects and SQLAlchemy select builders
- `typed_store/protocols.py`: runtime-checkable capability protocols used as public contracts
- `typed_store/sync.py` / `typed_store/async_store.py`: SQLAlchemy-backed implementations of those protocols
- `typed_store/bound_model.py`: model-bound capability views driven by the new request objects
- `typed_store/model_store.py`: removal of legacy `store.of()` surface
- tests/examples/docs: move all usage to protocol-first API

## Public API Decisions Locked By This Plan

- `QuerySpec` is removed, not deprecated
- Inline public filter signatures such as `find_many(Model, Model.name == "alice")` are removed from the public surface
- Public read methods take `query=Query[T](...)`
- Public pagination takes both `query=...` and `page=PageRequest(...)`
- Public mutation methods take `patch=Patch[T](...)`
- Bound model views remain the only model-first path, and they also consume the new request objects

## Task 1: Introduce Request Objects And Remove `QuerySpec`

**Files:**
- Create: `typed_store/specs.py`
- Delete: `typed_store/query_spec.py`
- Modify: `typed_store/__init__.py`
- Test: `tests/test_specs.py`

- [ ] **Step 1: Write failing tests for the new request objects**

```python
from __future__ import annotations

from tests.conftest import Widget
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


def test_query_builder_is_immutable():
    query = Query[Widget]().where(Widget.category == "a").order(Widget.id.asc()).limit_to(5).offset_by(2)

    assert len(query.filters) == 1
    assert len(query.order_by) == 1
    assert query.limit == 5
    assert query.offset == 2


def test_page_request_and_patch_store_boundary_inputs():
    page = PageRequest(limit=10, offset=20)
    patch = Patch[Widget]({"category": "updated"})

    assert page.limit == 10
    assert page.offset == 20
    assert patch.values == {"category": "updated"}


def test_projection_query_tracks_columns_and_filters():
    projection = (
        ProjectionQuery[tuple[int, str]](Widget.id, Widget.name)
        .where(Widget.category == "a")
        .order(Widget.id.asc())
    )

    assert projection.columns == (Widget.id, Widget.name)
    assert len(projection.filters) == 1
    assert len(projection.order_by) == 1
```

- [ ] **Step 2: Run the new request-object tests to verify they fail**

Run: `uv run pytest tests/test_specs.py -q`
Expected: FAIL because `typed_store.specs` does not exist and `QuerySpec` is still the only request object

- [ ] **Step 3: Implement immutable request objects and remove `QuerySpec`**

```python
# typed_store/specs.py
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from sqlalchemy import ColumnExpressionArgument, Select, select
from sqlalchemy.orm.interfaces import ORMOption

type FilterClause = ColumnExpressionArgument[bool]
type OrderClause = ColumnExpressionArgument[object]
type ProjectionClause = ColumnExpressionArgument[object]
type LoaderOption = ORMOption


@dataclass(slots=True, frozen=True)
class Query[TModel]:
    filters: tuple[FilterClause, ...] = field(default_factory=tuple)
    order_by: tuple[OrderClause, ...] = field(default_factory=tuple)
    limit: int | None = None
    offset: int | None = None
    options: tuple[LoaderOption, ...] = field(default_factory=tuple)

    def where(self, *filters: FilterClause) -> Query[TModel]:
        return replace(self, filters=self.filters + tuple(filters))

    def order(self, *clauses: OrderClause) -> Query[TModel]:
        return replace(self, order_by=self.order_by + tuple(clauses))

    def limit_to(self, limit: int | None) -> Query[TModel]:
        return replace(self, limit=limit)

    def offset_by(self, offset: int | None) -> Query[TModel]:
        return replace(self, offset=offset)

    def with_options(self, *options: LoaderOption) -> Query[TModel]:
        return replace(self, options=self.options + tuple(options))

    def build_select(self, model: type[TModel]) -> Select[Any]:
        stmt = select(model)
        if self.filters:
            stmt = stmt.where(*self.filters)
        if self.order_by:
            stmt = stmt.order_by(*self.order_by)
        if self.offset is not None:
            stmt = stmt.offset(self.offset)
        if self.limit is not None:
            stmt = stmt.limit(self.limit)
        if self.options:
            stmt = stmt.options(*self.options)
        return stmt

    def count_select(self, model: type[TModel]) -> Select[Any]:
        stmt = select(model)
        if self.filters:
            stmt = stmt.where(*self.filters)
        return stmt


@dataclass(slots=True, frozen=True)
class PageRequest:
    limit: int
    offset: int = 0


@dataclass(slots=True, frozen=True)
class Patch[TModel]:
    values: Mapping[str, object]


@dataclass(slots=True, frozen=True)
class ProjectionQuery[TRow]:
    columns: tuple[ProjectionClause, ...]
    filters: tuple[FilterClause, ...] = field(default_factory=tuple)
    order_by: tuple[OrderClause, ...] = field(default_factory=tuple)
    options: tuple[LoaderOption, ...] = field(default_factory=tuple)

    def __init__(self, *columns: ProjectionClause):
        object.__setattr__(self, "columns", tuple(columns))
        object.__setattr__(self, "filters", ())
        object.__setattr__(self, "order_by", ())
        object.__setattr__(self, "options", ())

    def where(self, *filters: FilterClause) -> ProjectionQuery[TRow]:
        return replace(self, filters=self.filters + tuple(filters))

    def order(self, *clauses: OrderClause) -> ProjectionQuery[TRow]:
        return replace(self, order_by=self.order_by + tuple(clauses))

    def with_options(self, *options: LoaderOption) -> ProjectionQuery[TRow]:
        return replace(self, options=self.options + tuple(options))

    def build_select(self, model: type[object]) -> Select[Any]:
        stmt = select(*self.columns).select_from(model)  # ty: ignore[no-matching-overload]
        if self.filters:
            stmt = stmt.where(*self.filters)
        if self.order_by:
            stmt = stmt.order_by(*self.order_by)
        if self.options:
            stmt = stmt.options(*self.options)
        return stmt
```

```python
# typed_store/__init__.py
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query

__all__ = [
    "PageRequest",
    "Patch",
    "ProjectionQuery",
    "Query",
]
```

Run delete: `rm typed_store/query_spec.py`

- [ ] **Step 4: Run the request-object tests again**

Run: `uv run pytest tests/test_specs.py -q`
Expected: PASS for immutable `Query`, `PageRequest`, `Patch`, and `ProjectionQuery`

- [ ] **Step 5: Commit**

```bash
git add typed_store/specs.py typed_store/__init__.py tests/test_specs.py
git rm typed_store/query_spec.py
git commit -m "feat: replace QuerySpec with explicit request objects"
```

### Task 2: Add Capability Protocols And Make The Sync Store Conform

**Files:**
- Create: `typed_store/protocols.py`
- Modify: `typed_store/sync.py`
- Modify: `typed_store/__init__.py`
- Test: `tests/test_protocols.py`
- Test: `tests/test_sync_store.py`

- [ ] **Step 1: Write failing protocol and sync-store tests**

```python
from __future__ import annotations

from tests.conftest import Widget
from typed_store import PageRequest, Patch, Query
from typed_store.protocols import (
    DeletableStoreProtocol,
    PatchableStoreProtocol,
    ReadableStoreProtocol,
    WritableStoreProtocol,
)


def test_sync_store_implements_runtime_protocols(store):
    assert isinstance(store.sync, ReadableStoreProtocol)
    assert isinstance(store.sync, WritableStoreProtocol)
    assert isinstance(store.sync, PatchableStoreProtocol)
    assert isinstance(store.sync, DeletableStoreProtocol)


def test_sync_store_uses_query_page_and_patch_objects(store):
    store.sync.insert_many(
        [
            Widget(name="alpha", category="a"),
            Widget(name="beta", category="b"),
            Widget(name="gamma", category="a"),
        ]
    )

    query = Query[Widget]().where(Widget.category == "a").order(Widget.id.asc())
    page = PageRequest(limit=1, offset=0)
    patch = Patch[Widget]({"category": "updated"})

    assert store.sync.exists(Widget, query=query) is True
    assert store.sync.count(Widget, query=query) == 2
    assert [item.name for item in store.sync.find_many(Widget, query=query)] == ["alpha", "gamma"]
    assert [item.name for item in store.sync.paginate(Widget, query=query, page=page).items] == ["alpha"]
    assert store.sync.update(Widget, query=Query[Widget]().where(Widget.name == "alpha"), patch=patch) == 1
    assert store.sync.delete(Widget, query=Query[Widget]().where(Widget.category == "updated")) == 1
```

- [ ] **Step 2: Run the protocol and sync-store tests to verify they fail**

Run: `uv run pytest tests/test_protocols.py tests/test_sync_store.py -q`
Expected: FAIL because capability protocols and spec-driven sync methods do not exist yet

- [ ] **Step 3: Add runtime-checkable protocols and rewrite the sync store surface**

```python
# typed_store/protocols.py
from __future__ import annotations

from typing import Protocol, runtime_checkable

from typed_store.results import Page
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


@runtime_checkable
class ReadableStoreProtocol[TModel](Protocol):
    def get(self, model: type[TModel], ident: object, /, *, session: object | None = None) -> TModel | None: ...
    def find_one(self, model: type[TModel], /, *, query: Query[TModel], session: object | None = None) -> TModel | None: ...
    def find_many(self, model: type[TModel], /, *, query: Query[TModel], session: object | None = None) -> list[TModel]: ...
    def exists(self, model: type[TModel], /, *, query: Query[TModel], session: object | None = None) -> bool: ...
    def count(self, model: type[TModel], /, *, query: Query[TModel], session: object | None = None) -> int: ...
    def paginate(self, model: type[TModel], /, *, query: Query[TModel], page: PageRequest, session: object | None = None) -> Page[TModel]: ...


@runtime_checkable
class WritableStoreProtocol[TModel](Protocol):
    def insert(self, entity: TModel, /, *, session: object | None = None, commit: bool = True, refresh: bool = False) -> TModel: ...
    def insert_many(self, entities: list[TModel] | tuple[TModel, ...], /, *, session: object | None = None, commit: bool = True) -> list[TModel]: ...


@runtime_checkable
class PatchableStoreProtocol[TModel](Protocol):
    def update(self, model: type[TModel], /, *, query: Query[TModel], patch: Patch[TModel], session: object | None = None, commit: bool = True) -> int: ...


@runtime_checkable
class DeletableStoreProtocol[TModel](Protocol):
    def delete(self, model: type[TModel], /, *, query: Query[TModel], session: object | None = None, commit: bool = True) -> int: ...


@runtime_checkable
class StatementExecutorProtocol(Protocol):
    def select_rows[TRow](self, model: type[object], /, *, projection: ProjectionQuery[TRow], session: object | None = None) -> list[TRow]: ...


@runtime_checkable
class TransactionalStoreProtocol(Protocol):
    def unit_of_work(self, *, auto_commit: bool = True) -> object: ...
```

```python
# typed_store/sync.py
from typed_store.protocols import (
    DeletableStoreProtocol,
    PatchableStoreProtocol,
    ReadableStoreProtocol,
    StatementExecutorProtocol,
    TransactionalStoreProtocol,
    WritableStoreProtocol,
)
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


class SyncTypedStore[TModel](
    ReadableStoreProtocol[TModel],
    WritableStoreProtocol[TModel],
    PatchableStoreProtocol[TModel],
    DeletableStoreProtocol[TModel],
    StatementExecutorProtocol,
    TransactionalStoreProtocol,
):
    def find_one(self, model: type[TModel], *, query: Query[TModel], session: Session | None = None) -> TModel | None:
        stmt = query.limit_to(1).offset_by(0).build_select(model)
        ...

    def find_many(self, model: type[TModel], *, query: Query[TModel], session: Session | None = None) -> list[TModel]:
        stmt = query.build_select(model)
        ...

    def exists(self, model: type[TModel], *, query: Query[TModel], session: Session | None = None) -> bool:
        return self.count(model, query=query, session=session) > 0

    def count(self, model: type[TModel], *, query: Query[TModel], session: Session | None = None) -> int:
        count_stmt = select(func.count()).select_from(query.count_select(model).subquery())
        ...

    def paginate(self, model: type[TModel], *, query: Query[TModel], page: PageRequest, session: Session | None = None) -> Page[TModel]:
        paged_query = query.limit_to(page.limit).offset_by(page.offset)
        ...

    def update(self, model: type[TModel], *, query: Query[TModel], patch: Patch[TModel], session: Session | None = None, commit: bool = True) -> int:
        items = self.find_many(model, query=query, session=session)
        for item in items:
            for key, value in patch.values.items():
                setattr(item, key, value)
        ...

    def delete(self, model: type[TModel], *, query: Query[TModel], session: Session | None = None, commit: bool = True) -> int:
        items = self.find_many(model, query=query, session=session)
        ...

    def select_rows[TRow](self, model: type[object], *, projection: ProjectionQuery[TRow], session: Session | None = None) -> list[TRow]:
        stmt = projection.build_select(model)
        ...
```

- [ ] **Step 4: Run the protocol and sync-store tests again**

Run: `uv run pytest tests/test_protocols.py tests/test_sync_store.py -q`
Expected: PASS with `SyncTypedStore` conforming to runtime protocols and using `Query`/`PageRequest`/`Patch`

- [ ] **Step 5: Commit**

```bash
git add typed_store/protocols.py typed_store/sync.py typed_store/__init__.py tests/test_protocols.py tests/test_sync_store.py
git commit -m "feat: add protocol-first sync store contracts"
```

### Task 3: Mirror The Protocol-First Surface In Async Stores And Bound Models

**Files:**
- Modify: `typed_store/async_store.py`
- Modify: `typed_store/bound_model.py`
- Modify: `typed_store/model.py`
- Test: `tests/test_async_store.py`
- Test: `tests/test_bound_model.py`

- [ ] **Step 1: Write failing async and bound-model tests**

```python
from __future__ import annotations

import pytest

from tests.conftest import Widget
from typed_store import PageRequest, Patch, Query


@pytest.mark.asyncio
async def test_async_store_uses_query_page_and_patch_objects(store):
    await store.async_.insert_many(
        [
            Widget(name="alpha", category="a"),
            Widget(name="beta", category="b"),
            Widget(name="gamma", category="a"),
        ]
    )

    query = Query[Widget]().where(Widget.category == "a").order(Widget.id.asc())

    assert await store.async_.exists(Widget, query=query) is True
    assert await store.async_.count(Widget, query=query) == 2
    assert [item.name for item in await store.async_.find_many(Widget, query=query)] == ["alpha", "gamma"]
    assert [item.name for item in (await store.async_.paginate(Widget, query=query, page=PageRequest(limit=1, offset=0))).items] == ["alpha"]
    assert await store.async_.update(
        Widget,
        query=Query[Widget]().where(Widget.name == "alpha"),
        patch=Patch[Widget]({"category": "updated"}),
    ) == 1


@pytest.mark.asyncio
async def test_bound_model_view_uses_query_objects(store):
    widgets = Widget.bind(store.async_)
    await widgets.insert(Widget(name="bound-alpha", category="bound"))

    rows = await widgets.find_many(query=Query[Widget]().where(Widget.category == "bound"))
    assert [row.name for row in rows] == ["bound-alpha"]
```

- [ ] **Step 2: Run the async and bound-model tests to verify they fail**

Run: `uv run pytest tests/test_async_store.py tests/test_bound_model.py -q`
Expected: FAIL because async methods and bound views still use the old inline query surface

- [ ] **Step 3: Rewrite async and bound-model methods to use protocol-first request objects**

```python
# typed_store/async_store.py
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


class AsyncTypedStore[TModel](...):
    async def find_one(self, model: type[TModel], *, query: Query[TModel], session: AsyncSession | None = None) -> TModel | None:
        stmt = query.limit_to(1).offset_by(0).build_select(model)
        ...

    async def find_many(self, model: type[TModel], *, query: Query[TModel], session: AsyncSession | None = None) -> list[TModel]:
        ...

    async def exists(self, model: type[TModel], *, query: Query[TModel], session: AsyncSession | None = None) -> bool:
        return await self.count(model, query=query, session=session) > 0

    async def count(self, model: type[TModel], *, query: Query[TModel], session: AsyncSession | None = None) -> int:
        ...

    async def paginate(self, model: type[TModel], *, query: Query[TModel], page: PageRequest, session: AsyncSession | None = None) -> Page[TModel]:
        ...

    async def update(self, model: type[TModel], *, query: Query[TModel], patch: Patch[TModel], session: AsyncSession | None = None, commit: bool = True) -> int:
        ...

    async def delete(self, model: type[TModel], *, query: Query[TModel], session: AsyncSession | None = None, commit: bool = True) -> int:
        ...
```

```python
# typed_store/bound_model.py
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


class SyncBoundModelView[TModel]:
    def find_one(self, *, query: Query[TModel], session: Session | None = None) -> TModel | None:
        return cast(TModel | None, self._store.find_one(self._model, query=query, session=session))

    def find_many(self, *, query: Query[TModel], session: Session | None = None) -> list[TModel]:
        return cast(list[TModel], self._store.find_many(self._model, query=query, session=session))

    def exists(self, *, query: Query[TModel], session: Session | None = None) -> bool:
        return self._store.exists(self._model, query=query, session=session)

    def count(self, *, query: Query[TModel], session: Session | None = None) -> int:
        return self._store.count(self._model, query=query, session=session)

    def paginate(self, *, query: Query[TModel], page: PageRequest, session: Session | None = None) -> Page[TModel]:
        return cast(Page[TModel], self._store.paginate(self._model, query=query, page=page, session=session))

    def update(self, *, query: Query[TModel], patch: Patch[TModel], session: Session | None = None, commit: bool = True) -> int:
        return self._store.update(self._model, query=query, patch=patch, session=session, commit=commit)

    def delete(self, *, query: Query[TModel], session: Session | None = None, commit: bool = True) -> int:
        return self._store.delete(self._model, query=query, session=session, commit=commit)
```

```python
# typed_store/model.py
class TypedStoreModel:
    # keep bind(store) only; no new implicit state helpers added here
    ...
```

- [ ] **Step 4: Run the async and bound-model suites again**

Run: `uv run pytest tests/test_async_store.py tests/test_bound_model.py -q`
Expected: PASS with async stores and bound model views using the new request objects exclusively

- [ ] **Step 5: Commit**

```bash
git add typed_store/async_store.py typed_store/bound_model.py typed_store/model.py tests/test_async_store.py tests/test_bound_model.py
git commit -m "feat: move async stores and bound views to protocol-first requests"
```

### Task 4: Update Public Docs, Examples, And Remaining Tests To The New Surface

**Files:**
- Modify: `tests/test_shortcuts.py`
- Modify: `tests/test_error_boundaries.py`
- Modify: `tests/test_examples.py`
- Modify: `examples/sync_basic.py`
- Modify: `examples/async_basic.py`
- Modify: `examples/repository_pattern.py`
- Modify: `examples/async_repository_pattern.py`
- Modify: `examples/model_mixin.py`
- Modify: `examples/model_store_view.py`
- Modify: `README.md`
- Modify: `docs/api-surface.md`
- Modify: `docs/design-spec.md`
- Modify: `docs/internal/progress.md`

- [ ] **Step 1: Write failing tests that lock the new public API shape**

```python
from pathlib import Path


def test_readme_teaches_query_and_bind_first():
    readme = Path("README.md").read_text()

    assert "User.bind(store)" in readme
    assert "Query[" in readme
    assert "PageRequest(" in readme
    assert "QuerySpec" not in readme


def test_examples_no_longer_use_queryspec():
    example = Path("examples/sync_basic.py").read_text()

    assert "Query[" in example
    assert "QuerySpec" not in example
```

- [ ] **Step 2: Run the docs/example tests to verify they fail**

Run: `uv run pytest tests/test_examples.py -q`
Expected: FAIL because docs/examples still teach `QuerySpec` or inline-filter signatures

- [ ] **Step 3: Rewrite docs, examples, and remaining tests to the new contracts**

```python
# examples/sync_basic.py
from typed_store import PageRequest, Query, SyncTypedStore

store = SyncTypedStore.from_url("sqlite:///sync_basic.sqlite3")
query = Query[User]().where(User.role == "admin").order(User.id.asc())
page = PageRequest(limit=10, offset=0)

store.insert(User(name="alice"))
rows = store.find_many(User, query=query)
page_result = store.paginate(User, query=query, page=page)
```

```python
# examples/model_mixin.py
from typed_store import PageRequest, Patch, Query, SyncTypedStore, TypedStoreModel

users = User.bind(store)
admins = users.find_many(query=Query[User]().where(User.role == "admin").order(User.name.asc()))
page = users.paginate(query=Query[User]().where(User.role == "admin"), page=PageRequest(limit=2, offset=0))
updated = users.update(query=Query[User]().where(User.name == "alice"), patch=Patch[User]({"role": "superadmin"}))
deleted = users.delete(query=Query[User]().where(User.role == "member"))
```

```markdown
<!-- README.md -->
### Model Binding

```python
from typed_store import PageRequest, Query, SyncTypedStore, TypedStoreModel

store = SyncTypedStore.from_url("sqlite:///app.db")

class User(Base, TypedStoreModel):
    ...

users = User.bind(store)
query = Query[User]().where(User.role == "admin").order(User.id.asc())
page = PageRequest(limit=10, offset=0)

users.find_many(query=query)
users.paginate(query=query, page=page)
```
```

```markdown
<!-- docs/internal/progress.md -->
## Next

- 推进 `v1.0` 最终 public API 稳定与 compatibility policy
- 评估 SQL 级 bulk update/delete 的最终语义
```

- [ ] **Step 4: Run the public-surface verification commands**

Run: `uv run pytest tests/test_examples.py tests/test_shortcuts.py tests/test_error_boundaries.py -q`
Expected: PASS with docs/examples/tests using `Query`, `PageRequest`, `Patch`, and `Model.bind(store)` only

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
git add README.md docs/api-surface.md docs/design-spec.md docs/internal/progress.md examples/sync_basic.py examples/async_basic.py examples/repository_pattern.py examples/async_repository_pattern.py examples/model_mixin.py examples/model_store_view.py tests/test_shortcuts.py tests/test_error_boundaries.py tests/test_examples.py
git commit -m "docs: teach protocol-first query and capability API"
```

## Self-Review Checklist

- `QuerySpec` removal is covered by Task 1 and not deferred
- Sync capability protocols are introduced and verified in Task 2
- Async stores and bound model views are migrated in Task 3
- Docs, examples, and test suites are aligned to the new API in Task 4
- No task relies on a compatibility layer for inline filters or `QuerySpec`

## Follow-Up Plans

After this plan lands, the next plan should cover only the remaining `v1.0` stabilization work:

- final naming cleanup if any transitional terms remain
- explicit compatibility policy documentation
- final SQL mutation semantics
