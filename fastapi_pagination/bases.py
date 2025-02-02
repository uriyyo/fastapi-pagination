from __future__ import annotations

__all__ = [
    "AbstractPage",
    "AbstractParams",
    "BasePage",
    "BaseRawParams",
    "CursorRawParams",
    "RawParams",
    "is_cursor",
    "is_limit_offset",
]

from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Optional,
    TypeVar,
)

from .utils import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import BaseModel as GenericModel
else:
    from pydantic.generics import GenericModel  # type: ignore[no-redef]


try:
    from pydantic import PydanticUndefinedAnnotation
except ImportError:

    class PydanticUndefinedAnnotation(Exception):  # type: ignore[no-redef]
        pass


from collections.abc import Sequence

from typing_extensions import Self, TypeIs

from .types import Cursor, GreaterEqualZero, ParamsType

T = TypeVar("T")
C = TypeVar("C")

TAbstractPage = TypeVar("TAbstractPage", bound="AbstractPage[Any]")


class BaseRawParams:
    type: ClassVar[ParamsType]
    include_total: bool

    def as_limit_offset(self) -> RawParams:
        if is_limit_offset(self):
            return self

        raise ValueError("Not a 'limit-offset' params")

    def as_cursor(self) -> CursorRawParams:
        if is_cursor(self):
            return self

        raise ValueError("Not a 'cursor' params")


def is_limit_offset(params: BaseRawParams) -> TypeIs[RawParams]:
    return params.type == "limit-offset"


def is_cursor(params: BaseRawParams) -> TypeIs[CursorRawParams]:
    return params.type == "cursor"


@dataclass
class RawParams(BaseRawParams):
    limit: Optional[int] = None
    offset: Optional[int] = None
    include_total: bool = True

    type: ClassVar[ParamsType] = "limit-offset"

    def as_slice(self) -> slice:
        return slice(
            self.offset,
            (self.offset or 0) + self.limit if self.limit is not None else None,
        )


@dataclass
class CursorRawParams(BaseRawParams):
    cursor: Optional[Cursor]
    size: int
    include_total: bool = False

    type: ClassVar[ParamsType] = "cursor"


class AbstractParams(ABC):
    @abstractmethod
    def to_raw_params(self) -> BaseRawParams:
        pass


class AbstractPage(GenericModel, Generic[T], ABC):
    __params_type__: ClassVar[type[AbstractParams]]

    # used by pydantic v2
    __model_aliases__: ClassVar[dict[str, str]] = {}
    __model_exclude__: ClassVar[set[str]] = set()

    if TYPE_CHECKING:  # only for pydantic v1
        __concrete__: ClassVar[bool]
        __parameters__: ClassVar[tuple[Any, ...]]

    if IS_PYDANTIC_V2:

        @classmethod
        def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
            super().__pydantic_init_subclass__(**kwargs)

            for exclude in cls.__model_exclude__:
                cls.model_fields[exclude].exclude = True
            for name, alias in cls.__model_aliases__.items():
                cls.model_fields[name].serialization_alias = alias

            # rebuild model only in case if customizations is present
            if cls.__model_exclude__ or cls.__model_aliases__:
                with suppress(PydanticUndefinedAnnotation):
                    cls.model_rebuild(force=True)

    @classmethod
    @abstractmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        **kwargs: Any,
    ) -> Self:
        pass

    if IS_PYDANTIC_V2:
        model_config = {
            "arbitrary_types_allowed": True,
            "from_attributes": True,
            "populate_by_name": True,
        }
    else:

        class Config:
            orm_mode = True
            arbitrary_types_allowed = True
            allow_population_by_field_name = True


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: Optional[GreaterEqualZero]
