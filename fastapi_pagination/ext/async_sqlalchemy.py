from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import func, select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import paginate_query

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import Select


async def paginate(
    session: AsyncSession,
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:  # pragma: no cover # FIXME: fix coverage report generation
    params = resolve_params(params)

    total = await session.scalar(select([func.count()]).select_from(query))
    items = await session.execute(paginate_query(query, params))

    return create_page([*items.scalars()], total, params)


__all__ = ["paginate"]
