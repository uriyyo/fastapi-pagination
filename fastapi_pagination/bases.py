from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Sequence, Type, TypeVar

from pydantic.generics import GenericModel
from typing_extensions import Protocol

if TYPE_CHECKING:
    from .params import LimitOffsetPaginationParams  # pragma no cover

T = TypeVar("T")
C = TypeVar("C")


class AbstractParams(Protocol):
    @abstractmethod
    def to_limit_offset(self) -> LimitOffsetPaginationParams:
        pass  # pragma: no cover


class AbstractPage(GenericModel, Generic[T], ABC):
    @classmethod
    @abstractmethod
    def create(cls: Type[C], items: Sequence[T], total: int, params: AbstractParams) -> C:
        pass  # pragma: no cover

    class Config:
        arbitrary_types_allowed = True


__all__ = [
    "AbstractPage",
    "AbstractParams",
]
