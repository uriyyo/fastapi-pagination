__all__ = [
    "unwrap_scalars",
    "wrap_scalars",
]

from typing import Any, Optional, Sequence, TypeVar, Union, no_type_check

T = TypeVar("T")


def len_or_none(obj: Any) -> Optional[int]:
    try:
        return len(obj)
    except TypeError:
        return None


@no_type_check
def unwrap_scalars(items: Sequence[Sequence[T]]) -> Union[Sequence[T], Sequence[Sequence[T]]]:
    return [item[0] if len_or_none(item) == 1 else item for item in items]


@no_type_check
def wrap_scalars(items: Sequence[Any]) -> Sequence[Sequence[Any]]:
    return [item if len_or_none(item) is not None else [item] for item in items]
