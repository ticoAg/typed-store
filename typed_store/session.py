"""Session provider abstractions for sync and async SQLAlchemy sessions."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from typed_store.errors import MissingAsyncSessionFactoryError, MissingSyncSessionFactoryError


@dataclass(slots=True)
class SessionProvider:
    """Provides sync and async session scopes for TypedStore."""

    sync_session_factory: sessionmaker | None = None
    async_session_factory: async_sessionmaker | None = None

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Yield a synchronous session and always close it afterwards."""
        if self.sync_session_factory is None:
            raise MissingSyncSessionFactoryError("Sync session factory is not configured.")

        session = self.sync_session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncIterator[AsyncSession]:
        """Yield an asynchronous session and always close it afterwards."""
        if self.async_session_factory is None:
            raise MissingAsyncSessionFactoryError("Async session factory is not configured.")

        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
