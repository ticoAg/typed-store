from __future__ import annotations

from typing import cast

import pytest

import typed_store
from tests.conftest import Widget
from typed_store import AsyncTypedStore, QuerySpec, SessionProvider, SyncTypedStore
from typed_store.errors import (
    InvalidStoreBindingError,
    MissingAsyncSessionFactoryError,
    MissingSyncSessionFactoryError,
    ProjectionPaginationError,
)


def test_missing_sync_session_factory_raises():
    provider = SessionProvider()
    store = SyncTypedStore(provider)

    with pytest.raises(MissingSyncSessionFactoryError):
        store.find_many(Widget)


@pytest.mark.asyncio
async def test_missing_async_session_factory_raises():
    provider = SessionProvider()
    store = AsyncTypedStore(provider)

    with pytest.raises(MissingAsyncSessionFactoryError):
        await store.find_many(Widget)


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


def test_sync_paginate_rejects_projection(store):
    spec = QuerySpec[Widget]().select_columns(Widget.id).paginate(limit=10, offset=0)

    with pytest.raises(ProjectionPaginationError):
        store.sync.paginate(Widget, spec=spec)


@pytest.mark.asyncio
async def test_async_paginate_rejects_projection(store):
    spec = QuerySpec[Widget]().select_columns(Widget.id).paginate(limit=10, offset=0)

    with pytest.raises(ProjectionPaginationError):
        await store.async_.paginate(Widget, spec=spec)
