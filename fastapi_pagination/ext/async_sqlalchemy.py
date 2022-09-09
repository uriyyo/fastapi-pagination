from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from ..types import PaginationQueryType
from .sqlalchemy import count_query, paginate_query
from .utils import unwrap_scalars


async def paginate(
    conn: AsyncSession,
    query: Select,
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[Any]:
    params = resolve_params(params)

    total = await conn.scalar(count_query(query))
    items = await conn.execute(paginate_query(query, params, query_type))

    return create_page(unwrap_scalars(items.unique().all()), total, params)


__all__ = [
    "paginate",
]
