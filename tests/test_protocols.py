from __future__ import annotations

from tests.conftest import Widget
from typed_store import PageRequest, Patch, Query
from typed_store.protocols import (
    AsyncDeletableStoreProtocol,
    AsyncPatchableStoreProtocol,
    AsyncReadableStoreProtocol,
    AsyncWritableStoreProtocol,
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


def test_async_store_implements_runtime_protocols(store):
    assert isinstance(store.async_, AsyncReadableStoreProtocol)
    assert isinstance(store.async_, AsyncWritableStoreProtocol)
    assert isinstance(store.async_, AsyncPatchableStoreProtocol)
    assert isinstance(store.async_, AsyncDeletableStoreProtocol)


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
    assert [item.name for item in store.sync.paginate(Widget, query=query, page=page).items] == [
        "alpha"
    ]
    assert (
        store.sync.update(
            Widget,
            query=Query[Widget]().where(Widget.name == "alpha"),
            patch=patch,
        )
        == 1
    )
    assert (
        store.sync.delete(
            Widget,
            query=Query[Widget]().where(Widget.category == "updated"),
        )
        == 1
    )
