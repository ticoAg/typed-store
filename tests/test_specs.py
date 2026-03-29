from __future__ import annotations

from tests.conftest import Widget
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
