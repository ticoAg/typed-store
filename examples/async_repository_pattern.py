"""Async repository and transaction oriented TypedStore example."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import (
    AsyncTypedStore,
    EngineConfig,
    QuerySpec,
    SessionProvider,
    build_engine_bundle,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Example declarative base."""


class User(Base):
    """Example user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)


@dataclass(slots=True)
class UserRepository:
    """Thin repository wrapping AsyncTypedStore for user operations."""

    store: AsyncTypedStore[User]

    async def add(self, user: User, *, session=None, commit: bool = False) -> User:
        return await self.store.insert(user, session=session, commit=commit)

    async def get_by_email(self, email: str, *, session=None) -> User | None:
        spec = QuerySpec[User].empty().where(User.email == email)
        return await self.store.find_one(User, spec, session=session)

    async def list_admins(self) -> list[User]:
        spec = QuerySpec[User].empty().where(User.role == "admin").order(User.id.asc())
        return await self.store.find_many(User, spec)


class UserService:
    """Service layer showing transaction composition with AsyncUnitOfWork."""

    def __init__(self, store: AsyncTypedStore[User]):
        self.store = store
        self.repo = UserRepository(store)

    async def register_admin(self, email: str) -> User:
        async with self.store.unit_of_work() as uow:
            existing = await self.repo.get_by_email(email, session=uow.session)
            if existing is not None:
                return existing
            user = User(email=email, role="admin")
            await self.repo.add(user, session=uow.session)
            return user


async def main() -> None:
    bundle = build_engine_bundle(
        async_config=EngineConfig(url="sqlite+aiosqlite:///async_repository_example.sqlite3")
    )
    assert bundle.async_engine is not None
    async with bundle.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    provider = SessionProvider(async_session_factory=bundle.async_session_factory)
    store = AsyncTypedStore[User](provider)
    service = UserService(store)

    await service.register_admin("alice@example.com")
    admins = await service.repo.list_admins()
    print([user.email for user in admins])
    await bundle.async_engine.dispose()


asyncio.run(main())
