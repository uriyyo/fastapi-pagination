__all__ = [
    "AbstractPagePydanticConfigV1",
    "BaseModelV1",
    "FieldV1",
    "GenericModelV1",
    "is_pydantic_v1_model",
]

from typing import Any

from fastapi.dependencies.utils import lenient_issubclass
from typing_extensions import TypeIs

try:
    from pydantic.v1 import BaseModel as BaseModelV1
    from pydantic.v1.fields import ModelField as FieldV1
    from pydantic.v1.generics import GenericModel as GenericModelV1
except ImportError:  # pragma: no cover
    from pydantic import BaseModel as BaseModelV1  # type: ignore[assignment]
    from pydantic.fields import ModelField as FieldV1  # type: ignore[attr-defined,no-redef]
    from pydantic.generics import GenericModel as GenericModelV1  # type: ignore[no-redef]


def is_pydantic_v1_model(model_cls: type[Any]) -> TypeIs[type[BaseModelV1]]:
    return lenient_issubclass(model_cls, BaseModelV1)


class AbstractPagePydanticConfigV1:
    orm_mode = True
    arbitrary_types_allowed = True
    allow_population_by_field_name = True
