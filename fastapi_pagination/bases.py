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
from operator import setitem
from types import new_class
from typing import (
    TYPE_CHECKING,
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
    no_type_check,
)

from pydantic import BaseModel, create_model

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


@no_type_check
def _create_params(cls: Type[AbstractParams], fields: Dict[str, Any]) -> Mapping[str, Any]:
    if not issubclass(cls, BaseModel):
        raise TypeError(f"{cls.__name__} must be subclass of BaseModel")

    model_fields = cls.model_fields if IS_PYDANTIC_V2 else cls.__fields__
    incorrect = sorted(fields.keys() - model_fields.keys() - cls.__class_vars__)
    if incorrect:
        ending = "s" if len(incorrect) > 1 else ""
        raise ValueError(f"Unknown field{ending} {', '.join(incorrect)}")

    annotations = get_type_hints(cls)
    return {name: (annotations[name], val) for name, val in fields.items()}


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
    @no_type_check
    def with_custom_options(
        cls,
        *,
        cls_name: Optional[str] = None,
        module: Optional[str] = None,
        **kwargs: Any,
    ) -> Type[Self]:
        params_cls = cls.__params_type__

        custom_params: Any = create_model(
            params_cls.__name__,
            __base__=params_cls,
            **_create_params(params_cls, kwargs),
        )

        return cls.with_params(
            custom_params,
            cls_name=cls_name,
            module=module,
        )

    @classmethod
    @no_type_check
    def with_params(
        cls,
        custom_params: Type[AbstractParams],
        *,
        cls_name: Optional[str] = None,
        module: Optional[str] = None,
    ) -> Type[Self]:
        bases: Tuple[Type[Any], ...]

        if IS_PYDANTIC_V2:
            params = cls.__pydantic_generic_metadata__["parameters"]
            bases = (cls,) if not params else (cls[params], Generic[params])
        else:
            if cls.__concrete__:
                bases = (cls,)
            else:
                params = tuple(cls.__parameters__)
                bases = (cls[params], Generic[params])

        cls_name = cls_name or f"Customized{cls.__name__}"
        module_name = module or get_caller()

        new_ns = {
            "__params_type__": custom_params,
            "__module__": module_name,
            "__qualname__": cls_name,
            "__name__": cls_name,
        }

        return new_class(cls_name, bases, exec_body=lambda ns: [setitem(ns, k, v) for k, v in new_ns.items()])

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
