import re
from dataclasses import astuple
from typing import Any, Optional

from asyncpg import Connection

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

_PARAMS_REGEX = re.compile(r"\$\d+")


# FIXME: find a way to parse raw sql queries
async def paginate(
    conn: Connection,
    query: str,
    *args: Any,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = await conn.fetchval(f"SELECT count(*) FROM ({query}) AS _pagination_query", *args)

    idx = max(
        (int(m[1:]) for m in _PARAMS_REGEX.findall(query)),
        default=0,
    )

    raw_params = params.to_raw_params()
    items = await conn.fetch(
        f"{query} LIMIT ${idx + 1} OFFSET ${idx + 2}",
        *args,
        *astuple(raw_params),
    )

    return create_page(
        [{**r} for r in items],
        total,
        params,
    )


__all__ = ["paginate"]
