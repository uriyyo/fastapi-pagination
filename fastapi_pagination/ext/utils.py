from typing import Sequence, TypeVar, Union, no_type_check

T = TypeVar("T")


@no_type_check
def unwrap_scalars(items: Sequence[Sequence[T]]) -> Union[Sequence[T], Sequence[Sequence[T]]]:
    return [item[0] if len(item) == 1 else item for item in items]


__all__ = ["unwrap_scalars"]
