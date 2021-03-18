from typing import Any, Optional

from asyncpg import Connection

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


# FIXME: find a way to parse raw sql queries
async def paginate(
    conn: Connection,
    query: str,
    *args: Any,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = await conn.fetchval(
        f"SELECT count(*) FROM ({query}) AS _pagination_query",
        *args,
    )

    raw_params = params.to_raw_params()
    items = await conn.fetch(
        f"{query} LIMIT {raw_params.limit} OFFSET {raw_params.offset}",
        *args,
    )

    return create_page(
        [{**r} for r in items],
        total,
        params,
    )


__all__ = ["paginate"]
