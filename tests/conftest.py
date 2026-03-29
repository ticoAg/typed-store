"""Shared test fixtures for TypedStore."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typed_store.engine import EngineConfig, build_engine_bundle
from typed_store.model import TypedStoreModel
from typed_store.session import SessionProvider
from typed_store.store import TypedStore


class Base(AsyncAttrs, DeclarativeBase):
    """Test declarative base."""


class Widget(Base, TypedStoreModel):
    """Simple model used by sync and async tests."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


class Team(Base, TypedStoreModel):
    """Parent model used to validate loader options."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    members: Mapped[list[Member]] = relationship(back_populates="team")


class Member(Base, TypedStoreModel):
    """Child model used to validate loader options."""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    team: Mapped[Team] = relationship(back_populates="members")


@pytest.fixture
def db_urls(tmp_path: Path) -> tuple[str, str]:
    db_file = tmp_path / "typed_store.sqlite"
    sync_url = f"sqlite:///{db_file}"
    async_url = f"sqlite+aiosqlite:///{db_file}"
    return sync_url, async_url


@pytest.fixture
def engine_bundle(db_urls: tuple[str, str]):
    sync_url, async_url = db_urls
    bundle = build_engine_bundle(
        sync_config=EngineConfig(url=sync_url),
        async_config=EngineConfig(url=async_url),
    )
    assert bundle.sync_engine is not None
    Base.metadata.create_all(bundle.sync_engine)
    yield bundle
    if bundle.async_engine is not None:
        import asyncio

        asyncio.run(bundle.async_engine.dispose())
    if bundle.sync_engine is not None:
        bundle.sync_engine.dispose()


@pytest.fixture
def provider(engine_bundle):
    return SessionProvider(
        sync_session_factory=engine_bundle.sync_session_factory,
        async_session_factory=engine_bundle.async_session_factory,
    )


@pytest.fixture
def store(provider: SessionProvider):
    return TypedStore(provider)
