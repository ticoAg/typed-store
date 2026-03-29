from __future__ import annotations

import pytest

from tests.conftest import Widget
from typed_store.bound_model import AsyncBoundModelView, SyncBoundModelView


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
