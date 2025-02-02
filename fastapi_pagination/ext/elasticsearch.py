__all__ = [
    "paginate",
]

from typing import Any, Optional

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams, is_limit_offset
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params


def paginate(
    conn: Elasticsearch,
    query: Search,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset", "cursor")

    total = None
    if raw_params.include_total:
        total = query.using(conn).count()

    kwargs = {}
    items: Any

    if is_limit_offset(raw_params):
        items = query.using(conn)[raw_params.as_slice()].execute()
    else:
        raw_params = raw_params.as_cursor()

        response: Any
        if not raw_params.cursor:
            response = query.params(scroll="1m").extra(size=raw_params.size).execute()
            items = response.hits
            next_ = response._scroll_id
        else:
            response = conn.scroll(scroll_id=raw_params.cursor, scroll="1m")  # type: ignore[arg-type]
            next_ = response.get("_scroll_id")
            items = [item.get("_source") for item in response["hits"]["hits"]]

        kwargs["next_"] = next_

    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **kwargs,
        **(additional_data or {}),
    )
