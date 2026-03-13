"""Minimal asynchronous TypedStore example."""

from __future__ import annotations

import asyncio

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import AsyncTypedStore


class Base(AsyncAttrs, DeclarativeBase):
    """Example declarative base."""


class User(Base):
    """Example model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


async def main() -> None:
    store = AsyncTypedStore.from_url("sqlite+aiosqlite:///async_example.sqlite3")
    assert store.engine is not None
    async with store.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await store.insert(User(name="alice"))
    rows = await store.find_many(User, User.name == "alice")
    print([row.name for row in rows])
    await store.engine.dispose()


asyncio.run(main())
