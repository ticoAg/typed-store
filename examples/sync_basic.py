"""Minimal synchronous TypedStore example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import PageRequest, Query, SyncTypedStore


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
query = Query[User]().where(User.name == "alice")
rows = store.find_many(User, query=query)
page = store.paginate(User, query=query, page=PageRequest(limit=10, offset=0))
print([row.name for row in rows])
print(page.total)
