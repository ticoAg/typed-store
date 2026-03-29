"""Model binding and TypedStore composition root example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import TypedStore, TypedStoreModel


class Base(DeclarativeBase):
    """Example declarative base."""


class User(Base, TypedStoreModel):
    """Example user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)


ts = TypedStore.from_url("sqlite:///model_store_view_example.sqlite3")
assert ts.engine is not None
Base.metadata.create_all(ts.engine)

users = User.bind(ts.sync)

# bind-first model operations on the sync facade
users.insert(User(name="alice", role="admin"))
users.insert(User(name="bob", role="member"))
users.insert(User(name="carol", role="admin"))

# 内联 filter + order
admins = users.find_many(User.role == "admin", order=User.name.asc())
print("admins:", [u.name for u in admins])

# 分页
page = users.paginate(User.role == "admin", limit=1, offset=0)
print(f"page: {[u.name for u in page.items]} (total={page.total})")

users.insert(User(name="dave", role="member"))
members = users.find_many(User.role == "member", order=User.name.asc())
print("members:", [u.name for u in members])

found = users.get(1)
print("get(1):", found.name if found else None)
