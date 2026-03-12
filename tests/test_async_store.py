from __future__ import annotations

import pytest
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from tests.conftest import Member, Team, Widget
from typed_store import QuerySpec


@pytest.mark.asyncio
async def test_async_insert_find_and_paginate(store):
    await store.async_.insert_many(
        [
            Widget(name="alpha", category="a"),
            Widget(name="beta", category="b"),
            Widget(name="gamma", category="a"),
        ]
    )

    spec = (
        QuerySpec[Widget]
        .empty()
        .where(Widget.category == "a")
        .order(Widget.id.asc())
        .paginate(limit=2, offset=0)
    )
    page = await store.async_.paginate(Widget, spec)

    assert page.total == 2
    assert [item.name for item in page.items] == ["alpha", "gamma"]

    found = await store.async_.find_one(
        Widget, QuerySpec[Widget].empty().where(Widget.name == "beta")
    )
    assert found is not None
    assert found.category == "b"


@pytest.mark.asyncio
async def test_async_select_rows_update_delete_and_mixin(store):
    await store.async_.insert_many(
        [Widget(name="alpha", category="a"), Widget(name="beta", category="a")]
    )

    rows = await store.async_.select_rows(
        Widget,
        QuerySpec[Widget].empty().select_columns(func.count()).where(Widget.category == "a"),
    )
    assert rows[0][0] == 2

    updated = await store.async_.update_fields(
        Widget,
        {"category": "changed"},
        QuerySpec[Widget].empty().where(Widget.name == "alpha"),
    )
    assert updated == 1

    deleted = await store.async_.delete_where(
        Widget, QuerySpec[Widget].empty().where(Widget.category == "changed")
    )
    assert deleted == 1

    await Widget(name="mixin-async", category="ma").ainsert()
    items = await Widget.afind_many(QuerySpec[Widget].empty().where(Widget.category == "ma"))
    assert len(items) == 1


@pytest.mark.asyncio
async def test_async_unit_of_work_commit_and_rollback(store):
    async with store.async_.unit_of_work() as uow:
        assert uow.session is not None
        uow.session.add(Widget(name="inside-async-uow", category="uow"))

    rows = await store.async_.find_many(
        Widget, QuerySpec[Widget].empty().where(Widget.category == "uow")
    )
    assert len(rows) == 1

    with pytest.raises(RuntimeError):
        async with store.async_.unit_of_work() as uow:
            uow.session.add(Widget(name="rolled-back", category="rollback"))
            raise RuntimeError("boom")

    assert (
        await store.async_.find_many(
            Widget, QuerySpec[Widget].empty().where(Widget.category == "rollback")
        )
        == []
    )


@pytest.mark.asyncio
async def test_async_external_session_reuse_and_loader_options(store, provider):
    async with provider.get_async_session() as session:
        await store.async_.insert(
            Widget(name="external", category="draft"), session=session, commit=False
        )
        await store.async_.update_fields(
            Widget,
            {"category": "persisted"},
            QuerySpec[Widget].empty().where(Widget.name == "external"),
            session=session,
            commit=False,
        )
        await session.commit()

    found = await store.async_.find_one(
        Widget, QuerySpec[Widget].empty().where(Widget.name == "external")
    )
    assert found is not None
    assert found.category == "persisted"

    team = Team(name="async-core")
    await store.async_.insert(team)
    await store.async_.insert_many(
        [Member(team_id=team.id, name="alice"), Member(team_id=team.id, name="bob")]
    )

    spec = (
        QuerySpec[Team].empty().with_options(selectinload(Team.members)).where(Team.id == team.id)
    )
    loaded = await store.async_.find_one(Team, spec)

    assert loaded is not None
    assert [member.name for member in loaded.members] == ["alice", "bob"]
