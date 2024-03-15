__all__ = ["paginate"]

from typing import Any, Optional

from asyncpg import Connection

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params
from .sqlalchemy import count_text_query, paginate_text_query


# FIXME: find a way to parse raw sql queries
async def paginate(
    conn: Connection,
    query: str,
    *args: Any,
    transformer: Optional[AsyncItemsTransformer] = None,
    params: Optional[AbstractParams] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if raw_params.include_total:
        total = await conn.fetchval(
            count_text_query(query),
            *args,
        )
    else:
        total = None

    items = await conn.fetch(paginate_text_query(query, params), *args)
    items = [{**r} for r in items]
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
