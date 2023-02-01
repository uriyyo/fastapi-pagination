__all__ = ["paginate"]

from typing import Any, Dict, Mapping, Optional, TypeVar

from pymongo.collection import Collection

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T", bound=Mapping[str, Any])


def paginate(
    collection: Collection[T],
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    **kwargs: Any,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    query_filter = query_filter or {}

    total = collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)

    return create_page([*cursor], total, params, **(additional_data or {}))
