"""Tests for store shortcuts, bind-first model usage, and composition roots."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import Base, Widget
from typed_store import (
    AsyncTypedStore,
    QuerySpec,
    SyncTypedStore,
    TypedStore,
)

# ---------------------------------------------------------------------------
# from_url factory methods
# ---------------------------------------------------------------------------


class TestSyncFromUrl:
    def test_creates_working_store(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        store = SyncTypedStore.from_url(f"sqlite:///{db}")
        assert store.engine is not None
        Base.metadata.create_all(store.engine)

        store.insert(Widget(name="alice", category="a"))
        rows = store.find_many(Widget)
        assert len(rows) == 1
        assert rows[0].name == "alice"

    def test_engine_property(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        store = SyncTypedStore.from_url(f"sqlite:///{db}")
        assert store.engine is not None

    def test_engine_none_when_not_from_url(self, provider):
        store = SyncTypedStore(provider)
        assert store.engine is None


class TestAsyncFromUrl:
    @pytest.mark.asyncio
    async def test_creates_working_store(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        store = AsyncTypedStore.from_url(f"sqlite+aiosqlite:///{db}")
        assert store.engine is not None
        async with store.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await store.insert(Widget(name="alice", category="a"))
        rows = await store.find_many(Widget)
        assert len(rows) == 1
        assert rows[0].name == "alice"
        await store.engine.dispose()


class TestTypedStoreFromUrl:
    def test_sync_only(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        ts = TypedStore.from_url(f"sqlite:///{db}")
        assert ts.engine is not None
        Base.metadata.create_all(ts.engine)

        ts.sync.insert(Widget(name="alice", category="a"))
        rows = ts.sync.find_many(Widget)
        assert len(rows) == 1

    def test_both_urls(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        ts = TypedStore.from_url(
            f"sqlite:///{db}",
            async_url=f"sqlite+aiosqlite:///{db}",
        )
        assert ts.engine is not None
        assert ts.async_engine is not None


class TestLifecycleApis:
    def test_sync_store_close_is_idempotent(self, tmp_path: Path):
        db = tmp_path / "lifecycle.sqlite"
        store = SyncTypedStore.from_url(f"sqlite:///{db}")

        store.close()
        store.dispose()

        assert store.engine is not None

    @pytest.mark.asyncio
    async def test_async_store_aclose_is_idempotent(self, tmp_path: Path):
        db = tmp_path / "lifecycle.sqlite"
        store = AsyncTypedStore.from_url(f"sqlite+aiosqlite:///{db}")

        await store.aclose()
        await store.dispose()

        assert store.engine is not None

    @pytest.mark.asyncio
    async def test_typed_store_closes_both_engines(self, tmp_path: Path):
        db = tmp_path / "typed-store.sqlite"
        store = TypedStore.from_url(
            f"sqlite:///{db}",
            async_url=f"sqlite+aiosqlite:///{db}",
        )

        store.close()
        await store.aclose()

        assert store.engine is not None
        assert store.async_engine is not None


# ---------------------------------------------------------------------------
# Inline filter parameters
# ---------------------------------------------------------------------------


class TestInlineFilters:
    def test_find_many_with_filter(self, store):
        store.sync.insert_many(
            [
                Widget(name="alice", category="a"),
                Widget(name="bob", category="b"),
                Widget(name="carol", category="a"),
            ]
        )

        rows = store.sync.find_many(Widget, Widget.category == "a")
        assert len(rows) == 2

    def test_find_many_with_order(self, store):
        store.sync.insert_many(
            [
                Widget(name="bob", category="a"),
                Widget(name="alice", category="a"),
            ]
        )

        rows = store.sync.find_many(Widget, Widget.category == "a", order=Widget.name.asc())
        assert [r.name for r in rows] == ["alice", "bob"]

    def test_find_many_with_limit_offset(self, store):
        store.sync.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
                Widget(name="c", category="x"),
            ]
        )

        rows = store.sync.find_many(
            Widget, Widget.category == "x", order=Widget.id.asc(), limit=2, offset=1
        )
        assert [r.name for r in rows] == ["b", "c"]

    def test_find_one_with_filter(self, store):
        store.sync.insert_many(
            [
                Widget(name="alice", category="a"),
                Widget(name="bob", category="b"),
            ]
        )

        found = store.sync.find_one(Widget, Widget.name == "bob")
        assert found is not None
        assert found.category == "b"

    def test_paginate_with_inline_params(self, store):
        store.sync.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
                Widget(name="c", category="y"),
            ]
        )

        page = store.sync.paginate(
            Widget, Widget.category == "x", order=Widget.id.asc(), limit=1, offset=0
        )
        assert page.total == 2
        assert len(page.items) == 1
        assert page.items[0].name == "a"

    def test_delete_where_with_filter(self, store):
        store.sync.insert_many(
            [
                Widget(name="a", category="del"),
                Widget(name="b", category="keep"),
            ]
        )

        deleted = store.sync.delete_where(Widget, Widget.category == "del")
        assert deleted == 1
        assert len(store.sync.find_many(Widget)) == 1

    def test_update_fields_with_filter(self, store):
        store.sync.insert_many(
            [
                Widget(name="a", category="old"),
                Widget(name="b", category="old"),
            ]
        )

        updated = store.sync.update_fields(Widget, {"category": "new"}, Widget.name == "a")
        assert updated == 1
        found = store.sync.find_one(Widget, Widget.name == "a")
        assert found is not None
        assert found.category == "new"

    def test_filters_combined_with_spec(self, store):
        """Filters and spec= can coexist."""
        store.sync.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
                Widget(name="c", category="y"),
            ]
        )

        spec = QuerySpec[Widget]().order(Widget.id.asc())
        rows = store.sync.find_many(Widget, Widget.category == "x", spec=spec)
        assert len(rows) == 2
        assert rows[0].name == "a"


class TestAsyncInlineFilters:
    @pytest.mark.asyncio
    async def test_find_many_with_filter(self, store):
        await store.async_.insert_many(
            [
                Widget(name="alice", category="a"),
                Widget(name="bob", category="b"),
            ]
        )

        rows = await store.async_.find_many(Widget, Widget.category == "a")
        assert len(rows) == 1
        assert rows[0].name == "alice"

    @pytest.mark.asyncio
    async def test_paginate_with_inline_params(self, store):
        await store.async_.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
                Widget(name="c", category="y"),
            ]
        )

        page = await store.async_.paginate(Widget, Widget.category == "x", limit=10, offset=0)
        assert page.total == 2


# ---------------------------------------------------------------------------
# Bind-first model views
# ---------------------------------------------------------------------------


class TestSyncModelBinding:
    def test_bind_returns_bound_model_view(self, store):
        widgets = Widget.bind(store.sync)
        assert widgets.__class__.__name__ == "SyncBoundModelView"

    def test_insert_and_find_many(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert(Widget(name="alice", category="a"))
        rows = widgets.find_many()
        assert len(rows) == 1
        assert rows[0].name == "alice"

    def test_get_by_id(self, store):
        widgets = Widget.bind(store.sync)
        w = widgets.insert(Widget(name="alice", category="a"))
        found = widgets.get(w.id)
        assert found is not None
        assert found.name == "alice"

    def test_find_many_with_filter(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="y"),
            ]
        )
        rows = widgets.find_many(Widget.category == "x")
        assert len(rows) == 1

    def test_find_one(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert(Widget(name="alice", category="a"))
        found = widgets.find_one(Widget.name == "alice")
        assert found is not None

    def test_paginate(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
            ]
        )
        page = widgets.paginate(Widget.category == "x", limit=10, offset=0)
        assert page.total == 2

    def test_delete_where(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert_many(
            [
                Widget(name="a", category="del"),
                Widget(name="b", category="keep"),
            ]
        )
        deleted = widgets.delete_where(Widget.category == "del")
        assert deleted == 1
        assert len(widgets.find_many()) == 1

    def test_update_fields(self, store):
        widgets = Widget.bind(store.sync)
        widgets.insert(Widget(name="a", category="old"))
        updated = widgets.update_fields({"category": "new"}, Widget.name == "a")
        assert updated == 1


class TestAsyncModelBinding:
    @pytest.mark.asyncio
    async def test_bind_returns_bound_model_view(self, store):
        widgets = Widget.bind(store.async_)
        assert widgets.__class__.__name__ == "AsyncBoundModelView"

    @pytest.mark.asyncio
    async def test_insert_and_find_many(self, store):
        widgets = Widget.bind(store.async_)
        await widgets.insert(Widget(name="alice", category="a"))
        rows = await widgets.find_many()
        assert len(rows) == 1
        assert rows[0].name == "alice"

    @pytest.mark.asyncio
    async def test_get_by_id(self, store):
        widgets = Widget.bind(store.async_)
        w = await widgets.insert(Widget(name="alice", category="a"))
        found = await widgets.get(w.id)
        assert found is not None
        assert found.name == "alice"


# ---------------------------------------------------------------------------
# TypedStore composition root
# ---------------------------------------------------------------------------


class TestTypedStoreCompositionRoot:
    def test_exposes_sync_and_async_stores(self, store):
        assert isinstance(store.sync, SyncTypedStore)
        assert isinstance(store.async_, AsyncTypedStore)

    def test_has_no_direct_sync_crud_delegate(self, store):
        assert not hasattr(store, "find_many")
        assert not hasattr(store, "insert")

    def test_sync_and_async_stores_have_no_model_of_shortcut(self, store):
        assert not hasattr(store.sync, "of")
        assert not hasattr(store.async_, "of")
        assert not hasattr(store, "of")
