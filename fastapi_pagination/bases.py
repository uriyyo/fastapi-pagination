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
from functools import update_wrapper
from operator import setitem
from types import new_class
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    get_type_hints,
)

from pydantic import BaseModel, create_model
from pydantic.generics import GenericModel
from typing_extensions import TypeGuard

from .types import Cursor, GreaterEqualZero, ParamsType

T = TypeVar("T")
C = TypeVar("C")

TAbstractPage = TypeVar("TAbstractPage", bound="AbstractPage[Any]")


class BaseRawParams:
    type: ClassVar[ParamsType]

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
    limit: int
    offset: int

    type: ClassVar[ParamsType] = "limit-offset"


@dataclass
class CursorRawParams(BaseRawParams):
    cursor: Optional[Cursor]
    size: int

    type: ClassVar[ParamsType] = "cursor"


class AbstractParams(ABC):
    @abstractmethod
    def to_raw_params(self) -> BaseRawParams:
        pass


def _create_params(cls: Type[AbstractParams], fields: Dict[str, Any]) -> Mapping[str, Any]:
    if not issubclass(cls, BaseModel):
        raise ValueError(f"{cls.__name__} must be subclass of BaseModel")

    incorrect = sorted(fields.keys() - cls.__fields__.keys() - cls.__class_vars__)
    if incorrect:
        ending = "s" if len(incorrect) > 1 else ""
        raise ValueError(f"Unknown field{ending} {', '.join(incorrect)}")

    anns = get_type_hints(cls)
    return {name: (anns[name], val) for name, val in fields.items()}


def _new_page_signature(items: Sequence[T], params: AbstractParams, **kwargs: Any) -> Type:  # type: ignore  # noqa
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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        try:
            is_same = cls.create.__func__ is AbstractPage.create.__func__  # type: ignore[attr-defined]
        except AttributeError:
            is_same = False

        if not is_same and _check_for_old_sign(cls.create):
            warnings.warn(
                "The signature of the `AbstractPage.create` method has changed. "
                f"Please, update it to the new one. {_NEW_SIGNATURE}",
                DeprecationWarning,
                stacklevel=3,
            )

    @classmethod
    @abstractmethod
    def create(
        cls: Type[C],
        *args: Any,
        **kwargs: Any,
    ) -> C:
        pass

    @classmethod
    def with_custom_options(cls: Type[TAbstractPage], **kwargs: Any) -> Type[TAbstractPage]:
        params_cls = cls.__params_type__

        custom_params: Any = create_model(  # noqa
            params_cls.__name__,
            __base__=params_cls,
            **_create_params(params_cls, kwargs),
        )

        bases: Tuple[Type[Any], ...]
        if cls.__concrete__:
            bases = (cls,)
        else:
            params = tuple(cls.__parameters__)
            bases = (cls[params], Generic[params])  # type: ignore[assignment, index]

        new_cls = new_class("CustomPage", bases, exec_body=lambda ns: setitem(ns, "__params_type__", custom_params))
        new_cls = update_wrapper(new_cls, cls, updated=())

        return new_cls  # noqa

    class Config:
        arbitrary_types_allowed = True


class BasePage(AbstractPage[T], Generic[T], ABC):
    items: Sequence[T]
    total: GreaterEqualZero
