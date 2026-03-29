"""Runtime-checkable capability protocols for TypedStore public APIs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from typed_store.results import Page
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query


@runtime_checkable
class ReadableStoreProtocol[TModel](Protocol):
    def get(
        self, model: type[TModel], ident: object, *, session: Session | None = None
    ) -> TModel | None: ...
    def find_one(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> TModel | None: ...
    def find_many(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> list[TModel]: ...
    def exists(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> bool: ...
    def count(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> int: ...
    def paginate(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        page: PageRequest,
        session: Session | None = None,
    ) -> Page[TModel]: ...


@runtime_checkable
class WritableStoreProtocol[TModel](Protocol):
    def insert(
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel: ...
    def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]: ...


@runtime_checkable
class PatchableStoreProtocol[TModel](Protocol):
    def update(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int: ...


@runtime_checkable
class DeletableStoreProtocol[TModel](Protocol):
    def delete(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int: ...


@runtime_checkable
class StatementExecutorProtocol(Protocol):
    def select_rows[TRow](
        self,
        model: type[object],
        *,
        projection: ProjectionQuery[TRow],
        session: Session | None = None,
    ) -> list[TRow]: ...
    def select_scalars[TScalar](
        self, statement: Executable, *, session: Session | None = None
    ) -> list[TScalar]: ...


@runtime_checkable
class TransactionalStoreProtocol(Protocol):
    def unit_of_work(self, *, auto_commit: bool = True) -> object: ...


@runtime_checkable
class SyncModelBoundStoreProtocol[TModel](
    ReadableStoreProtocol[TModel],
    WritableStoreProtocol[TModel],
    PatchableStoreProtocol[TModel],
    DeletableStoreProtocol[TModel],
    Protocol,
):
    """Composite sync capability protocol used by bound model views."""


@runtime_checkable
class AsyncReadableStoreProtocol[TModel](Protocol):
    async def get(
        self, model: type[TModel], ident: object, *, session: AsyncSession | None = None
    ) -> TModel | None: ...
    async def find_one(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: AsyncSession | None = None,
    ) -> TModel | None: ...
    async def find_many(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: AsyncSession | None = None,
    ) -> list[TModel]: ...
    async def exists(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: AsyncSession | None = None,
    ) -> bool: ...
    async def count(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: AsyncSession | None = None,
    ) -> int: ...
    async def paginate(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        page: PageRequest,
        session: AsyncSession | None = None,
    ) -> Page[TModel]: ...


@runtime_checkable
class AsyncWritableStoreProtocol[TModel](Protocol):
    async def insert(
        self,
        entity: TModel,
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel: ...
    async def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[TModel]: ...


@runtime_checkable
class AsyncPatchableStoreProtocol[TModel](Protocol):
    async def update(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int: ...


@runtime_checkable
class AsyncDeletableStoreProtocol[TModel](Protocol):
    async def delete(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int: ...


@runtime_checkable
class AsyncStatementExecutorProtocol(Protocol):
    async def select_rows[TRow](
        self,
        model: type[object],
        *,
        projection: ProjectionQuery[TRow],
        session: AsyncSession | None = None,
    ) -> list[TRow]: ...
    async def select_scalars[TScalar](
        self, statement: Executable, *, session: AsyncSession | None = None
    ) -> list[TScalar]: ...


@runtime_checkable
class AsyncTransactionalStoreProtocol(Protocol):
    def unit_of_work(self, *, auto_commit: bool = True) -> object: ...


@runtime_checkable
class AsyncModelBoundStoreProtocol[TModel](
    AsyncReadableStoreProtocol[TModel],
    AsyncWritableStoreProtocol[TModel],
    AsyncPatchableStoreProtocol[TModel],
    AsyncDeletableStoreProtocol[TModel],
    Protocol,
):
    """Composite async capability protocol used by bound model views."""
