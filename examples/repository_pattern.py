"""Repository and transaction oriented TypedStore example."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typed_store import Query, SyncTypedStore


class Base(DeclarativeBase):
    """Example declarative base."""


class User(Base):
    """Example user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)


@dataclass(slots=True)
class UserRepository:
    """Thin repository wrapping SyncTypedStore for user operations."""

    store: SyncTypedStore

    def add(self, user: User, *, session=None, commit: bool = False) -> User:
        return self.store.insert(user, session=session, commit=commit)

    def get_by_email(self, email: str, *, session=None) -> User | None:
        return self.store.find_one(
            User,
            query=Query[User]().where(User.email == email),
            session=session,
        )

    def list_admins(self) -> list[User]:
        return self.store.find_many(
            User,
            query=Query[User]().where(User.role == "admin").order(User.id.asc()),
        )


class UserService:
    """Service layer showing transaction composition with UnitOfWork."""

    def __init__(self, store: SyncTypedStore):
        self.store = store
        self.repo = UserRepository(store)

    def register_admin(self, email: str) -> User:
        with self.store.unit_of_work() as uow:
            existing = self.repo.get_by_email(email, session=uow.session)
            if existing is not None:
                return existing
            user = User(email=email, role="admin")
            self.repo.add(user, session=uow.session)
            return user


store = SyncTypedStore.from_url("sqlite:///repository_example.sqlite3")
assert store.engine is not None
Base.metadata.create_all(store.engine)
service = UserService(store)

service.register_admin("alice@example.com")
admins = service.repo.list_admins()
print([user.email for user in admins])
