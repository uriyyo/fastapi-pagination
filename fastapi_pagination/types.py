from typing import Union

from pydantic import conint
from typing_extensions import TYPE_CHECKING, Literal, TypeAlias

Cursor = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]

if TYPE_CHECKING:
    GreaterEqualZero: TypeAlias = int
    GreaterEqualOne: TypeAlias = int
else:
    GreaterEqualZero: TypeAlias = conint(ge=0)
    GreaterEqualOne: TypeAlias = conint(ge=1)

__all__ = [
    "Cursor",
    "ParamsType",
    "GreaterEqualZero",
    "GreaterEqualOne",
]
