"""Optional Active Record style helpers built on top of TypedStore."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import ClassVar, Self, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from typed_store.async_store import AsyncTypedStore
from typed_store.errors import InvalidStoreBindingError, MissingGlobalStoreError
from typed_store.query_spec import FilterClause, OrderClause, QuerySpec
from typed_store.results import Page
from typed_store.store import TypedStore
from typed_store.sync import SyncTypedStore

type StoreBinding = TypedStore | SyncTypedStore[object] | AsyncTypedStore[object]
type SyncStoreBinding = TypedStore | SyncTypedStore[object]
type AsyncStoreBinding = TypedStore | AsyncTypedStore[object]

_default_store: StoreBinding | None = None


def set_default_store(store: StoreBinding) -> None:
    """Bind a default store used by TypedStoreModel."""
    global _default_store
    _default_store = store


def get_default_store() -> StoreBinding:
    """Return the default store used by TypedStoreModel."""
    if _default_store is None:
        raise MissingGlobalStoreError("No default TypedStore has been configured.")
    return _default_store


def clear_default_store() -> None:
    """Clear the configured default store."""
    global _default_store
    _default_store = None


def _resolve_sync_store(store: SyncStoreBinding) -> SyncTypedStore[object]:
    if isinstance(store, SyncTypedStore):
        return cast(SyncTypedStore[object], store)
    if isinstance(store, TypedStore):
        return store.sync
    raise InvalidStoreBindingError(
        "A sync model operation requires a TypedStore or SyncTypedStore instance."
    )


def _resolve_async_store(store: AsyncStoreBinding) -> AsyncTypedStore[object]:
    if isinstance(store, AsyncTypedStore):
        return cast(AsyncTypedStore[object], store)
    if isinstance(store, TypedStore):
        return store.async_
    raise InvalidStoreBindingError(
        "An async model operation requires a TypedStore or AsyncTypedStore instance."
    )


class TypedStoreModel:
    """Optional mixin exposing store-backed helper methods on ORM models."""

    __typed_store__: ClassVar[StoreBinding | None] = None

    @classmethod
    def use_store(cls, store: StoreBinding | None) -> None:
        """Bind a store directly to the model class."""
        cls.__typed_store__ = store

    @classmethod
    def store(cls) -> StoreBinding:
        """Resolve the store bound to the model or fallback to the global store."""
        return cls.__typed_store__ or get_default_store()

    def insert(
        self,
        *,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> Self:
        """Insert the current model instance using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or self.store()))
        active_store.insert(self, session=session, commit=commit)
        return self

    async def ainsert(
        self,
        *,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> Self:
        """Insert the current model instance using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or self.store()))
        await active_store.insert(self, session=session, commit=commit)
        return self

    @classmethod
    def insert_many(
        cls: type[Self],
        entities: Sequence[Self],
        *,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[Self]:
        """Insert multiple model instances using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return cast(list[Self], active_store.insert_many(entities, session=session, commit=commit))

    @classmethod
    async def ainsert_many(
        cls: type[Self],
        entities: Sequence[Self],
        *,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[Self]:
        """Insert multiple model instances using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return cast(
            list[Self], await active_store.insert_many(entities, session=session, commit=commit)
        )

    @classmethod
    def get(
        cls: type[Self],
        ident: object,
        *,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
    ) -> Self | None:
        """Fetch a model instance by primary key using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return cast(Self | None, active_store.get(cls, ident, session=session))

    @classmethod
    async def aget(
        cls: type[Self],
        ident: object,
        *,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
    ) -> Self | None:
        """Fetch a model instance by primary key using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return cast(Self | None, await active_store.get(cls, ident, session=session))

    @classmethod
    def find_one(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
    ) -> Self | None:
        """Find a single model instance using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return cast(
            Self | None,
            active_store.find_one(cls, *filters, spec=spec, order=order, session=session),
        )

    @classmethod
    async def afind_one(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
    ) -> Self | None:
        """Find a single model instance using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return cast(
            Self | None,
            await active_store.find_one(cls, *filters, spec=spec, order=order, session=session),
        )

    @classmethod
    def find_many(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
    ) -> list[Self]:
        """Find many model instances using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return cast(
            list[Self],
            active_store.find_many(
                cls, *filters, spec=spec, order=order, limit=limit, offset=offset, session=session
            ),
        )

    @classmethod
    async def afind_many(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
    ) -> list[Self]:
        """Find many model instances using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return cast(
            list[Self],
            await active_store.find_many(
                cls, *filters, spec=spec, order=order, limit=limit, offset=offset, session=session
            ),
        )

    @classmethod
    def paginate(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
    ) -> Page[Self]:
        """Paginate model instances using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return cast(
            Page[Self],
            active_store.paginate(
                cls, *filters, spec=spec, order=order, limit=limit, offset=offset, session=session
            ),
        )

    @classmethod
    async def apaginate(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
    ) -> Page[Self]:
        """Paginate model instances using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return cast(
            Page[Self],
            await active_store.paginate(
                cls, *filters, spec=spec, order=order, limit=limit, offset=offset, session=session
            ),
        )

    @classmethod
    def update_fields(
        cls: type[Self],
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching model instances using the sync facade."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return active_store.update_fields(
            cls, values, *filters, spec=spec, session=session, commit=commit
        )

    @classmethod
    async def aupdate_fields(
        cls: type[Self],
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching model instances using the async facade."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return await active_store.update_fields(
            cls, values, *filters, spec=spec, session=session, commit=commit
        )

    @classmethod
    def delete_where(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        store: SyncStoreBinding | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Delete model instances matching the provided spec."""
        active_store = _resolve_sync_store(cast(SyncStoreBinding, store or cls.store()))
        return active_store.delete_where(cls, *filters, spec=spec, session=session, commit=commit)

    @classmethod
    async def adelete_where(
        cls: type[Self],
        *filters: FilterClause,
        spec: QuerySpec[Self] | None = None,
        store: AsyncStoreBinding | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        """Delete model instances matching the provided spec."""
        active_store = _resolve_async_store(cast(AsyncStoreBinding, store or cls.store()))
        return await active_store.delete_where(
            cls, *filters, spec=spec, session=session, commit=commit
        )
