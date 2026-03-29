from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from tests.conftest import Member, Team, Widget
from typed_store import QuerySpec


def test_sync_insert_find_and_paginate(store):
    store.sync.insert_many(
        [
            Widget(name="alpha", category="a"),
            Widget(name="beta", category="b"),
            Widget(name="gamma", category="a"),
        ]
    )

    page = store.sync.paginate(
        Widget, Widget.category == "a", order=Widget.id.asc(), limit=1, offset=0
    )

    assert page.total == 2
    assert [item.name for item in page.items] == ["alpha"]

    found = store.sync.find_one(Widget, Widget.name == "beta")
    assert found is not None
    assert found.category == "b"


def test_sync_select_rows_and_count_from_clause(store):
    store.sync.insert_many([Widget(name="alpha", category="a"), Widget(name="beta", category="a")])

    rows = store.sync.select_rows(
        Widget,
        QuerySpec[Widget]().select_columns(func.count()).where(Widget.category == "a"),
    )

    assert rows[0][0] == 2


def test_sync_update_delete_and_custom_scalars(store):
    store.sync.insert_many([Widget(name="alpha", category="a"), Widget(name="beta", category="b")])

    updated = store.sync.update_fields(
        Widget,
        {"category": "updated"},
        Widget.name == "alpha",
    )
    assert updated == 1

    names = store.sync.select_scalars(select(Widget.name).order_by(Widget.id.asc()))
    assert names == ["alpha", "beta"]

    deleted = store.sync.delete_where(Widget, Widget.category == "updated")
    assert deleted == 1
    assert store.sync.select_scalars(select(func.count()).select_from(Widget))[0] == 1


def test_sync_unit_of_work_commit_and_rollback(store):
    with store.sync.unit_of_work() as uow:
        assert uow.session is not None
        uow.session.add(Widget(name="inside-uow", category="uow"))

    items = store.sync.find_many(Widget, Widget.category == "uow")
    assert len(items) == 1

    with pytest.raises(RuntimeError), store.sync.unit_of_work() as uow:
        uow.session.add(Widget(name="rolled-back", category="rollback"))
        raise RuntimeError("boom")

    assert store.sync.find_many(Widget, Widget.category == "rollback") == []


def test_sync_external_session_reuse(store, provider):
    with provider.get_session() as session:
        store.sync.insert(Widget(name="external", category="draft"), session=session, commit=False)
        store.sync.update_fields(
            Widget,
            {"category": "persisted"},
            Widget.name == "external",
            session=session,
            commit=False,
        )
        session.commit()

    found = store.sync.find_one(Widget, Widget.name == "external")
    assert found is not None
    assert found.category == "persisted"


def test_sync_loader_options_and_model_mixin(store):
    team = Team(name="core")
    store.sync.insert(team)
    store.sync.insert_many(
        [Member(team_id=team.id, name="alice"), Member(team_id=team.id, name="bob")]
    )

    spec = QuerySpec[Team]().with_options(selectinload(Team.members)).where(Team.id == team.id)
    loaded = store.sync.find_one(Team, spec=spec)

    assert loaded is not None
    assert [member.name for member in loaded.members] == ["alice", "bob"]

    widgets = Widget.bind(store.sync)
    widgets.insert(Widget(name="mixin", category="m"))
    mixin_rows = widgets.find_many(Widget.category == "m")
    assert len(mixin_rows) == 1
