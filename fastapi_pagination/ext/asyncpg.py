__all__ = ["paginate"]

from typing import Any, Optional

from asyncpg import Connection

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


# FIXME: find a way to parse raw sql queries
async def paginate(
    conn: Connection,
    query: str,
    *args: Any,
    params: Optional[AbstractParams] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    total = await conn.fetchval(
        f"SELECT count(*) FROM ({query}) AS _pagination_query",
        *args,
    )

    items = await conn.fetch(
        f"{query} LIMIT {raw_params.limit} OFFSET {raw_params.offset}",
        *args,
    )

    return create_page(
        [{**r} for r in items],
        total,
        params,
        **(additional_data or {}),
    )
