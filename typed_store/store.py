"""Top-level TypedStore entrypoint bundling sync and async facades."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Engine

from typed_store.async_store import AsyncTypedStore
from typed_store.engine import EngineBundle, EngineConfig, build_engine_bundle
from typed_store.session import SessionProvider
from typed_store.sync import SyncTypedStore
from typed_store.uow import AsyncUnitOfWork, UnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class TypedStore:
    """Bundle synchronous and asynchronous TypedStore facades under one provider."""

    _bundle: EngineBundle | None

    def __init__(self, provider: SessionProvider):
        self.provider = provider
        self.sync: SyncTypedStore[object] = SyncTypedStore(provider)
        self.async_: AsyncTypedStore[object] = AsyncTypedStore(provider)
        self._bundle = None

    @classmethod
    def from_url(
        cls,
        url: str | None = None,
        *,
        async_url: str | None = None,
        echo: bool = False,
        **engine_options: Any,
    ) -> TypedStore:
        """Create a TypedStore from database URL(s) in one step."""
        bundle = build_engine_bundle(
            sync_config=EngineConfig(url=url, echo=echo, engine_options=engine_options)
            if url
            else None,
            async_config=EngineConfig(url=async_url, echo=echo, engine_options=engine_options)
            if async_url
            else None,
        )
        provider = SessionProvider(
            sync_session_factory=bundle.sync_session_factory,
            async_session_factory=bundle.async_session_factory,
        )
        instance = cls(provider)
        instance._bundle = bundle
        return instance

    @property
    def engine(self) -> Engine | None:
        """Return the underlying sync engine, if available."""
        if self._bundle is not None:
            return self._bundle.sync_engine
        return None

    @property
    def async_engine(self) -> AsyncEngine | None:
        """Return the underlying async engine, if available."""
        if self._bundle is not None:
            return self._bundle.async_engine
        return None

    def unit_of_work(self, *, auto_commit: bool = True) -> UnitOfWork:
        """Create a synchronous unit of work through the sync facade."""
        return self.sync.unit_of_work(auto_commit=auto_commit)

    def async_unit_of_work(self, *, auto_commit: bool = True) -> AsyncUnitOfWork:
        """Create an asynchronous unit of work through the async facade."""
        return self.async_.unit_of_work(auto_commit=auto_commit)

    def dispose(self) -> None:
        """Dispose sync resources through the sync facade."""
        self.sync.dispose()

    def close(self) -> None:
        """Close sync resources through the sync facade."""
        self.sync.close()

    async def aclose(self) -> None:
        """Close async resources through the async facade."""
        await self.async_.aclose()
