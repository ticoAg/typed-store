from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import Patch, Query, SyncTypedStore, TypedStoreModel


class Base(DeclarativeBase):
    pass


class User(Base, TypedStoreModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    role: Mapped[str]


store = SyncTypedStore.from_url("sqlite:///bulk_operations.sqlite3")
assert store.engine is not None
Base.metadata.create_all(store.engine)

users = User.bind(store)
users.insert_many(
    [
        User(name="alice", role="member"),
        User(name="bob", role="member"),
        User(name="eve", role="guest"),
    ]
)

updated = users.bulk_update(
    query=Query[User]().where(User.role == "member"),
    patch=Patch[User]({"role": "staff"}),
)
deleted = users.bulk_delete(query=Query[User]().where(User.role == "guest"))

print(f"bulk updated: {updated}")
print(f"bulk deleted: {deleted}")
