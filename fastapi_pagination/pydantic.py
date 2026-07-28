__all__ = [
    "create_pydantic_model",
    "get_field_tp",
    "get_model_fields",
    "is_pydantic_field",
    "make_field_optional",
    "make_field_required",
]

from copy import copy
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from fastapi_pagination.typing_utils import create_annotated_tp, remove_optional_from_tp

TModel = TypeVar("TModel", bound=BaseModel)


def create_pydantic_model(model_cls: type[TModel], /, **kwargs: Any) -> TModel:
    return model_cls.model_validate(kwargs, from_attributes=True)


def get_model_fields(model: type[BaseModel], /) -> dict[str, FieldInfo]:
    return copy(model.model_fields)


def is_pydantic_field(field: Any, /) -> bool:
    return isinstance(field, FieldInfo)


def make_field_optional(field: FieldInfo, /) -> FieldInfo:
    field = copy(field)

    field.annotation = field.annotation | None  # type: ignore[ty:unsupported-operator]
    field.default = None
    field.default_factory = None

    return field


def make_field_required(field: FieldInfo, /) -> FieldInfo:
    field = copy(field)

    field.annotation = remove_optional_from_tp(field.annotation)
    field.default = ...
    field.default_factory = None

    return field


def get_field_tp(field: FieldInfo, /) -> Any:
    if field.metadata:
        return create_annotated_tp(field.annotation, *field.metadata)

    return field.annotation
