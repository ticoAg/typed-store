from __future__ import annotations

import pytest
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from tests.conftest import Member, Team, Widget
from typed_store import PageRequest, Patch, ProjectionQuery, Query


@pytest.mark.asyncio
async def test_async_insert_find_and_paginate(store):
    await store.async_.insert_many(
        [
            Widget(name="alpha", category="a"),
            Widget(name="beta", category="b"),
            Widget(name="gamma", category="a"),
        ]
    )

    query = Query[Widget]().where(Widget.category == "a").order(Widget.id.asc())
    page = await store.async_.paginate(Widget, query=query, page=PageRequest(limit=2, offset=0))

    assert page.total == 2
    assert [item.name for item in page.items] == ["alpha", "gamma"]

    found = await store.async_.find_one(Widget, query=Query[Widget]().where(Widget.name == "beta"))
    assert found is not None
    assert found.category == "b"


@pytest.mark.asyncio
async def test_async_select_rows_update_delete_and_mixin(store):
    await store.async_.insert_many(
        [Widget(name="alpha", category="a"), Widget(name="beta", category="a")]
    )

    rows = await store.async_.select_rows(
        Widget,
        projection=ProjectionQuery[tuple[int]](func.count()).where(Widget.category == "a"),
    )
    assert rows[0][0] == 2

    updated = await store.async_.update(
        Widget,
        query=Query[Widget]().where(Widget.name == "alpha"),
        patch=Patch[Widget]({"category": "changed"}),
    )
    assert updated == 1

    deleted = await store.async_.delete(
        Widget,
        query=Query[Widget]().where(Widget.category == "changed"),
    )
    assert deleted == 1

    widgets = Widget.bind(store.async_)
    await widgets.insert(Widget(name="mixin-async", category="ma"))
    items = await widgets.find_many(query=Query[Widget]().where(Widget.category == "ma"))
    assert len(items) == 1


@pytest.mark.asyncio
async def test_async_bulk_update_and_delete(store):
    await store.async_.insert_many(
        [
            Widget(name="a", category="bulk"),
            Widget(name="b", category="bulk"),
            Widget(name="c", category="keep"),
        ]
    )

    updated = await store.async_.bulk_update(
        Widget,
        query=Query[Widget]().where(Widget.category == "bulk"),
        patch=Patch[Widget]({"category": "bulk-updated"}),
    )
    assert updated == 2

    assert (
        await store.async_.count(
            Widget,
            query=Query[Widget]().where(Widget.category == "bulk-updated"),
        )
        == 2
    )

    deleted = await store.async_.bulk_delete(
        Widget,
        query=Query[Widget]().where(Widget.category == "bulk-updated"),
    )
    assert deleted == 2


@pytest.mark.asyncio
async def test_async_unit_of_work_commit_and_rollback(store):
    async with store.async_.unit_of_work() as uow:
        assert uow.session is not None
        uow.session.add(Widget(name="inside-async-uow", category="uow"))

    rows = await store.async_.find_many(
        Widget, query=Query[Widget]().where(Widget.category == "uow")
    )
    assert len(rows) == 1

    with pytest.raises(RuntimeError):
        async with store.async_.unit_of_work() as uow:
            uow.session.add(Widget(name="rolled-back", category="rollback"))
            raise RuntimeError("boom")

    assert (
        await store.async_.find_many(
            Widget, query=Query[Widget]().where(Widget.category == "rollback")
        )
        == []
    )


@pytest.mark.asyncio
async def test_async_external_session_reuse_and_loader_options(store, provider):
    async with provider.get_async_session() as session:
        await store.async_.insert(
            Widget(name="external", category="draft"), session=session, commit=False
        )
        await store.async_.update(
            Widget,
            query=Query[Widget]().where(Widget.name == "external"),
            patch=Patch[Widget]({"category": "persisted"}),
            session=session,
            commit=False,
        )
        await session.commit()

    found = await store.async_.find_one(
        Widget,
        query=Query[Widget]().where(Widget.name == "external"),
    )
    assert found is not None
    assert found.category == "persisted"

    team = Team(name="async-core")
    await store.async_.insert(team)
    await store.async_.insert_many(
        [Member(team_id=team.id, name="alice"), Member(team_id=team.id, name="bob")]
    )

    query = Query[Team]().with_options(selectinload(Team.members)).where(Team.id == team.id)
    loaded = await store.async_.find_one(Team, query=query)

    assert loaded is not None
    assert [member.name for member in loaded.members] == ["alice", "bob"]
