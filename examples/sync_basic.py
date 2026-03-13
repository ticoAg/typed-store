"""Minimal synchronous TypedStore example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import SyncTypedStore


class Base(DeclarativeBase):
    """Example declarative base."""


class User(Base):
    """Example model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


store = SyncTypedStore.from_url("sqlite:///sync_example.sqlite3")
assert store.engine is not None
Base.metadata.create_all(store.engine)

store.insert(User(name="alice"))
rows = store.find_many(User, User.name == "alice")
print([row.name for row in rows])
