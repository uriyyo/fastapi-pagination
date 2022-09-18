from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params
from .sqlalchemy_future import async_exec_pagination


async def paginate(
    conn: AsyncSession,
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params, _ = verify_params(params, "limit-offset", "cursor")
    return await async_exec_pagination(query, params, conn.execute)


__all__ = [
    "paginate",
]
