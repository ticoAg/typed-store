"""Minimal asynchronous TypedStore example."""

from __future__ import annotations

import asyncio

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
    """Example model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


async def main() -> None:
    bundle = build_engine_bundle(
        async_config=EngineConfig(url="sqlite+aiosqlite:///async_example.sqlite3")
    )
    assert bundle.async_engine is not None
    async with bundle.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    provider = SessionProvider(async_session_factory=bundle.async_session_factory)
    store = AsyncTypedStore(provider)

    await store.insert(User(name="alice"))
    rows = await store.find_many(User, QuerySpec[User].empty().where(User.name == "alice"))
    print([row.name for row in rows])
    await bundle.async_engine.dispose()


asyncio.run(main())
