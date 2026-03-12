"""Unit-of-work helpers for TypedStore."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from typed_store.session import SessionProvider


class UnitOfWork:
    """Sync unit-of-work wrapper around a session provider."""

    def __init__(self, provider: SessionProvider, *, auto_commit: bool = True):
        self.provider = provider
        self.auto_commit = auto_commit
        self.session: Session | None = None
        self._ctx: AbstractContextManager[Session] | None = None

    def __enter__(self) -> Self:
        self._ctx = self.provider.get_session()
        self.session = self._ctx.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self.session is not None
        try:
            if exc_type is None and self.auto_commit:
                self.session.commit()
            elif exc_type is not None:
                self.session.rollback()
        finally:
            assert self._ctx is not None
            self._ctx.__exit__(exc_type, exc, tb)

    def commit(self) -> None:
        """Commit the current transaction."""
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized.")
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized.")
        self.session.rollback()


class AsyncUnitOfWork:
    """Async unit-of-work wrapper around a session provider."""

    def __init__(self, provider: SessionProvider, *, auto_commit: bool = True):
        self.provider = provider
        self.auto_commit = auto_commit
        self.session: AsyncSession | None = None
        self._ctx: AbstractAsyncContextManager[AsyncSession] | None = None

    async def __aenter__(self) -> Self:
        self._ctx = self.provider.get_async_session()
        self.session = await self._ctx.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self.session is not None
        try:
            if exc_type is None and self.auto_commit:
                await self.session.commit()
            elif exc_type is not None:
                await self.session.rollback()
        finally:
            assert self._ctx is not None
            await self._ctx.__aexit__(exc_type, exc, tb)

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self.session is None:
            raise RuntimeError("AsyncUnitOfWork session is not initialized.")
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self.session is None:
            raise RuntimeError("AsyncUnitOfWork session is not initialized.")
        await self.session.rollback()
