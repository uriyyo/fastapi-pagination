from typing import Any, Dict, Optional, Union, Callable, Sequence

__all__ = [
    "Cursor",
    "ParamsType",
    "AdditionalData",
    "GreaterEqualZero",
    "GreaterEqualOne",
    "ItemsTransformer",
]

from pydantic import conint
from typing_extensions import TYPE_CHECKING, Literal, TypeAlias

Cursor: TypeAlias = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]
AdditionalData: TypeAlias = Optional[Dict[str, Any]]
ItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Sequence[Any]]

if TYPE_CHECKING:
    GreaterEqualZero: TypeAlias = int
    GreaterEqualOne: TypeAlias = int
else:
    GreaterEqualZero: TypeAlias = conint(ge=0)
    GreaterEqualOne: TypeAlias = conint(ge=1)
