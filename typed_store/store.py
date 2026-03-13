"""Top-level TypedStore entrypoint bundling sync and async facades."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import Engine
from sqlalchemy.sql.expression import Executable

from typed_store.async_store import AsyncTypedStore
from typed_store.engine import EngineBundle, EngineConfig, build_engine_bundle
from typed_store.query_spec import FilterClause, OrderClause, QuerySpec
from typed_store.results import Page
from typed_store.session import SessionProvider
from typed_store.sync import SyncTypedStore
from typed_store.uow import AsyncUnitOfWork, UnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.orm import Session

    from typed_store.model_store import SyncModelStore


class TypedStore:
    """Bundle synchronous and asynchronous TypedStore facades under one provider."""

    _bundle: EngineBundle | None

    def __init__(self, provider: SessionProvider):
        self.provider = provider
        self.sync: SyncTypedStore[object] = SyncTypedStore(provider)
        self.async_: AsyncTypedStore[object] = AsyncTypedStore(provider)
        self._bundle = None

    @classmethod
    def from_url(
        cls,
        url: str | None = None,
        *,
        async_url: str | None = None,
        echo: bool = False,
        **engine_options: Any,
    ) -> TypedStore:
        """Create a TypedStore from database URL(s) in one step."""
        bundle = build_engine_bundle(
            sync_config=EngineConfig(url=url, echo=echo, engine_options=engine_options)
            if url
            else None,
            async_config=EngineConfig(url=async_url, echo=echo, engine_options=engine_options)
            if async_url
            else None,
        )
        provider = SessionProvider(
            sync_session_factory=bundle.sync_session_factory,
            async_session_factory=bundle.async_session_factory,
        )
        instance = cls(provider)
        instance._bundle = bundle
        return instance

    @property
    def engine(self) -> Engine | None:
        """Return the underlying sync engine, if available."""
        if self._bundle is not None:
            return self._bundle.sync_engine
        return None

    @property
    def async_engine(self) -> AsyncEngine | None:
        """Return the underlying async engine, if available."""
        if self._bundle is not None:
            return self._bundle.async_engine
        return None

    def unit_of_work(self, *, auto_commit: bool = True) -> UnitOfWork:
        """Create a synchronous unit of work through the sync facade."""
        return self.sync.unit_of_work(auto_commit=auto_commit)

    def async_unit_of_work(self, *, auto_commit: bool = True) -> AsyncUnitOfWork:
        """Create an asynchronous unit of work through the async facade."""
        return self.async_.unit_of_work(auto_commit=auto_commit)

    # -- Sync delegate methods --------------------------------------------------

    def of[M](self, model: type[M]) -> SyncModelStore[M]:
        """Return a model-bound sync view."""
        return self.sync.of(model)

    def insert[TModel](
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        """Insert an entity (delegates to sync facade)."""
        return cast(
            TModel,
            self.sync.insert(entity, session=session, commit=commit, refresh=refresh),
        )

    def insert_many[TModel](
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        """Insert multiple entities (delegates to sync facade)."""
        return cast(list[TModel], self.sync.insert_many(entities, session=session, commit=commit))

    def get[TModel](
        self, model: type[TModel], ident: object, *, session: Session | None = None
    ) -> TModel | None:
        """Fetch one entity by primary key (delegates to sync facade)."""
        return cast(TModel | None, self.sync.get(model, ident, session=session))

    def find_one[TModel](
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        session: Session | None = None,
    ) -> TModel | None:
        """Fetch the first matching entity (delegates to sync facade)."""
        return cast(
            TModel | None,
            self.sync.find_one(model, *filters, spec=spec, order=order, session=session),
        )

    def find_many[TModel](
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> list[TModel]:
        """Fetch all matching entities (delegates to sync facade)."""
        return cast(
            list[TModel],
            self.sync.find_many(
                model,
                *filters,
                spec=spec,
                order=order,
                limit=limit,
                offset=offset,
                session=session,
            ),
        )

    def paginate[TModel](
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: Session | None = None,
    ) -> Page[TModel]:
        """Return a page of entities and total count (delegates to sync facade)."""
        return cast(
            Page[TModel],
            self.sync.paginate(
                model,
                *filters,
                spec=spec,
                order=order,
                limit=limit,
                offset=offset,
                session=session,
            ),
        )

    def update_fields[TModel](
        self,
        model: type[TModel],
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching entities (delegates to sync facade)."""
        return self.sync.update_fields(
            model, values, *filters, spec=spec, session=session, commit=commit
        )

    def delete_where[TModel](
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Delete matching entities (delegates to sync facade)."""
        return self.sync.delete_where(model, *filters, spec=spec, session=session, commit=commit)

    def select_rows[TModel](
        self,
        model: type[TModel],
        spec: QuerySpec[TModel],
        *,
        session: Session | None = None,
    ) -> list[object]:
        """Fetch row-style results for column projections (delegates to sync facade)."""
        return self.sync.select_rows(model, spec, session=session)

    def select_scalars[TScalar](
        self, statement: Executable, *, session: Session | None = None
    ) -> list[TScalar]:
        """Execute a custom select and return scalar values (delegates to sync facade)."""
        return cast(list[TScalar], self.sync.select_scalars(statement, session=session))
