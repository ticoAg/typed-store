"""Engine and session factory helpers for TypedStore."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Engine
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine as sa_create_async_engine,
)
from sqlalchemy.orm import sessionmaker


@dataclass(slots=True)
class EngineConfig:
    """Configuration used to build a SQLAlchemy engine."""

    url: str
    echo: bool = False
    future: bool = True
    pool_pre_ping: bool = True
    connect_args: dict[str, Any] = field(default_factory=dict)
    engine_options: dict[str, Any] = field(default_factory=dict)

    def to_kwargs(self) -> dict[str, Any]:
        """Return keyword arguments accepted by SQLAlchemy engine builders."""
        kwargs: dict[str, Any] = {
            "echo": self.echo,
            "future": self.future,
            "pool_pre_ping": self.pool_pre_ping,
        }
        if self.connect_args:
            kwargs["connect_args"] = dict(self.connect_args)
        kwargs.update(self.engine_options)
        return kwargs


@dataclass(slots=True)
class EngineBundle:
    """Container bundling engines and their session factories."""

    sync_engine: Engine | None = None
    async_engine: AsyncEngine | None = None
    sync_session_factory: sessionmaker | None = None
    async_session_factory: async_sessionmaker | None = None


def create_sync_engine(config: EngineConfig) -> Engine:
    """Create a synchronous SQLAlchemy engine from a config object."""
    return sa_create_engine(config.url, **config.to_kwargs())


def create_async_engine(config: EngineConfig) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine from a config object."""
    return sa_create_async_engine(config.url, **config.to_kwargs())


def build_engine_bundle(
    *,
    sync_config: EngineConfig | None = None,
    async_config: EngineConfig | None = None,
    expire_on_commit: bool = False,
    autoflush: bool = False,
) -> EngineBundle:
    """Build engines and matching session factories in one step."""
    bundle = EngineBundle()

    if sync_config is not None:
        bundle.sync_engine = create_sync_engine(sync_config)
        bundle.sync_session_factory = sessionmaker(
            bind=bundle.sync_engine,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit,
        )

    if async_config is not None:
        bundle.async_engine = create_async_engine(async_config)
        bundle.async_session_factory = async_sessionmaker(
            bind=bundle.async_engine,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit,
        )

    return bundle
