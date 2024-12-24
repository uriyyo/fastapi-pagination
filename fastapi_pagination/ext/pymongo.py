from __future__ import annotations

__all__ = ["paginate"]

from collections.abc import Mapping, Sequence
from typing import Any, Optional, TypeVar

from pymongo.collection import Collection

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

T = TypeVar("T", bound=Mapping[str, Any])


def paginate(
    collection: Collection[T],
    query_filter: Optional[dict[Any, Any]] = None,
    filter_fields: Optional[dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    sort: Optional[Sequence[Any]] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    **kwargs: Any,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    query_filter = query_filter or {}

    total = collection.count_documents(query_filter) if raw_params.include_total else None
    cursor = collection.find(
        query_filter,
        filter_fields,
        skip=raw_params.offset,
        limit=raw_params.limit,
        sort=sort,
        **kwargs,
    )
    items = [*cursor]
    t_items = apply_items_transformer(
        items,
        transformer,
    )

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
