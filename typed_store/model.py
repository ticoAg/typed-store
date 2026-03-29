"""Bind-first model helpers built on top of TypedStore."""

from __future__ import annotations

from typing import Self, cast, overload

from typed_store.async_store import AsyncTypedStore
from typed_store.bound_model import AsyncBoundModelView, SyncBoundModelView
from typed_store.errors import InvalidStoreBindingError
from typed_store.sync import SyncTypedStore


class TypedStoreModel:
    """Mixin giving ORM models a pure functional bind(store) entrypoint."""

    @classmethod
    @overload
    def bind(cls: type[Self], store: SyncTypedStore[object]) -> SyncBoundModelView[Self]: ...

    @classmethod
    @overload
    def bind(cls: type[Self], store: AsyncTypedStore[object]) -> AsyncBoundModelView[Self]: ...

    @classmethod
    def bind(
        cls: type[Self], store: SyncTypedStore[object] | AsyncTypedStore[object]
    ) -> SyncBoundModelView[Self] | AsyncBoundModelView[Self]:
        """Bind this model to a concrete store and return a bound view."""
        if isinstance(store, SyncTypedStore):
            return SyncBoundModelView(cls, cast(SyncTypedStore[object], store))
        if isinstance(store, AsyncTypedStore):
            return AsyncBoundModelView(cls, cast(AsyncTypedStore[object], store))
        raise InvalidStoreBindingError(
            "bind() requires a SyncTypedStore or AsyncTypedStore instance."
        )
