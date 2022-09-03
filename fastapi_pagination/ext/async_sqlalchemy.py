from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import count_query, paginate_query
from .utils import unwrap_scalars

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio.engine import AsyncConnectable
    from sqlalchemy.sql import Select


async def paginate(
    conn: Union[AsyncConnectable, AsyncSession],
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = await conn.scalar(count_query(query))
    items = await conn.execute(paginate_query(query, params))

    return create_page(unwrap_scalars(items.unique().all()), total, params)


__all__ = ["paginate"]
