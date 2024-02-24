from __future__ import annotations

__all__ = [
    "AbstractPage",
    "AbstractParams",
    "BasePage",
    "BaseRawParams",
    "RawParams",
    "CursorRawParams",
    "is_cursor",
    "is_limit_offset",
]

import inspect
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from .utils import IS_PYDANTIC_V2, get_caller

if IS_PYDANTIC_V2:
    from pydantic import BaseModel as GenericModel
else:
    from pydantic.generics import GenericModel


from typing_extensions import Self, TypeGuard

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


def is_limit_offset(params: BaseRawParams) -> TypeGuard[RawParams]:
    return params.type == "limit-offset"


def is_cursor(params: BaseRawParams) -> TypeGuard[CursorRawParams]:
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


def _new_page_signature(items: Sequence[T], params: AbstractParams, **kwargs: Any) -> Type:  # type: ignore
    return int


_NEW_SIGNATURE = inspect.signature(_new_page_signature)


def _check_for_old_sign(func: Any) -> bool:
    sign = inspect.signature(func)

    try:
        sign.bind([], None)
    except TypeError:
        return True

    has_kwargs = False
    pos_params = []
    for param in sign.parameters.values():
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            pos_params.append(param.name)
        elif param.kind == param.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == param.KEYWORD_ONLY and param.default is inspect.Parameter.empty:
            return True
        elif param.kind in {param.POSITIONAL_ONLY, param.VAR_POSITIONAL}:
            return True

    return not (pos_params == ["items", "params"] and has_kwargs)


class AbstractPage(GenericModel, Generic[T], ABC):
    __params_type__: ClassVar[Type[AbstractParams]]

    if TYPE_CHECKING:
        __concrete__: ClassVar[bool]
        __parameters__: ClassVar[Tuple[Any, ...]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        try:
            is_same = cls.create.__func__ is AbstractPage.create.__func__  # type: ignore[attr-defined]
        except AttributeError:
            is_same = False

        if not is_same and _check_for_old_sign(cls.create):
            warnings.warn(
                "The signature of the `AbstractPage.create` method has changed. "
                f"Please, update it to the new one. {_NEW_SIGNATURE}"
                "\nSupport of old signature will be removed in the next major release (0.13.0).",
                DeprecationWarning,
                stacklevel=3,
            )

        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def create(
        cls: Type[C],
        *args: Any,
        **kwargs: Any,
    ) -> C:
        pass

    @classmethod
    def _old_customization(
        cls,
        custom_params: Optional[Type[AbstractParams]] = None,
        /,
        *,
        cls_name: Optional[str] = None,
        module: Optional[str] = None,
        **kwargs: Any,
    ) -> Type[Self]:
        from .customization import CustomizePage, PageCustomizer, UseModule, UseName, UseParams, UseParamsFields

        args: List[PageCustomizer] = []

        if cls_name:
            args.append(UseName(cls_name))
        if module:
            args.append(UseModule(module))
        if custom_params:
            args.append(UseParams(custom_params))
        if kwargs:
            args.append(UseParamsFields(**kwargs))

        return cast(Type[Self], CustomizePage[(cls, *args)])

    @classmethod
    def with_custom_options(
        cls,
        *,
        cls_name: Optional[str] = None,
        module: Optional[str] = None,
        **kwargs: Any,
    ) -> Type[Self]:
        return cls._old_customization(
            cls_name=cls_name,
            module=module or get_caller(),
            **kwargs,
        )

    @classmethod
    def with_params(
        cls,
        custom_params: Type[AbstractParams],
        *,
        cls_name: Optional[str] = None,
        module: Optional[str] = None,
    ) -> Type[Self]:
        return cls._old_customization(
            cls_name=cls_name,
            module=module or get_caller(),
            custom_params=custom_params,
        )

    if IS_PYDANTIC_V2:
        model_config = {
            "arbitrary_types_allowed": True,
            "from_attributes": True,
        }
    else:

        class Config:
            orm_mode = True
            arbitrary_types_allowed = True


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: Optional[GreaterEqualZero]
