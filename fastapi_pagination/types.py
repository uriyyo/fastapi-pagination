from typing import Union

from typing_extensions import Literal, TypeAlias

Cursor = Union[str, bytes]
ParamsType: TypeAlias = Literal["cursor", "limit-offset"]

__all__ = [
    "Cursor",
    "ParamsType",
]
