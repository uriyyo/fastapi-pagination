__all__ = [
    "remove_optional_from_tp",
]

from typing import Annotated, Any, Union, get_args, get_origin

try:
    from types import UnionType  # type: ignore[attr-defined]
except ImportError:
    UnionType = Union


def remove_optional_from_tp(tp: Any, /) -> Any:
    if get_origin(tp) in (Union, UnionType):
        args = tuple(arg for arg in get_args(tp) if arg is not type(None))

        if len(args) == 1:
            return remove_optional_from_tp(args[0])

        return Union[args]
    if get_origin(tp) is Annotated:
        return Annotated[
            (
                remove_optional_from_tp(get_args(tp)[0]),
                *tp.__metadata__,
            )
        ]

    return tp
