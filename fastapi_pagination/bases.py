from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Generic, Sequence, Type, TypeVar

from pydantic.generics import GenericModel
from pydantic.types import conint

T = TypeVar("T")
C = TypeVar("C")


@dataclass
class RawParams:
    limit: int
    offset: int


class AbstractParams(ABC):
    @abstractmethod
    def to_raw_params(self) -> RawParams:
        pass  # pragma: no cover


class AbstractPage(GenericModel, Generic[T], ABC):
    __params_type__: ClassVar[Type[AbstractParams]]

    @classmethod
    @abstractmethod
    def create(cls: Type[C], items: Sequence[T], total: int, params: AbstractParams) -> C:
        pass  # pragma: no cover

    class Config:
        arbitrary_types_allowed = True


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: conint(ge=0)  # type: ignore


__all__ = [
    "AbstractPage",
    "AbstractParams",
    "BasePage",
    "RawParams",
]
