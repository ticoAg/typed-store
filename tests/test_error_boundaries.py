from __future__ import annotations

from typing import cast

import pytest

import typed_store
from tests.conftest import Widget
from typed_store import AsyncTypedStore, ProjectionQuery, Query, SessionProvider, SyncTypedStore
from typed_store.errors import (
    InvalidStoreBindingError,
    MissingAsyncSessionFactoryError,
    MissingSyncSessionFactoryError,
)


def test_missing_sync_session_factory_raises():
    provider = SessionProvider()
    store = SyncTypedStore(provider)

    with pytest.raises(MissingSyncSessionFactoryError):
        store.find_many(Widget, query=Query[Widget]())


@pytest.mark.asyncio
async def test_missing_async_session_factory_raises():
    provider = SessionProvider()
    store = AsyncTypedStore(provider)

    with pytest.raises(MissingAsyncSessionFactoryError):
        await store.find_many(Widget, query=Query[Widget]())


def test_bind_rejects_invalid_sync_store_binding():
    with pytest.raises(InvalidStoreBindingError):
        Widget.bind(cast(SyncTypedStore[object], "bad-store"))


@pytest.mark.asyncio
async def test_bind_rejects_invalid_async_store_binding():
    with pytest.raises(InvalidStoreBindingError):
        Widget.bind(cast(AsyncTypedStore[object], "bad-store"))


def test_model_no_longer_exposes_implicit_store_methods():
    assert not hasattr(Widget, "find_many")
    assert not hasattr(Widget, "insert_many")
    assert not hasattr(Widget, "use_store")


def test_package_no_longer_exports_default_store_helpers():
    assert not hasattr(typed_store, "set_default_store")
    assert not hasattr(typed_store, "get_default_store")
    assert not hasattr(typed_store, "clear_default_store")


def test_select_rows_requires_projection_keyword(store):
    with pytest.raises(TypeError):
        store.sync.select_rows(Widget, Query[Widget]())


@pytest.mark.asyncio
async def test_async_select_rows_requires_projection_keyword(store):
    with pytest.raises(TypeError):
        await store.async_.select_rows(Widget, ProjectionQuery[tuple[int]](Widget.id))
