from __future__ import annotations

__all__ = [
    "ClsNamespace",
    "CustomizedPage",
    "PageCls",
    "PageCustomizer",
    "UseAdditionalFields",
    "UseExcludedFields",
    "UseFieldsAliases",
    "UseIncludeTotal",
    "UseModelConfig",
    "UseModule",
    "UseName",
    "UseOptionalParams",
    "UseParams",
    "UseParamsFields",
    "UseQuotedCursor",
    "get_page_bases",
    "new_page_cls",
]

from abc import abstractmethod
from copy import copy
from dataclasses import dataclass
from types import new_class
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

from fastapi import Query
from fastapi.params import Param
from pydantic import BaseModel, ConfigDict, create_model
from typing_extensions import TypeAlias, Unpack, get_type_hints

from .bases import AbstractPage, AbstractParams, BaseRawParams
from .utils import IS_PYDANTIC_V2, get_caller

ClsNamespace: TypeAlias = Dict[str, Any]
PageCls: TypeAlias = "Type[AbstractPage[Any]]"

TPage = TypeVar("TPage", bound=PageCls)


def get_page_bases(cls: TPage) -> Tuple[Type[Any], ...]:
    bases: Tuple[Type[Any], ...]

    if IS_PYDANTIC_V2:
        params = cls.__pydantic_generic_metadata__["parameters"]
        bases = (cls,) if not params else (cls[params], Generic[params])  # type: ignore
    else:
        if cls.__concrete__:
            bases = (cls,)
        else:
            params = tuple(cls.__parameters__)
            bases = (cls[params], Generic[params])  # type: ignore

    return bases


def new_page_cls(cls: TPage, new_ns: ClsNamespace) -> TPage:
    new_cls = new_class(
        new_ns.get("__name__", cls.__name__),
        get_page_bases(cls),
        exec_body=lambda ns: ns.update(new_ns),
    )

    return cast(TPage, new_cls)


if TYPE_CHECKING:
    from typing_extensions import Annotated as CustomizedPage
else:

    class CustomizedPage:
        def __class_getitem__(cls, item: Any) -> Any:
            if not isinstance(item, tuple):
                item = (item,)

            page_cls, *customizers = item

            assert isinstance(page_cls, type), f"Expected type, got {page_cls!r}"
            assert issubclass(page_cls, AbstractPage), f"Expected subclass of AbstractPage, got {page_cls!r}"

            if not customizers:
                return page_cls

            original_name = page_cls.__name__
            if original_name.endswith("Customized"):
                original_name = original_name[: -len("Customized")]

            cls_name = f"{original_name}Customized"

            new_ns = {
                "__name__": cls_name,
                "__qualname__": cls_name,
                "__module__": get_caller(),
                "__params_type__": page_cls.__params_type__,
                "__model_aliases__": copy(page_cls.__model_aliases__),
                "__model_exclude__": copy(page_cls.__model_exclude__),
            }

            if IS_PYDANTIC_V2:
                new_ns["model_config"] = {}
            else:

                class Config:
                    pass

                new_ns["Config"] = Config

            for customizer in customizers:
                if isinstance(customizer, PageCustomizer):
                    customizer.customize_page_ns(page_cls, new_ns)
                else:
                    raise TypeError(f"Expected PageCustomizer, got {customizer!r}")

            return new_page_cls(page_cls, new_ns)


@runtime_checkable
class PageCustomizer(Protocol):
    @abstractmethod
    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        pass


@dataclass
class UseName(PageCustomizer):
    name: str

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        ns["__name__"] = self.name
        ns["__qualname__"] = self.name


@dataclass
class UseModule(PageCustomizer):
    module: str

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        ns["__module__"] = self.module


@dataclass
class UseIncludeTotal(PageCustomizer):
    include_total: bool

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
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
class UseQuotedCursor(PageCustomizer):
    quoted_cursor: bool = True

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if TYPE_CHECKING:
            from .cursor import CursorParams
        else:
            CursorParams = ns["__params_type__"]

        class CustomizedParams(CursorParams):
            quoted_cursor: ClassVar[bool] = self.quoted_cursor

        ns["__params_type__"] = CustomizedParams


@dataclass
class UseParams(PageCustomizer):
    params: Type[AbstractParams]

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if page_cls.__params_type__ is not ns["__params_type__"]:
            raise ValueError(
                "Params type was already customized, cannot customize it again. "
                "(IncludeTotal/UseParamsFields must go after UseParams)"
            )

        ns["__params_type__"] = self.params


def _get_model_fields(cls: Type[BaseModel]) -> ClsNamespace:
    if IS_PYDANTIC_V2:
        return {**cls.model_fields}

    return {**cls.__fields__}  # type: ignore[dict-item]


if IS_PYDANTIC_V2:
    from pydantic.fields import FieldInfo as _PydanticField

    def _make_field_optional(field: Any) -> Any:
        assert isinstance(field, _PydanticField)

        field = copy(field)

        field.annotation = Optional[field.annotation]  # type: ignore[assignment]
        field.default = None
        field.default_factory = None

        return field

else:
    from pydantic.fields import ModelField as _PydanticField  # type: ignore

    def _make_field_optional(field: Any) -> Any:
        assert isinstance(field, _PydanticField)

        return None


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
            return getattr(v, "annotation", None) or anns[name]

        return anns[name]

    return {name: (_get_ann(name, val), _wrap_val(name, val)) for name, val in fields.items()}


class UseParamsFields(PageCustomizer):
    def __init__(self, **kwargs: Any) -> None:
        self.fields = kwargs

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        params_cls = ns["__params_type__"]

        ns["__params_type__"] = create_model(
            params_cls.__name__,
            __base__=params_cls,
            **_update_params_fields(params_cls, self.fields),
        )


class UseOptionalParams(PageCustomizer):
    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        params_cls = ns["__params_type__"]

        fields = _get_model_fields(params_cls)
        new_fields = {name: _make_field_optional(field) for name, field in fields.items()}

        customizer = UseParamsFields(**new_fields)
        customizer.customize_page_ns(page_cls, ns)


class UseModelConfig(PageCustomizer):
    def __init__(self, **kwargs: Unpack[ConfigDict]) -> None:
        self.config = kwargs

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if IS_PYDANTIC_V2:
            ns["model_config"].update(self.config)
        else:
            for key, val in self.config.items():
                setattr(ns["Config"], key, val)


def _pydantic_v1_get_inited_fields(cls: Any, /, *fields: str) -> ClsNamespace:
    if not hasattr(cls, "fields"):
        cls.fields = {}

    for f in fields:
        cls.fields.setdefault(f, {})

    return cls.fields  # type: ignore[no-any-return]


class UseExcludedFields(PageCustomizer):
    def __init__(self, *fields: str) -> None:
        self.fields = fields

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if IS_PYDANTIC_V2:
            ns["__model_exclude__"].update(self.fields)
        else:
            fields_config = _pydantic_v1_get_inited_fields(ns["Config"], *self.fields)

            for f in self.fields:
                fields_config[f]["exclude"] = True


class UseFieldsAliases(PageCustomizer):
    def __init__(self, **aliases: str) -> None:
        self.aliases = aliases

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        if IS_PYDANTIC_V2:
            ns["__model_aliases__"].update(self.aliases)
        else:
            fields_config = _pydantic_v1_get_inited_fields(ns["Config"], *self.aliases)

            for name, alias in self.aliases.items():
                assert name in page_cls.__fields__, f"Unknown field {name!r}"  # type: ignore[operator]
                fields_config[name]["alias"] = alias


_RawFieldDef: TypeAlias = Union[Any, Tuple[Any, Any]]


class UseAdditionalFields(PageCustomizer):
    def __init__(self, **fields: _RawFieldDef) -> None:
        self.fields = fields

    def customize_page_ns(self, page_cls: PageCls, ns: ClsNamespace) -> None:
        anns = ns.setdefault("__annotations__", {})

        for name, field in self.fields.items():
            if isinstance(field, tuple):
                anns[name], ns[name] = field
            else:
                anns[name] = field
