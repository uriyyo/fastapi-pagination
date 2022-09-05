from typing import Any, Dict, Mapping, Optional, TypeVar

from pymongo.collection import Collection

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", bound=Mapping[str, Any])


def paginate(
    collection: Collection[T],
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    **kwargs: Any,
) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    query_filter = query_filter or {}

    total = collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)

    return create_page([*cursor], total, params)


__all__ = [
    "paginate",
]
