"""TypedStoreModel bind-first example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import SyncTypedStore, TypedStoreModel


class Base(DeclarativeBase):
    """Example declarative base."""


class User(Base, TypedStoreModel):
    """Example user model with Active Record mixin."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)


store = SyncTypedStore.from_url("sqlite:///model_mixin_example.sqlite3")
assert store.engine is not None
Base.metadata.create_all(store.engine)

users = User.bind(store)

# 绑定视图: insert / insert_many
users.insert(User(name="alice", role="admin"))
users.insert(User(name="bob", role="member"))
users.insert(User(name="carol", role="admin"))

users.insert_many([User(name="dave", role="member"), User(name="eve", role="admin")])

# 绑定视图: find_many (内联 filter + order)
admins = users.find_many(User.role == "admin", order=User.name.asc())
print("admins:", [u.name for u in admins])

# 绑定视图: find_one
first = users.find_one(User.name == "alice")
print("find_one:", first.name if first else None)

# 绑定视图: get (按主键)
user = users.get(1)
print("get(1):", user.name if user else None)

# 绑定视图: paginate
page = users.paginate(User.role == "admin", limit=2, offset=0)
print(f"page: {[u.name for u in page.items]} (total={page.total})")

# 绑定视图: update_fields
updated = users.update_fields({"role": "superadmin"}, User.name == "alice")
print(f"updated {updated} row(s)")
alice = users.find_one(User.name == "alice")
print(f"alice role: {alice.role if alice else None}")

# 绑定视图: delete_where
deleted = users.delete_where(User.role == "member")
print(f"deleted {deleted} member(s)")
remaining = users.find_many()
print("remaining:", [u.name for u in remaining])
