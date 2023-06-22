__all__ = ["paginate"]

from typing import Any, Optional

from asyncpg import Connection

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params


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

    total = await conn.fetchval(
        f"SELECT count(*) FROM ({query}) AS _pagination_query",  # noqa: S608
        *args,
    )

    limit_offset_str = ""
    if raw_params.limit is not None:
        limit_offset_str += f" LIMIT {raw_params.limit}"
    if raw_params.offset is not None:
        limit_offset_str += f" OFFSET {raw_params.offset}"

    items = await conn.fetch(f"{query} {limit_offset_str}", *args)
    items = [{**r} for r in items]
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
