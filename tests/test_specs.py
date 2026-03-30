from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.orm.interfaces import ORMOption

from tests.conftest import Widget
from typed_store.errors import BulkQueryShapeError
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


def test_query_builder_is_immutable():
    query = (
        Query[Widget]()
        .where(Widget.category == "a")
        .order(Widget.id.asc())
        .limit_to(5)
        .offset_by(2)
    )

    assert len(query.filters) == 1
    assert len(query.order_by) == 1
    assert query.limit == 5
    assert query.offset == 2


def test_page_request_and_patch_store_boundary_inputs():
    page = PageRequest(limit=10, offset=20)
    patch = Patch[Widget]({"category": "updated"})

    assert page.limit == 10
    assert page.offset == 20
    assert patch.values == {"category": "updated"}


def test_projection_query_tracks_columns_and_filters():
    projection = (
        ProjectionQuery[tuple[int, str]](Widget.id, Widget.name)
        .where(Widget.category == "a")
        .order(Widget.id.asc())
    )

    assert projection.columns == (Widget.id, Widget.name)
    assert len(projection.filters) == 1
    assert len(projection.order_by) == 1


def test_query_accepts_filter_only_bulk_shape() -> None:
    query = Query[Widget]().where(Widget.category == "ops")

    query.assert_bulk_compatible()


@pytest.mark.parametrize(
    ("query_factory", "expected_fragment"),
    [
        (lambda: Query[Widget]().order(Widget.id.asc()), "order_by"),
        (lambda: Query[Widget]().limit_to(10), "limit"),
        (lambda: Query[Widget]().offset_by(5), "offset"),
        (lambda: Query[Widget]().with_options(cast(ORMOption, object())), "options"),
    ],
)
def test_query_rejects_unsupported_bulk_shape(query_factory, expected_fragment) -> None:
    with pytest.raises(BulkQueryShapeError, match=expected_fragment):
        query_factory().assert_bulk_compatible()
