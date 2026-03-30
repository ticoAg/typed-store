"""Protocol-first immutable request objects for TypedStore."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from sqlalchemy import ColumnExpressionArgument, Select, select
from sqlalchemy.orm.interfaces import ORMOption

from typed_store.errors import BulkQueryShapeError

type FilterClause = ColumnExpressionArgument[bool]
type OrderClause = ColumnExpressionArgument[object]
type ProjectionClause = ColumnExpressionArgument[object]
type LoaderOption = ORMOption


@dataclass(slots=True, frozen=True)
class Query[TModel]:
    filters: tuple[FilterClause, ...] = field(default_factory=tuple)
    order_by: tuple[OrderClause, ...] = field(default_factory=tuple)
    limit: int | None = None
    offset: int | None = None
    options: tuple[LoaderOption, ...] = field(default_factory=tuple)

    def where(self, *filters: FilterClause) -> Query[TModel]:
        return replace(self, filters=self.filters + tuple(filters))

    def order(self, *clauses: OrderClause) -> Query[TModel]:
        return replace(self, order_by=self.order_by + tuple(clauses))

    def limit_to(self, limit: int | None) -> Query[TModel]:
        return replace(self, limit=limit)

    def offset_by(self, offset: int | None) -> Query[TModel]:
        return replace(self, offset=offset)

    def with_options(self, *options: LoaderOption) -> Query[TModel]:
        return replace(self, options=self.options + tuple(options))

    def assert_bulk_compatible(self) -> None:
        invalid_parts: list[str] = []
        if self.order_by:
            invalid_parts.append("order_by")
        if self.limit is not None:
            invalid_parts.append("limit")
        if self.offset is not None:
            invalid_parts.append("offset")
        if self.options:
            invalid_parts.append("options")
        if invalid_parts:
            joined = ", ".join(invalid_parts)
            message = (
                "Bulk mutation only supports filter-only Query objects; "
                f"got unsupported fields: {joined}."
            )
            raise BulkQueryShapeError(message)

    def build_select(self, model: type[TModel]) -> Select[Any]:
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
        stmt = select(model)
        if self.filters:
            stmt = stmt.where(*self.filters)
        return stmt


@dataclass(slots=True, frozen=True)
class PageRequest:
    limit: int
    offset: int = 0


@dataclass(slots=True, frozen=True)
class Patch[TModel]:
    values: Mapping[str, object]


@dataclass(slots=True, frozen=True, init=False)
class ProjectionQuery[TRow]:
    columns: tuple[ProjectionClause, ...]
    filters: tuple[FilterClause, ...] = field(default_factory=tuple)
    order_by: tuple[OrderClause, ...] = field(default_factory=tuple)
    options: tuple[LoaderOption, ...] = field(default_factory=tuple)

    def __init__(self, *columns: ProjectionClause):
        object.__setattr__(self, "columns", tuple(columns))
        object.__setattr__(self, "filters", ())
        object.__setattr__(self, "order_by", ())
        object.__setattr__(self, "options", ())

    @classmethod
    def _from_parts(
        cls,
        columns: tuple[ProjectionClause, ...],
        filters: tuple[FilterClause, ...],
        order_by: tuple[OrderClause, ...],
        options: tuple[LoaderOption, ...],
    ) -> ProjectionQuery[TRow]:
        instance = cls(*columns)
        object.__setattr__(instance, "filters", filters)
        object.__setattr__(instance, "order_by", order_by)
        object.__setattr__(instance, "options", options)
        return instance

    def where(self, *filters: FilterClause) -> ProjectionQuery[TRow]:
        return self._from_parts(
            self.columns,
            self.filters + tuple(filters),
            self.order_by,
            self.options,
        )

    def order(self, *clauses: OrderClause) -> ProjectionQuery[TRow]:
        return self._from_parts(
            self.columns,
            self.filters,
            self.order_by + tuple(clauses),
            self.options,
        )

    def with_options(self, *options: LoaderOption) -> ProjectionQuery[TRow]:
        return self._from_parts(
            self.columns,
            self.filters,
            self.order_by,
            self.options + tuple(options),
        )

    def build_select(self, model: type[object]) -> Select[Any]:
        stmt = select(*self.columns).select_from(model)  # ty: ignore[no-matching-overload]
        if self.filters:
            stmt = stmt.where(*self.filters)
        if self.order_by:
            stmt = stmt.order_by(*self.order_by)
        if self.options:
            stmt = stmt.options(*self.options)
        return stmt
