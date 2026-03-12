"""Query specification objects used by TypedStore."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from sqlalchemy import ColumnExpressionArgument, Select, select
from sqlalchemy.orm.interfaces import ORMOption

type FilterClause = ColumnExpressionArgument[bool]
type OrderClause = ColumnExpressionArgument[object]
type ProjectionClause = ColumnExpressionArgument[object]
type LoaderOption = ORMOption


@dataclass(slots=True, frozen=True)
class QuerySpec[TModel]:
    """Typed query specification used to build SQLAlchemy select statements."""

    filters: tuple[FilterClause, ...] = field(default_factory=tuple)
    order_by: tuple[OrderClause, ...] = field(default_factory=tuple)
    limit: int | None = None
    offset: int | None = None
    columns: tuple[ProjectionClause, ...] | None = field(default=None)
    options: tuple[LoaderOption, ...] = field(default_factory=tuple)

    @classmethod
    def empty(cls) -> QuerySpec[TModel]:
        """Return an empty query specification."""
        return cls()

    def where(self, *filters: FilterClause) -> QuerySpec[TModel]:
        """Return a new spec with additional filters."""
        return replace(self, filters=self.filters + tuple(filters))

    def order(self, *clauses: OrderClause) -> QuerySpec[TModel]:
        """Return a new spec with additional order clauses."""
        return replace(self, order_by=self.order_by + tuple(clauses))

    def paginate(self, *, limit: int | None, offset: int | None = None) -> QuerySpec[TModel]:
        """Return a new spec with pagination settings."""
        return replace(self, limit=limit, offset=offset)

    def select_columns(self, *columns: ProjectionClause) -> QuerySpec[TModel]:
        """Return a new spec that selects explicit columns."""
        return replace(self, columns=tuple(columns))

    def with_options(self, *options: LoaderOption) -> QuerySpec[TModel]:
        """Return a new spec with SQLAlchemy loader options."""
        return replace(self, options=self.options + tuple(options))

    def build_select(self, model: type[TModel]) -> Select[Any]:
        """Build a SQLAlchemy select statement for the given model."""
        if self.columns is not None:
            stmt = select(*self.columns).select_from(model)  # ty: ignore[no-matching-overload]
        else:
            stmt = select(model)

        if self.filters:
            stmt = stmt.where(*self.filters)
        if self.order_by:
            stmt = stmt.order_by(*self.order_by)
        if self.offset is not None:
            stmt = stmt.offset(self.offset)
        if self.limit is not None:
            stmt = stmt.limit(self.limit)
        if self.options:
            stmt = stmt.options(*self.options)
        return stmt

    def count_select(self, model: type[TModel]) -> Select[Any]:
        """Build the base select used for count queries."""
        stmt = select(model)
        if self.filters:
            stmt = stmt.where(*self.filters)
        return stmt
