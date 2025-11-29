__all__ = [
    "AnyBaseModel",
    "AnyField",
    "LatestGenericModel",
]

from typing import TypeAlias

from .consts import IS_PYDANTIC_V2
from .v1 import BaseModelV1, FieldV1
from .v2 import BaseModelV2, FieldV2

AnyBaseModel: TypeAlias = BaseModelV1 | BaseModelV2
AnyField: TypeAlias = FieldV1 | FieldV2

if IS_PYDANTIC_V2:
    from .v2 import GenericModelV2 as LatestGenericModel
else:
    from .v1 import GenericModelV1 as LatestGenericModel  # type: ignore[assignment]
