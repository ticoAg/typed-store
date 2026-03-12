"""Result value objects returned by TypedStore."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Page[T]:
    """A simple page container for paginated results."""

    items: list[T]
    total: int
    limit: int
    offset: int
