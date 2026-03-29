"""Bind-first model helpers built on top of TypedStore."""

from __future__ import annotations

from inspect import iscoroutinefunction
from typing import Self, cast, overload

from typed_store.bound_model import AsyncBoundModelView, SyncBoundModelView
from typed_store.errors import InvalidStoreBindingError
from typed_store.protocols import AsyncModelBoundStoreProtocol, SyncModelBoundStoreProtocol


class TypedStoreModel:
    """Mixin giving ORM models a pure functional bind(store) entrypoint."""

    @classmethod
    @overload
    def bind(
        cls: type[Self], store: SyncModelBoundStoreProtocol[object]
    ) -> SyncBoundModelView[Self]: ...

    @classmethod
    @overload
    def bind(
        cls: type[Self], store: AsyncModelBoundStoreProtocol[object]
    ) -> AsyncBoundModelView[Self]: ...

    @classmethod
    def bind(
        cls: type[Self],
        store: SyncModelBoundStoreProtocol[object] | AsyncModelBoundStoreProtocol[object],
    ) -> SyncBoundModelView[Self] | AsyncBoundModelView[Self]:
        """Bind this model to a concrete store and return a bound view."""
        insert = getattr(store, "insert", None)
        if isinstance(store, AsyncModelBoundStoreProtocol) and iscoroutinefunction(insert):
            return AsyncBoundModelView(cls, cast(AsyncModelBoundStoreProtocol[object], store))
        if isinstance(store, SyncModelBoundStoreProtocol) and not iscoroutinefunction(insert):
            return SyncBoundModelView(cls, cast(SyncModelBoundStoreProtocol[object], store))
        raise InvalidStoreBindingError(
            "bind() requires a store that implements the TypedStore bind protocols."
        )
