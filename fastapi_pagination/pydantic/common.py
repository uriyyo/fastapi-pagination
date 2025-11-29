__all__ = [
    "create_pydantic_model",
    "get_field_tp",
    "get_model_fields",
    "is_pydantic_field",
    "make_field_optional",
    "make_field_required",
]

from copy import copy
from functools import singledispatch
from typing import Annotated, Any, TypeVar, cast

from fastapi_pagination.typing_utils import remove_optional_from_tp

from .types import AnyBaseModel, AnyField
from .v1 import FieldV1
from .v2 import FieldV2, is_pydantic_v2_model

TAny = TypeVar("TAny")
TModel = TypeVar("TModel", bound=AnyBaseModel)


def create_pydantic_model(model_cls: type[TModel], /, **kwargs: Any) -> TModel:
    if is_pydantic_v2_model(model_cls):
        return model_cls.model_validate(kwargs, from_attributes=True)

    return cast(TModel, model_cls(**kwargs))


@singledispatch
def get_model_fields(model: type[AnyBaseModel], /) -> dict[str, AnyField]:
    if is_pydantic_v2_model(model):
        return cast(dict[str, AnyField], copy(model.model_fields))

    return cast(dict[str, AnyField], copy(model.__fields__))


def is_pydantic_field(field: Any, /) -> bool:
    return isinstance(field, (FieldV1, FieldV2))


@singledispatch
def make_field_optional(field: Any) -> Any:  # pragma: no cover
    raise ValueError(f"Invalid field type {field!r}")


@make_field_optional.register
def _(field: FieldV1, /) -> Any:
    return None


@make_field_optional.register
def _(field: FieldV2, /) -> Any:
    field = copy(field)

    field.annotation = field.annotation | None  # type: ignore[operator, assignment]
    field.default = None
    field.default_factory = None

    return field


@singledispatch
def make_field_required(field: Any, /) -> Any:  # pragma: no cover
    raise ValueError(f"Invalid field type {field!r}")


@make_field_required.register
def _(field: FieldV1, /) -> Any:
    field = copy(field)
    field.required = True
    field.default = ...
    field.default_factory = None

    return field


@make_field_required.register
def _(field: FieldV2, /) -> Any:
    field = copy(field)

    field.annotation = remove_optional_from_tp(field.annotation)
    field.default = ...
    field.default_factory = None

    return field


@singledispatch
def get_field_tp(field: Any, /) -> Any:  # pragma: no cover
    raise ValueError(f"Invalid field type {field!r}")


@get_field_tp.register
def _(field: FieldV1, /) -> Any:
    return field.type_


@get_field_tp.register
def _(field: FieldV2, /) -> Any:
    if field.metadata:
        return Annotated[(field.annotation, *field.metadata)]

    return field.annotation
