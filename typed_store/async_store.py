"""Asynchronous TypedStore facade."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.sql.expression import Executable

from typed_store.engine import EngineBundle, EngineConfig, build_engine_bundle
from typed_store.errors import ProjectionPaginationError
from typed_store.query_spec import FilterClause, OrderClause, QuerySpec
from typed_store.results import Page
from typed_store.session import SessionProvider
from typed_store.uow import AsyncUnitOfWork


class AsyncTypedStore[TModel]:
    """An asynchronous, type-oriented data access facade built on top of SQLAlchemy."""

    _bundle: EngineBundle | None

    def __init__(self, provider: SessionProvider):
        self.provider = provider
        self._bundle = None

    @classmethod
    def from_url(
        cls, url: str, *, echo: bool = False, **engine_options: Any
    ) -> AsyncTypedStore[Any]:
        """Create an AsyncTypedStore from a database URL in one step."""
        bundle = build_engine_bundle(
            async_config=EngineConfig(url=url, echo=echo, engine_options=engine_options),
        )
        provider = SessionProvider(async_session_factory=bundle.async_session_factory)
        instance: AsyncTypedStore[Any] = cls(provider)
        instance._bundle = bundle
        return instance

    @property
    def engine(self) -> AsyncEngine | None:
        """Return the underlying async engine, if available."""
        if self._bundle is not None:
            return self._bundle.async_engine
        return None

    def unit_of_work(self, *, auto_commit: bool = True) -> AsyncUnitOfWork:
        """Create an asynchronous unit of work."""
        return AsyncUnitOfWork(self.provider, auto_commit=auto_commit)

    async def dispose(self) -> None:
        """Dispose the underlying async engine if available."""
        if self.engine is not None:
            await self.engine.dispose()

    async def aclose(self) -> None:
        """Close async store resources."""
        await self.dispose()

    async def insert(
        self,
        entity: TModel,
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
        refresh: bool = False,
    ) -> TModel:
        """Insert an entity using an async session."""
        if session is not None:
            session.add(entity)
            if commit:
                await session.commit()
            if refresh:
                await session.refresh(entity)
            return entity

        async with self.provider.get_async_session() as managed_session:
            managed_session.add(entity)
            if commit:
                await managed_session.commit()
            if refresh:
                await managed_session.refresh(entity)
            return entity

    async def insert_many(
        self,
        entities: Sequence[TModel],
        *,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> list[TModel]:
        """Insert multiple entities using an async session."""
        items = list(entities)
        if session is not None:
            session.add_all(items)
            if commit:
                await session.commit()
            return items

        async with self.provider.get_async_session() as managed_session:
            managed_session.add_all(items)
            if commit:
                await managed_session.commit()
            return items

    async def get(
        self, model: type[TModel], ident: object, *, session: AsyncSession | None = None
    ) -> TModel | None:
        """Fetch one entity by primary key using an async session."""
        if session is not None:
            return await session.get(model, ident)

        async with self.provider.get_async_session() as managed_session:
            return await managed_session.get(model, ident)

    async def find_one(
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        session: AsyncSession | None = None,
    ) -> TModel | None:
        """Fetch the first matching entity using an async session."""
        from typed_store.query_spec import _merge_spec

        active_spec = _merge_spec(*filters, spec=spec, order=order)
        stmt = active_spec.paginate(limit=1, offset=0).build_select(model)
        if session is not None:
            await session.flush()
            result = await session.execute(stmt)
            return result.scalars().first()

        async with self.provider.get_async_session() as managed_session:
            result = await managed_session.execute(stmt)
            return result.scalars().first()

    async def find_many(
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: AsyncSession | None = None,
    ) -> list[TModel]:
        """Fetch all matching entities using an async session."""
        from typed_store.query_spec import _merge_spec

        active_spec = _merge_spec(*filters, spec=spec, order=order, limit=limit, offset=offset)
        stmt = active_spec.build_select(model)
        if session is not None:
            await session.flush()
            result = await session.execute(stmt)
            return list(result.scalars().all())

        async with self.provider.get_async_session() as managed_session:
            result = await managed_session.execute(stmt)
            return list(result.scalars().all())

    async def select_rows(
        self,
        model: type[TModel],
        spec: QuerySpec[TModel],
        *,
        session: AsyncSession | None = None,
    ) -> list[object]:
        """Fetch row-style results for explicit column selections."""
        stmt = spec.build_select(model)
        if session is not None:
            await session.flush()
            result = await session.execute(stmt)
            return list(result.all())

        async with self.provider.get_async_session() as managed_session:
            result = await managed_session.execute(stmt)
            return list(result.all())

    async def select_scalars[TScalar](
        self, statement: Executable, *, session: AsyncSession | None = None
    ) -> list[TScalar]:
        """Execute a custom async select statement and return scalar values."""
        if session is not None:
            await session.flush()
            result = await session.execute(statement)
            return list(result.scalars().all())

        async with self.provider.get_async_session() as managed_session:
            result = await managed_session.execute(statement)
            return list(result.scalars().all())

    async def paginate(
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        order: OrderClause | tuple[OrderClause, ...] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        session: AsyncSession | None = None,
    ) -> Page[TModel]:
        """Return a page of entities and the matching total count."""
        from typed_store.query_spec import _merge_spec

        active_spec = _merge_spec(*filters, spec=spec, order=order, limit=limit, offset=offset)
        if active_spec.columns is not None:
            raise ProjectionPaginationError(
                "paginate() only supports entity queries; use select_rows() for column projections."
            )

        count_stmt = select(func.count()).select_from(active_spec.count_select(model).subquery())
        page_stmt = active_spec.build_select(model)
        limit = active_spec.limit or 0
        offset = active_spec.offset or 0

        if session is not None:
            await session.flush()
            total = int((await session.execute(count_stmt)).scalar_one())
            items = list((await session.execute(page_stmt)).scalars().all())
            return Page(items=items, total=total, limit=limit, offset=offset)

        async with self.provider.get_async_session() as managed_session:
            total = int((await managed_session.execute(count_stmt)).scalar_one())
            items = list((await managed_session.execute(page_stmt)).scalars().all())
            return Page(items=items, total=total, limit=limit, offset=offset)

    async def update_fields(
        self,
        model: type[TModel],
        values: Mapping[str, object],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching entities by mutating loaded ORM objects."""
        from typed_store.query_spec import _merge_spec

        active_spec = _merge_spec(*filters, spec=spec)
        if active_spec.columns is not None:
            raise ValueError("update_fields() does not support column projections.")

        if session is not None:
            items = await self.find_many(model, spec=active_spec, session=session)
            for item in items:
                for key, value in values.items():
                    setattr(item, key, value)
            if commit:
                await session.commit()
            return len(items)

        async with self.provider.get_async_session() as managed_session:
            items = await self.find_many(model, spec=active_spec, session=managed_session)
            for item in items:
                for key, value in values.items():
                    setattr(item, key, value)
            if commit:
                await managed_session.commit()
            return len(items)

    async def delete_where(
        self,
        model: type[TModel],
        *filters: FilterClause,
        spec: QuerySpec[TModel] | None = None,
        session: AsyncSession | None = None,
        commit: bool = True,
    ) -> int:
        """Delete matching entities by loading and removing ORM objects."""
        from typed_store.query_spec import _merge_spec

        active_spec = _merge_spec(*filters, spec=spec)
        if session is not None:
            items = await self.find_many(model, spec=active_spec, session=session)
            for item in items:
                await session.delete(item)
            if commit:
                await session.commit()
            return len(items)

        async with self.provider.get_async_session() as managed_session:
            items = await self.find_many(model, spec=active_spec, session=managed_session)
            for item in items:
                await managed_session.delete(item)
            if commit:
                await managed_session.commit()
            return len(items)
