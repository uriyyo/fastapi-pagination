from abc import ABC, abstractmethod
from collections import ChainMap
from dataclasses import dataclass
from functools import wraps
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Mapping,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from pydantic import BaseModel, create_model
from pydantic.generics import GenericModel
from pydantic.types import conint

T = TypeVar("T")
C = TypeVar("C")

TAbstractPage = TypeVar("TAbstractPage", bound="AbstractPage")


@dataclass
class RawParams:
    limit: int
    offset: int


class AbstractParams(ABC):
    @abstractmethod
    def to_raw_params(self) -> RawParams:
        pass


def _create_params(cls: Type[AbstractParams], fields: Dict[str, Any]) -> Mapping[str, Any]:
    if not issubclass(cls, BaseModel):
        raise ValueError(f"{cls.__name__} must be subclass of BaseModel")

    incorrect = sorted(fields.keys() - cls.__fields__.keys())
    if incorrect:
        ending = "s" if len(incorrect) > 1 else ""
        raise ValueError(f"Unknown field{ending} {', '.join(incorrect)}")

    anns = ChainMap(*(obj.__dict__.get("__annotations__", {}) for obj in cls.mro()))
    return {name: (anns[name], val) for name, val in fields.items()}


class AbstractPage(GenericModel, Generic[T], ABC):
    __params_type__: ClassVar[Type[AbstractParams]]

    @classmethod
    @abstractmethod
    def create(cls: Type[C], items: Sequence[T], total: int, params: AbstractParams) -> C:
        pass

    @classmethod
    def with_custom_options(cls: Type[TAbstractPage], **kwargs: Any) -> Type[TAbstractPage]:
        params_cls = cast(Type[AbstractPage], cls).__params_type__

        custom_params: Any = create_model(
            params_cls.__name__,
            __base__=params_cls,
            **_create_params(params_cls, kwargs),
        )

        if cls.__concrete__:
            bases = (cls,)
        else:
            params = tuple(TypeVar(f"T{i}") for i, _ in enumerate(cls.__parameters__))
            bases = (cls[params], Generic[params])  # type: ignore

        @wraps(cls, updated=())
        class CustomPage(*bases):  # type: ignore
            __params_type__: ClassVar[Type[AbstractParams]] = custom_params

        return cast(Type[TAbstractPage], CustomPage)

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
