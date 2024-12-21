__all__ = [
    "generic_query_apply_params",
    "unwrap_scalars",
    "wrap_scalars",
]

from typing import Any, Optional, Protocol, Sequence, TypeVar, Union, cast

from typing_extensions import Self

from fastapi_pagination.bases import RawParams

T = TypeVar("T")


def len_or_none(obj: Any) -> Optional[int]:
    try:
        return len(obj)
    except TypeError:
        return None


def unwrap_scalars(
    items: Sequence[Sequence[T]],
    *,
    force_unwrap: bool = False,
) -> Union[Sequence[T], Sequence[Sequence[T]]]:
    return cast(
        Union[Sequence[T], Sequence[Sequence[T]]],
        [item[0] if force_unwrap or len_or_none(item) == 1 else item for item in items],
    )


def wrap_scalars(items: Sequence[Any]) -> Sequence[Sequence[Any]]:
    return [item if len_or_none(item) is not None else [item] for item in items]


class AbstractQuery(Protocol):
    def limit(self, *_: Any, **__: Any) -> Self:  # pragma: no cover
        pass

    def offset(self, *_: Any, **__: Any) -> Self:  # pragma: no cover
        pass


TAbstractQuery = TypeVar("TAbstractQuery", bound=AbstractQuery)


def generic_query_apply_params(q: TAbstractQuery, params: RawParams) -> TAbstractQuery:
    if params.limit is not None:
        q = q.limit(params.limit)
    if params.offset is not None:
        q = q.offset(params.offset)

    return q
