"""Model-bound store views that eliminate repeated model arguments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from typed_store.query_spec import FilterClause, OrderClause, QuerySpec
from typed_store.results import Page

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session


class SyncModelStore[TModel]:
    """Model-bound view over SyncTypedStore, eliminates repeated model arg."""

    def __init__(self, store: Any, model: type[TModel]):
        self._store = store
        self._model = model

    def insert(
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return self._store.insert(entity, session=session, commit=commit, refresh=refresh)

    def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return self._store.insert_many(entities, session=session, commit=commit)

    def get(self, ident: object, *, session: Session | None = None) -> TModel | None:
        return self._store.get(self._model, ident, session=session)

    def find_one(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        session: Session | None = None,
    ) -> TModel | None:
        return self._store.find_one(self._model, *filters, spec=spec, order=order, session=session)

    def find_many(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> list[TModel]:
        return self._store.find_many(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    def paginate(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> Page[TModel]:
        return self._store.paginate(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    def update_fields(
        self,
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.update_fields(
            self._model, values, *filters, spec=spec, session=session, commit=commit
        )

    def delete_where(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.delete_where(
            self._model, *filters, spec=spec, session=session, commit=commit
        )


class AsyncModelStore[TModel]:
    """Model-bound view over AsyncTypedStore, eliminates repeated model arg."""

    def __init__(self, store: Any, model: type[TModel]):
        self._store = store
        self._model = model

    async def insert(
        self,
        entity: TModel,
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return await self._store.insert(entity, session=session, commit=commit, refresh=refresh)

    async def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return await self._store.insert_many(entities, session=session, commit=commit)

    async def get(self, ident: object, *, session: AsyncSession | None = None) -> TModel | None:
        return await self._store.get(self._model, ident, session=session)

    async def find_one(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        session: AsyncSession | None = None,
    ) -> TModel | None:
        return await self._store.find_one(
            self._model, *filters, spec=spec, order=order, session=session
        )

    async def find_many(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: AsyncSession | None = None,
    ) -> list[TModel]:
        return await self._store.find_many(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    async def paginate(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: AsyncSession | None = None,
    ) -> Page[TModel]:
        return await self._store.paginate(
            self._model,
            *filters,
            spec=spec,
            order=order,
            limit=limit,
            offset=offset,
            session=session,
        )

    async def update_fields(
        self,
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        return await self._store.update_fields(
            self._model, values, *filters, spec=spec, session=session, commit=commit
        )

    async def delete_where(
        self,
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        return await self._store.delete_where(
            self._model, *filters, spec=spec, session=session, commit=commit
        )
