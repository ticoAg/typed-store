"""Tests for simplified API: from_url, inline filters, model-bound views, TypedStore delegation."""

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
from typed_store.model_store import AsyncModelStore, SyncModelStore

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

        ts.insert(Widget(name="alice", category="a"))
        rows = ts.find_many(Widget)
        assert len(rows) == 1

    def test_both_urls(self, tmp_path: Path):
        db = tmp_path / "test.sqlite"
        ts = TypedStore.from_url(
            f"sqlite:///{db}",
            async_url=f"sqlite+aiosqlite:///{db}",
        )
        assert ts.engine is not None
        assert ts.async_engine is not None


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
# Model-bound sub-views (store.of)
# ---------------------------------------------------------------------------


class TestSyncModelStore:
    def test_of_returns_model_store(self, store):
        widgets = store.sync.of(Widget)
        assert isinstance(widgets, SyncModelStore)

    def test_insert_and_find_many(self, store):
        widgets = store.sync.of(Widget)
        widgets.insert(Widget(name="alice", category="a"))
        rows = widgets.find_many()
        assert len(rows) == 1
        assert rows[0].name == "alice"

    def test_get_by_id(self, store):
        widgets = store.sync.of(Widget)
        w = widgets.insert(Widget(name="alice", category="a"))
        found = widgets.get(w.id)
        assert found is not None
        assert found.name == "alice"

    def test_find_many_with_filter(self, store):
        widgets = store.sync.of(Widget)
        widgets.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="y"),
            ]
        )
        rows = widgets.find_many(Widget.category == "x")
        assert len(rows) == 1

    def test_find_one(self, store):
        widgets = store.sync.of(Widget)
        widgets.insert(Widget(name="alice", category="a"))
        found = widgets.find_one(Widget.name == "alice")
        assert found is not None

    def test_paginate(self, store):
        widgets = store.sync.of(Widget)
        widgets.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
            ]
        )
        page = widgets.paginate(Widget.category == "x", limit=10, offset=0)
        assert page.total == 2

    def test_delete_where(self, store):
        widgets = store.sync.of(Widget)
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
        widgets = store.sync.of(Widget)
        widgets.insert(Widget(name="a", category="old"))
        updated = widgets.update_fields({"category": "new"}, Widget.name == "a")
        assert updated == 1


class TestAsyncModelStore:
    @pytest.mark.asyncio
    async def test_of_returns_model_store(self, store):
        widgets = store.async_.of(Widget)
        assert isinstance(widgets, AsyncModelStore)

    @pytest.mark.asyncio
    async def test_insert_and_find_many(self, store):
        widgets = store.async_.of(Widget)
        await widgets.insert(Widget(name="alice", category="a"))
        rows = await widgets.find_many()
        assert len(rows) == 1
        assert rows[0].name == "alice"

    @pytest.mark.asyncio
    async def test_get_by_id(self, store):
        widgets = store.async_.of(Widget)
        w = await widgets.insert(Widget(name="alice", category="a"))
        found = await widgets.get(w.id)
        assert found is not None
        assert found.name == "alice"


# ---------------------------------------------------------------------------
# TypedStore sync delegation
# ---------------------------------------------------------------------------


class TestTypedStoreDelegation:
    def test_insert_and_find_many(self, store):
        store.insert(Widget(name="alice", category="a"))
        rows = store.find_many(Widget)
        assert len(rows) == 1

    def test_find_many_with_filter(self, store):
        store.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="y"),
            ]
        )
        rows = store.find_many(Widget, Widget.category == "x")
        assert len(rows) == 1

    def test_get_by_id(self, store):
        w = store.insert(Widget(name="alice", category="a"))
        found = store.get(Widget, w.id)
        assert found is not None
        assert found.name == "alice"

    def test_find_one(self, store):
        store.insert(Widget(name="alice", category="a"))
        found = store.find_one(Widget, Widget.name == "alice")
        assert found is not None

    def test_paginate(self, store):
        store.insert_many(
            [
                Widget(name="a", category="x"),
                Widget(name="b", category="x"),
            ]
        )
        page = store.paginate(Widget, Widget.category == "x", limit=10, offset=0)
        assert page.total == 2

    def test_delete_where(self, store):
        store.insert_many(
            [
                Widget(name="a", category="del"),
                Widget(name="b", category="keep"),
            ]
        )
        deleted = store.delete_where(Widget, Widget.category == "del")
        assert deleted == 1

    def test_update_fields(self, store):
        store.insert(Widget(name="a", category="old"))
        updated = store.update_fields(Widget, {"category": "new"}, Widget.name == "a")
        assert updated == 1

    def test_of_returns_sync_model_store(self, store):
        widgets = store.of(Widget)
        assert isinstance(widgets, SyncModelStore)
        widgets.insert(Widget(name="via-of", category="z"))
        assert len(widgets.find_many()) == 1
