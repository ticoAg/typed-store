"""Top-level TypedStore entrypoint bundling sync and async facades."""

from __future__ import annotations

from typed_store.async_store import AsyncTypedStore
from typed_store.session import SessionProvider
from typed_store.sync import SyncTypedStore
from typed_store.uow import AsyncUnitOfWork, UnitOfWork


class TypedStore:
    """Bundle synchronous and asynchronous TypedStore facades under one provider."""

    def __init__(self, provider: SessionProvider):
        self.provider = provider
        self.sync: SyncTypedStore[object] = SyncTypedStore(provider)
        self.async_: AsyncTypedStore[object] = AsyncTypedStore(provider)

    def unit_of_work(self, *, auto_commit: bool = True) -> UnitOfWork:
        """Create a synchronous unit of work through the sync facade."""
        return self.sync.unit_of_work(auto_commit=auto_commit)

    def async_unit_of_work(self, *, auto_commit: bool = True) -> AsyncUnitOfWork:
        """Create an asynchronous unit of work through the async facade."""
        return self.async_.unit_of_work(auto_commit=auto_commit)
