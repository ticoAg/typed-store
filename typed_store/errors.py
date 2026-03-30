"""Custom exceptions raised by TypedStore."""


class TypedStoreError(Exception):
    """Base exception for TypedStore failures."""


class TypedStoreConfigurationError(TypedStoreError):
    """Raised when the store is missing a required dependency or setting."""


class MissingSyncSessionFactoryError(TypedStoreConfigurationError):
    """Raised when a sync operation is requested without a sync session factory."""


class MissingAsyncSessionFactoryError(TypedStoreConfigurationError):
    """Raised when an async operation is requested without an async session factory."""


class MissingGlobalStoreError(TypedStoreConfigurationError):
    """Raised when the model mixin is used without a configured default store."""


class InvalidStoreBindingError(TypedStoreConfigurationError):
    """Raised when a model mixin receives an unsupported store binding."""


class ProjectionPaginationError(TypedStoreError):
    """Raised when pagination is requested for a column projection query."""


class BulkQueryShapeError(TypedStoreError):
    """Raised when a Query contains fields invalid for SQL bulk mutation."""
