from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Union

__all__ = [
    "Cursor",
    "ParamsType",
    "AdditionalData",
    "GreaterEqualZero",
    "GreaterEqualOne",
    "ItemsTransformer",
    "AsyncItemsTransformer",
    "SyncItemsTransformer",
]

from pydantic import conint
from typing_extensions import TYPE_CHECKING, Literal, TypeAlias

Cursor: TypeAlias = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]
AdditionalData: TypeAlias = Optional[Dict[str, Any]]

AsyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Union[Sequence[Any], Awaitable[Sequence[Any]]]]
SyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Sequence[Any]]
ItemsTransformer: TypeAlias = Union[AsyncItemsTransformer, SyncItemsTransformer]

if TYPE_CHECKING:
    GreaterEqualZero: TypeAlias = int
    GreaterEqualOne: TypeAlias = int
else:
    GreaterEqualZero: TypeAlias = conint(ge=0)
    GreaterEqualOne: TypeAlias = conint(ge=1)
