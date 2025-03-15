__all__ = [
    "AdditionalData",
    "AsyncItemsTransformer",
    "Cursor",
    "GreaterEqualOne",
    "GreaterEqualZero",
    "ItemsTransformer",
    "ParamsType",
    "SyncItemsTransformer",
]
from collections.abc import Awaitable, Sequence
from typing import TYPE_CHECKING, Any, Callable, Union

from pydantic import conint
from typing_extensions import Literal, TypeAlias

Cursor: TypeAlias = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]
AdditionalData: TypeAlias = dict[str, Any]

AsyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Union[Sequence[Any], Awaitable[Sequence[Any]]]]
SyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Sequence[Any]]
ItemsTransformer: TypeAlias = Union[AsyncItemsTransformer, SyncItemsTransformer]

if TYPE_CHECKING:
    GreaterEqualZero: TypeAlias = int
    GreaterEqualOne: TypeAlias = int
else:
    GreaterEqualZero: TypeAlias = conint(ge=0)
    GreaterEqualOne: TypeAlias = conint(ge=1)
