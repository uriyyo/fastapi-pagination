__all__ = [
    "paginate",
]


from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams, CursorRawParams, is_limit_offset
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params


def paginate(
    conn: Elasticsearch,
    query: Search,
    params: AbstractParams | None = None,
    *,
    transformer: SyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
):
    params, raw_params = verify_params(params, "limit-offset", "cursor")
    if is_limit_offset(raw_params):
        total = query.using(conn).count()
        response = query.using(conn)[raw_params.offset : raw_params.offset + raw_params.limit].execute()
        items = response
        t_items = apply_items_transformer(items, transformer)
        return create_page(
            t_items,
            total=total,
            params=params,
            **(additional_data or {}),
        )

    total = None
    if raw_params.include_total:
        total = query.using(conn).count()
    raw_params: CursorRawParams
    if not raw_params.cursor:
        response = query.params(scroll="1m").extra(size=raw_params.size).execute()
        items = response.hits
        next_ = response._scroll_id
    else:
        response = conn.scroll(scroll_id=raw_params.cursor, scroll="1m")
        next_ = response.get("_scroll_id")
        items = [item.get("_source") for item in response["hits"]["hits"]]
    t_items = apply_items_transformer(items, transformer)
    return create_page(
        t_items,
        total=total,
        params=params,
        next_=next_,
        **(additional_data or {}),
    )
