from __future__ import annotations

__all__ = [
    "new_page_cls",
    "get_page_bases",
    "CustomizePage",
    "PageCustomizer",
    "UseName",
    "UseModule",
    "IncludeTotal",
    "UseParams",
    "UseParamsFields",
]

from copy import copy
from dataclasses import dataclass
from types import new_class
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, Tuple, Type, TypeVar, no_type_check

from fastapi import Query
from fastapi.params import Param
from pydantic import BaseModel, create_model
from typing_extensions import TypeAlias, get_type_hints

from .bases import AbstractPage, AbstractParams, BaseRawParams
from .utils import IS_PYDANTIC_V2, get_caller

TPage = TypeVar("TPage", bound="AbstractPage[Any]")

ClsNamespace: TypeAlias = Dict[str, Any]


@no_type_check
def get_page_bases(cls: Type[TPage]) -> tuple[Type[Any], ...]:
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

    return bases


def new_page_cls(cls: Type[TPage], new_ns: ClsNamespace) -> Type[TPage]:
    return new_class(
        new_ns.get("__name__", cls.__name__),
        get_page_bases(cls),
        exec_body=lambda ns: ns.update(new_ns),
    )


if TYPE_CHECKING:
    from typing_extensions import Annotated as CustomizePage
else:

    class CustomizePage:
        def __class_getitem__(cls, item: Any) -> Any:
            if not isinstance(item, tuple):
                item = (item,)

            page_cls, *customizers = item

            assert isinstance(page_cls, type), f"Expected type, got {page_cls!r}"
            assert issubclass(page_cls, AbstractPage), f"Expected subclass of AbstractPage, got {page_cls!r}"

            if not customizers:
                return page_cls

            cls_name = f"{page_cls.__name__}Customized"

            new_ns = {
                "__name__": cls_name,
                "__qualname__": cls_name,
                "__module__": get_caller(),
                "__params_type__": page_cls.__params_type__,
            }

            for customizer in customizers:
                if isinstance(customizer, PageCustomizer):
                    customizer.customize_page_ns(page_cls, new_ns)
                else:
                    raise TypeError(f"Expected PageCustomizer, got {customizer!r}")

            return new_page_cls(page_cls, new_ns)


class PageCustomizer:
    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        return None


@dataclass
class UseName(PageCustomizer):
    name: str

    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        ns["__name__"] = self.name
        ns["__qualname__"] = self.name


@dataclass
class UseModule(PageCustomizer):
    module: str

    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        ns["__module__"] = self.module


@dataclass
class IncludeTotal(PageCustomizer):
    include_total: bool

    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        include_total = self.include_total

        if TYPE_CHECKING:
            from .bases import AbstractParams as ParamsCls
        else:
            ParamsCls = ns["__params_type__"]

        class CustomizedParams(ParamsCls):
            def to_raw_params(self) -> BaseRawParams:
                raw_params = super().to_raw_params()  # type: ignore[safe-super]
                raw_params.include_total = include_total

                return raw_params

        ns["__params_type__"] = CustomizedParams


@dataclass
class UseParams(PageCustomizer):
    params: Type[AbstractParams]

    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        if page_cls.__params_type__ is not ns["__params_type__"]:
            raise ValueError(
                "Params type was already customized, cannot customize it again. "
                "(IncludeTotal must go after UseParams)"
            )

        ns["__params_type__"] = self.params


def _get_model_fields(cls: Type[BaseModel]) -> ClsNamespace:
    if IS_PYDANTIC_V2:
        return cls.model_fields  # type: ignore

    return cls.__fields__


if IS_PYDANTIC_V2:
    from pydantic.fields import FieldInfo as _PydanticField

    @no_type_check
    def _make_field_optional(field: Any) -> Any:
        assert isinstance(field, _PydanticField)

        field = copy(field)

        field.annotation = Optional[field.annotation]
        field.default = None
        field.default_factory = None

        return field

else:
    from pydantic.fields import ModelField as _PydanticField  # type: ignore[assignment]

    def _make_field_optional(field: Any) -> Any:
        assert isinstance(field, _PydanticField)

        return copy(field)


@no_type_check
def _update_params_fields(cls: Type[AbstractParams], fields: ClsNamespace) -> ClsNamespace:
    if not issubclass(cls, BaseModel):
        raise TypeError(f"{cls.__name__} must be subclass of BaseModel")

    model_fields = _get_model_fields(cls)
    incorrect = sorted(fields.keys() - model_fields.keys() - cls.__class_vars__)

    if incorrect:
        ending = "s" if len(incorrect) > 1 else ""
        raise ValueError(f"Unknown field{ending} {', '.join(incorrect)}")

    anns = get_type_hints(cls)

    def _wrap_val(name: str, v: Any) -> Any:
        if name in cls.__class_vars__:
            return v
        if not isinstance(v, (Param, _PydanticField)):
            return Query(v)

        return v

    def _get_ann(name: str, v: Any) -> Any:
        if IS_PYDANTIC_V2:
            return getattr(v, "annotation", anns[name])

        return anns[name]

    return {name: (_get_ann(name, val), _wrap_val(name, val)) for name, val in fields.items()}


class UseParamsFields(PageCustomizer):
    def __init__(self, **kwargs: Any) -> None:
        self.fields = kwargs

    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        params_cls = ns["__params_type__"]

        ns["__params_type__"] = create_model(
            params_cls.__name__,
            __base__=params_cls,
            **_update_params_fields(params_cls, self.fields),
        )


class UseOptionalParams(PageCustomizer):
    def customize_page_ns(self, page_cls: Type[TPage], ns: ClsNamespace) -> None:
        params_cls = ns["__params_type__"]

        fields = _get_model_fields(params_cls)
        new_fields = {name: _make_field_optional(field) for name, field in fields.items()}

        customizer = UseParamsFields(**new_fields)
        customizer.customize_page_ns(page_cls, ns)
