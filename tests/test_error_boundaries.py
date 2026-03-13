from __future__ import annotations

from typing import cast

import pytest

from tests.conftest import Widget
from typed_store import AsyncTypedStore, QuerySpec, SessionProvider, SyncTypedStore
from typed_store.errors import (
    InvalidStoreBindingError,
    MissingAsyncSessionFactoryError,
    MissingGlobalStoreError,
    MissingSyncSessionFactoryError,
    ProjectionPaginationError,
)
from typed_store.model import StoreBinding, clear_default_store


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


def test_model_mixin_requires_global_store():
    clear_default_store()

    with pytest.raises(MissingGlobalStoreError):
        Widget.find_many()


def test_model_mixin_rejects_invalid_sync_store_binding():
    Widget.use_store(cast(StoreBinding, "bad-store"))
    try:
        with pytest.raises(InvalidStoreBindingError):
            Widget.find_many()
    finally:
        Widget.use_store(None)


@pytest.mark.asyncio
async def test_model_mixin_rejects_invalid_async_store_binding():
    Widget.use_store(cast(StoreBinding, "bad-store"))
    try:
        with pytest.raises(InvalidStoreBindingError):
            await Widget.afind_many()
    finally:
        Widget.use_store(None)


def test_sync_paginate_rejects_projection(store):
    spec = QuerySpec[Widget]().select_columns(Widget.id).paginate(limit=10, offset=0)

    with pytest.raises(ProjectionPaginationError):
        store.sync.paginate(Widget, spec=spec)


@pytest.mark.asyncio
async def test_async_paginate_rejects_projection(store):
    spec = QuerySpec[Widget]().select_columns(Widget.id).paginate(limit=10, offset=0)

    with pytest.raises(ProjectionPaginationError):
        await store.async_.paginate(Widget, spec=spec)
