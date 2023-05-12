__all__ = [
    "unwrap_scalars",
    "wrap_scalars",
    "generic_query_apply_params",
]

from typing import Any, Optional, Protocol, Sequence, TypeVar, Union, no_type_check

from typing_extensions import Self

from fastapi_pagination.bases import RawParams

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
