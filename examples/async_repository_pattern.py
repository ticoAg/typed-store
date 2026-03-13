"""Async repository and transaction oriented TypedStore example."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import AsyncTypedStore


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
        return await self.store.find_one(User, User.email == email, session=session)

    async def list_admins(self) -> list[User]:
        return await self.store.find_many(User, User.role == "admin", order=User.id.asc())


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
    store = AsyncTypedStore.from_url("sqlite+aiosqlite:///async_repository_example.sqlite3")
    assert store.engine is not None
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    service = UserService(store)

    await service.register_admin("alice@example.com")
    admins = await service.repo.list_admins()
    print([user.email for user in admins])
    await store.engine.dispose()


asyncio.run(main())
