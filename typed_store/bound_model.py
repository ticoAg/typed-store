"""Bound model views exposed by TypedStoreModel.bind()."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from typed_store.protocols import AsyncModelBoundStoreProtocol, SyncModelBoundStoreProtocol
from typed_store.results import Page
from typed_store.specs import PageRequest, Patch, Query


class SyncBoundModelView[TModel]:
    """Bound sync model operations routed through sync store capabilities."""

    def __init__(self, model: type[TModel], store: SyncModelBoundStoreProtocol[object]):
        self._model = model
        self._store = store

    def insert(
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return cast(
            TModel,
            self._store.insert(entity, session=session, commit=commit, refresh=refresh),
        )

    def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return cast(list[TModel], self._store.insert_many(entities, session=session, commit=commit))

    def get(self, ident: object, *, session: Session | None = None) -> TModel | None:
        return cast(TModel | None, self._store.get(self._model, ident, session=session))

    def find_one(self, *, query: Query[TModel], session: Session | None = None) -> TModel | None:
        return cast(TModel | None, self._store.find_one(self._model, query=query, session=session))

    def find_many(self, *, query: Query[TModel], session: Session | None = None) -> list[TModel]:
        return cast(list[TModel], self._store.find_many(self._model, query=query, session=session))

    def exists(self, *, query: Query[TModel], session: Session | None = None) -> bool:
        return self._store.exists(self._model, query=query, session=session)

    def count(self, *, query: Query[TModel], session: Session | None = None) -> int:
        return self._store.count(self._model, query=query, session=session)

    def paginate(
        self,
        *,
        query: Query[TModel],
        page: PageRequest,
        session: Session | None = None,
    ) -> Page[TModel]:
        return cast(
            Page[TModel],
            self._store.paginate(self._model, query=query, page=page, session=session),
        )

    def update(
        self,
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.update(
            self._model, query=query, patch=patch, session=session, commit=commit
        )

    def bulk_update(
        self,
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        return self._store.bulk_update(
            self._model,
            query=query,
            patch=patch,
            session=session,
            commit=commit,
        )

    def delete(
        self, *, query: Query[TModel], session: Session | None = None, commit: bool = True
    ) -> int:
        return self._store.delete(self._model, query=query, session=session, commit=commit)

    def bulk_delete(
        self, *, query: Query[TModel], session: Session | None = None, commit: bool = True
    ) -> int:
        return self._store.bulk_delete(self._model, query=query, session=session, commit=commit)


class AsyncBoundModelView[TModel]:
    """Bound async model operations routed through async store capabilities."""

    def __init__(self, model: type[TModel], store: AsyncModelBoundStoreProtocol[object]):
        self._model = model
        self._store = store

    async def insert(
        self,
        entity: TModel,
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        return cast(
            TModel,
            await self._store.insert(entity, session=session, commit=commit, refresh=refresh),
        )

    async def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        return cast(
            list[TModel],
            await self._store.insert_many(entities, session=session, commit=commit),
        )

    async def get(self, ident: object, *, session: AsyncSession | None = None) -> TModel | None:
        return cast(TModel | None, await self._store.get(self._model, ident, session=session))

    async def find_one(
        self, *, query: Query[TModel], session: AsyncSession | None = None
    ) -> TModel | None:
        return cast(
            TModel | None, await self._store.find_one(self._model, query=query, session=session)
        )

    async def find_many(
        self, *, query: Query[TModel], session: AsyncSession | None = None
    ) -> list[TModel]:
        return cast(
            list[TModel], await self._store.find_many(self._model, query=query, session=session)
        )

    async def exists(self, *, query: Query[TModel], session: AsyncSession | None = None) -> bool:
        return await self._store.exists(self._model, query=query, session=session)

    async def count(self, *, query: Query[TModel], session: AsyncSession | None = None) -> int:
        return await self._store.count(self._model, query=query, session=session)

    async def paginate(
        self,
        *,
        query: Query[TModel],
        page: PageRequest,
        session: AsyncSession | None = None,
    ) -> Page[TModel]:
        return cast(
            Page[TModel],
            await self._store.paginate(self._model, query=query, page=page, session=session),
        )

    async def update(
        self,
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        return await self._store.update(
            self._model, query=query, patch=patch, session=session, commit=commit
        )

    async def bulk_update(
        self,
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        return await self._store.bulk_update(
            self._model,
            query=query,
            patch=patch,
            session=session,
            commit=commit,
        )

    async def delete(
        self, *, query: Query[TModel], session: AsyncSession | None = None, commit: bool = True
    ) -> int:
        return await self._store.delete(self._model, query=query, session=session, commit=commit)

    async def bulk_delete(
        self, *, query: Query[TModel], session: AsyncSession | None = None, commit: bool = True
    ) -> int:
        return await self._store.bulk_delete(
            self._model,
            query=query,
            session=session,
            commit=commit,
        )
