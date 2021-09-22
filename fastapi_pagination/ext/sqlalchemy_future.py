from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import paginate_query

if TYPE_CHECKING:
    from sqlalchemy.future import Connection, Engine, Select


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = conn.scalar(select(func.count()).select_from(query.subquery()))
    items = conn.execute(paginate_query(query, params))

    return create_page(items.scalars().unique().all(), total, params)


__all__ = ["paginate"]
