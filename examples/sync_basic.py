"""Minimal synchronous TypedStore example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import (
    EngineConfig,
    QuerySpec,
    SessionProvider,
    SyncTypedStore,
    build_engine_bundle,
)


class Base(DeclarativeBase):
    """Example declarative base."""


class User(Base):
    """Example model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


bundle = build_engine_bundle(sync_config=EngineConfig(url="sqlite:///sync_example.sqlite3"))
assert bundle.sync_engine is not None
Base.metadata.create_all(bundle.sync_engine)
provider = SessionProvider(sync_session_factory=bundle.sync_session_factory)
store = SyncTypedStore(provider)

store.insert(User(name="alice"))
rows = store.find_many(User, QuerySpec[User].empty().where(User.name == "alice"))
print([row.name for row in rows])
