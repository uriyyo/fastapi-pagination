from typing import Any, Dict, List, Optional

from pymongo.collection import Collection

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


def paginate(
    collection: Collection,
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    **kwargs: Any,
) -> AbstractPage:
    params = resolve_params(params)
    query_filter = query_filter or {}

    raw_params = params.to_raw_params()
    total = collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)
    items = list(cursor)

    return create_page(items, total, params)


__all__ = ["paginate"]
