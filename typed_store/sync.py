"""Synchronous TypedStore facade."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import Engine, func, select
from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from typed_store.engine import EngineBundle, EngineConfig, build_engine_bundle
from typed_store.protocols import (
    StatementExecutorProtocol,
    SyncModelBoundStoreProtocol,
    TransactionalStoreProtocol,
)
from typed_store.results import Page
from typed_store.session import SessionProvider
from typed_store.specs import PageRequest, Patch, ProjectionQuery, Query
from typed_store.uow import UnitOfWork


class SyncTypedStore[TModel](
    SyncModelBoundStoreProtocol[TModel],
    StatementExecutorProtocol,
    TransactionalStoreProtocol,
):
    """A synchronous, type-oriented data access facade built on top of SQLAlchemy."""

    _bundle: EngineBundle | None

    def __init__(self, provider: SessionProvider):
        self.provider = provider
        self._bundle = None

    @classmethod
    def from_url(
        cls, url: str, *, echo: bool = False, **engine_options: Any
    ) -> SyncTypedStore[Any]:
        """Create a SyncTypedStore from a database URL in one step."""
        bundle = build_engine_bundle(
            sync_config=EngineConfig(url=url, echo=echo, engine_options=engine_options),
        )
        provider = SessionProvider(sync_session_factory=bundle.sync_session_factory)
        instance: SyncTypedStore[Any] = cls(provider)
        instance._bundle = bundle
        return instance

    @property
    def engine(self) -> Engine | None:
        """Return the underlying sync engine, if available."""
        if self._bundle is not None:
            return self._bundle.sync_engine
        return None

    def unit_of_work(self, *, auto_commit: bool = True) -> UnitOfWork:
        """Create a synchronous unit of work."""
        return UnitOfWork(self.provider, auto_commit=auto_commit)

    def dispose(self) -> None:
        """Dispose the underlying sync engine if available."""
        if self.engine is not None:
            self.engine.dispose()

    def close(self) -> None:
        """Close sync store resources."""
        self.dispose()

    def insert(
        self,
        entity: TModel,
        *,
        session: Session | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        """Insert an entity using a sync session."""
        if session is not None:
            session.add(entity)
            if commit:
                session.commit()
            if refresh:
                session.refresh(entity)
            return entity

        with self.provider.get_session() as managed_session:
            managed_session.add(entity)
            if commit:
                managed_session.commit()
            if refresh:
                managed_session.refresh(entity)
            return entity

    def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        """Insert multiple entities using a sync session."""
        items = list(entities)
        if session is not None:
            session.add_all(items)
            if commit:
                session.commit()
            return items

        with self.provider.get_session() as managed_session:
            managed_session.add_all(items)
            if commit:
                managed_session.commit()
            return items

    def get(
        self, model: type[TModel], ident: object, *, session: Session | None = None
    ) -> TModel | None:
        """Fetch one entity by primary key using a sync session."""
        if session is not None:
            return session.get(model, ident)

        with self.provider.get_session() as managed_session:
            return managed_session.get(model, ident)

    def find_one(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> TModel | None:
        """Fetch the first matching entity using a sync session."""
        stmt = query.limit_to(1).offset_by(0).build_select(model)
        if session is not None:
            session.flush()
            result = session.execute(stmt)
            return result.scalars().first()

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            return result.scalars().first()

    def find_many(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> list[TModel]:
        """Fetch all matching entities using a sync session."""
        stmt = query.build_select(model)
        if session is not None:
            session.flush()
            result = session.execute(stmt)
            return list(result.scalars().all())

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            return list(result.scalars().all())

    def exists(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> bool:
        """Return whether any matching entity exists."""
        return self.count(model, query=query, session=session) > 0

    def count(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
    ) -> int:
        """Return the count for the given query."""
        count_stmt = select(func.count()).select_from(query.count_select(model).subquery())
        if session is not None:
            session.flush()
            return int(session.execute(count_stmt).scalar_one())

        with self.provider.get_session() as managed_session:
            return int(managed_session.execute(count_stmt).scalar_one())

    def select_rows[TRow](
        self,
        model: type[object],
        *,
        projection: ProjectionQuery[TRow],
        session: Session | None = None,
    ) -> list[TRow]:
        """Fetch row-style results for explicit column selections."""
        stmt = projection.build_select(model)
        if session is not None:
            session.flush()
            result = session.execute(stmt)
            return cast(list[TRow], list(result.all()))

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            return cast(list[TRow], list(result.all()))

    def select_scalars[TScalar](
        self, statement: Executable, *, session: Session | None = None
    ) -> list[TScalar]:
        """Execute a custom select statement and return scalar values."""
        if session is not None:
            session.flush()
            result = session.execute(statement)
            return list(result.scalars().all())

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(statement)
            return list(result.scalars().all())

    def paginate(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        page: PageRequest,
        session: Session | None = None,
    ) -> Page[TModel]:
        """Return a page of entities and the matching total count."""
        total = self.count(model, query=query, session=session)
        page_query = query.limit_to(page.limit).offset_by(page.offset)
        page_stmt = page_query.build_select(model)

        if session is not None:
            session.flush()
            items = list(session.execute(page_stmt).scalars().all())
            return Page(items=items, total=total, limit=page.limit, offset=page.offset)

        with self.provider.get_session() as managed_session:
            items = list(managed_session.execute(page_stmt).scalars().all())
            return Page(items=items, total=total, limit=page.limit, offset=page.offset)

    def update(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching entities by mutating loaded ORM objects."""
        if session is not None:
            items = self.find_many(model, query=query, session=session)
            for item in items:
                for key, value in patch.values.items():
                    setattr(item, key, value)
            if commit:
                session.commit()
            return len(items)

        with self.provider.get_session() as managed_session:
            items = self.find_many(model, query=query, session=managed_session)
            for item in items:
                for key, value in patch.values.items():
                    setattr(item, key, value)
            if commit:
                managed_session.commit()
            return len(items)

    def bulk_update(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        patch: Patch[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching rows with a SQL bulk statement."""
        query.assert_bulk_compatible()
        stmt = sa_update(model).values(**dict(patch.values))
        if query.filters:
            stmt = stmt.where(*query.filters)
        if session is not None:
            result = session.execute(stmt)
            if commit:
                session.commit()
            return int(cast(CursorResult[Any], result).rowcount or 0)

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            if commit:
                managed_session.commit()
            return int(cast(CursorResult[Any], result).rowcount or 0)

    def delete(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Delete matching entities by loading and removing ORM objects."""
        if session is not None:
            items = self.find_many(model, query=query, session=session)
            for item in items:
                session.delete(item)
            if commit:
                session.commit()
            return len(items)

        with self.provider.get_session() as managed_session:
            items = self.find_many(model, query=query, session=managed_session)
            for item in items:
                managed_session.delete(item)
            if commit:
                managed_session.commit()
            return len(items)

    def bulk_delete(
        self,
        model: type[TModel],
        *,
        query: Query[TModel],
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Delete matching rows with a SQL bulk statement."""
        query.assert_bulk_compatible()
        stmt = sa_delete(model)
        if query.filters:
            stmt = stmt.where(*query.filters)
        if session is not None:
            result = session.execute(stmt)
            if commit:
                session.commit()
            return int(cast(CursorResult[Any], result).rowcount or 0)

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            if commit:
                managed_session.commit()
            return int(cast(CursorResult[Any], result).rowcount or 0)
