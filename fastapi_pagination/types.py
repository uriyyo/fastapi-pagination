__all__ = [
    "AdditionalData",
    "AdditionalDataCallable",
    "AdditionalDataResult",
    "AsyncAdditionalData",
    "AsyncAdditionalDataCallable",
    "AsyncItemsTransformer",
    "Cursor",
    "GreaterEqualOne",
    "GreaterEqualZero",
    "ItemsTransformer",
    "ParamsType",
    "SyncAdditionalData",
    "SyncAdditionalDataCallable",
    "SyncItemsTransformer",
]
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from pydantic import conint

Cursor: TypeAlias = str | bytes
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]

AdditionalDataResult: TypeAlias = dict[str, Any]
SyncAdditionalDataCallable: TypeAlias = Callable[[Sequence[Any]], AdditionalDataResult]
AsyncAdditionalDataCallable: TypeAlias = Callable[[Sequence[Any]], Awaitable[AdditionalDataResult]]
AdditionalDataCallable: TypeAlias = SyncAdditionalDataCallable | AsyncAdditionalDataCallable
AsyncAdditionalData: TypeAlias = AsyncAdditionalDataCallable | AdditionalDataResult
SyncAdditionalData: TypeAlias = SyncAdditionalDataCallable | AdditionalDataResult
AdditionalData: TypeAlias = AsyncAdditionalData | SyncAdditionalData

AsyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Sequence[Any] | Awaitable[Sequence[Any]]]
SyncItemsTransformer: TypeAlias = Callable[[Sequence[Any]], Sequence[Any]]
ItemsTransformer: TypeAlias = AsyncItemsTransformer | SyncItemsTransformer

if TYPE_CHECKING:
    GreaterEqualZero: TypeAlias = int
    GreaterEqualOne: TypeAlias = int
else:
    GreaterEqualZero: TypeAlias = conint(ge=0)
    GreaterEqualOne: TypeAlias = conint(ge=1)
