__all__ = [
    "BaseModelV2",
    "FieldV2",
    "GenericModelV2",
    "is_pydantic_v2_model",
]

from typing import Any

from fastapi.dependencies.utils import lenient_issubclass
from typing_extensions import TypeIs

from .consts import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import BaseModel as BaseModelV2
    from pydantic import BaseModel as GenericModelV2
    from pydantic.fields import FieldInfo as FieldV2
else:

    class _DummyCls:
        pass

    BaseModelV2 = _DummyCls  # type: ignore[misc,assignment]
    GenericBaseModelV2 = _DummyCls
    FieldV2 = _DummyCls  # type: ignore[misc,assignment]


def is_pydantic_v2_model(model_cls: type[Any]) -> TypeIs[type[BaseModelV2]]:
    if not IS_PYDANTIC_V2:
        return False

    from .v1 import BaseModelV1

    return not lenient_issubclass(model_cls, BaseModelV1)
