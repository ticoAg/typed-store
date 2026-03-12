"""Synchronous TypedStore facade."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from typed_store.errors import ProjectionPaginationError
from typed_store.query_spec import QuerySpec
from typed_store.results import Page
from typed_store.session import SessionProvider
from typed_store.uow import UnitOfWork


class SyncTypedStore[TModel]:
    """A synchronous, type-oriented data access facade built on top of SQLAlchemy."""

    def __init__(self, provider: SessionProvider):
        self.provider = provider

    def unit_of_work(self, *, auto_commit: bool = True) -> UnitOfWork:
        """Create a synchronous unit of work."""
        return UnitOfWork(self.provider, auto_commit=auto_commit)

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
        spec: QuerySpec[TModel] | None = None,
        *,
        session: Session | None = None,
    ) -> TModel | None:
        """Fetch the first matching entity using a sync session."""
        active_spec = spec or QuerySpec[TModel].empty()
        stmt = active_spec.paginate(limit=1, offset=0).build_select(model)
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
        spec: QuerySpec[TModel] | None = None,
        *,
        session: Session | None = None,
    ) -> list[TModel]:
        """Fetch all matching entities using a sync session."""
        active_spec = spec or QuerySpec[TModel].empty()
        stmt = active_spec.build_select(model)
        if session is not None:
            session.flush()
            result = session.execute(stmt)
            return list(result.scalars().all())

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            return list(result.scalars().all())

    def select_rows(
        self,
        model: type[TModel],
        spec: QuerySpec[TModel],
        *,
        session: Session | None = None,
    ) -> list[object]:
        """Fetch row-style results for explicit column selections."""
        stmt = spec.build_select(model)
        if session is not None:
            session.flush()
            result = session.execute(stmt)
            return list(result.all())

        with self.provider.get_session() as managed_session:
            result = managed_session.execute(stmt)
            return list(result.all())

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
        spec: QuerySpec[TModel] | None = None,
        *,
        session: Session | None = None,
    ) -> Page[TModel]:
        """Return a page of entities and the matching total count."""
        active_spec = spec or QuerySpec[TModel].empty()
        if active_spec.columns is not None:
            raise ProjectionPaginationError(
                "paginate() only supports entity queries; use select_rows() for column projections."
            )

        count_stmt = select(func.count()).select_from(active_spec.count_select(model).subquery())
        page_stmt = active_spec.build_select(model)
        limit = active_spec.limit or 0
        offset = active_spec.offset or 0

        if session is not None:
            session.flush()
            total = int(session.execute(count_stmt).scalar_one())
            items = list(session.execute(page_stmt).scalars().all())
            return Page(items=items, total=total, limit=limit, offset=offset)

        with self.provider.get_session() as managed_session:
            total = int(managed_session.execute(count_stmt).scalar_one())
            items = list(managed_session.execute(page_stmt).scalars().all())
            return Page(items=items, total=total, limit=limit, offset=offset)

    def update_fields(
        self,
        model: type[TModel],
        values: Mapping[str, object],
        spec: QuerySpec[TModel] | None = None,
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Update matching entities by mutating loaded ORM objects."""
        active_spec = spec or QuerySpec[TModel].empty()
        if active_spec.columns is not None:
            raise ValueError("update_fields() does not support column projections.")

        if session is not None:
            items = self.find_many(model, active_spec, session=session)
            for item in items:
                for key, value in values.items():
                    setattr(item, key, value)
            if commit:
                session.commit()
            return len(items)

        with self.provider.get_session() as managed_session:
            items = self.find_many(model, active_spec, session=managed_session)
            for item in items:
                for key, value in values.items():
                    setattr(item, key, value)
            if commit:
                managed_session.commit()
            return len(items)

    def delete_where(
        self,
        model: type[TModel],
        spec: QuerySpec[TModel] | None = None,
        *,
        session: Session | None = None,
        commit: bool = True,
    ) -> int:
        """Delete matching entities by loading and removing ORM objects."""
        active_spec = spec or QuerySpec[TModel].empty()
        if session is not None:
            items = self.find_many(model, active_spec, session=session)
            for item in items:
                session.delete(item)
            if commit:
                session.commit()
            return len(items)

        with self.provider.get_session() as managed_session:
            items = self.find_many(model, active_spec, session=managed_session)
            for item in items:
                managed_session.delete(item)
            if commit:
                managed_session.commit()
            return len(items)

    @staticmethod
    def equals_spec(model: type[TModel], **kwargs: object) -> QuerySpec[TModel]:
        """Build a query spec from exact-match keyword arguments."""
        spec = QuerySpec[TModel].empty()
        for key, value in kwargs.items():
            spec = spec.where(getattr(model, key) == value)
        return spec
