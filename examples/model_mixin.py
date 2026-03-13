"""TypedStoreModel Active Record mixin example."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import SyncTypedStore, TypedStoreModel, clear_default_store, set_default_store


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

# 绑定全局默认 store
set_default_store(store)

# 实例方法: insert
User(name="alice", role="admin").insert()
User(name="bob", role="member").insert()
User(name="carol", role="admin").insert()

# 类方法: insert_many
User.insert_many([User(name="dave", role="member"), User(name="eve", role="admin")])

# 类方法: find_many (内联 filter + order)
admins = User.find_many(User.role == "admin", order=User.name.asc())
print("admins:", [u.name for u in admins])

# 类方法: find_one
first = User.find_one(User.name == "alice")
print("find_one:", first.name if first else None)

# 类方法: get (按主键)
user = User.get(1)
print("get(1):", user.name if user else None)

# 类方法: paginate
page = User.paginate(User.role == "admin", limit=2, offset=0)
print(f"page: {[u.name for u in page.items]} (total={page.total})")

# 类方法: update_fields
updated = User.update_fields({"role": "superadmin"}, User.name == "alice")
print(f"updated {updated} row(s)")
alice = User.find_one(User.name == "alice")
print(f"alice role: {alice.role if alice else None}")

# 类方法: delete_where
deleted = User.delete_where(User.role == "member")
print(f"deleted {deleted} member(s)")
remaining = User.find_many()
print("remaining:", [u.name for u in remaining])

clear_default_store()
