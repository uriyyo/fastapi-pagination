from __future__ import annotations

from typing import Any, Optional, Union

from sqlalchemy.future import Connection, Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import count_query, paginate_query
from .utils import unwrap_scalars


def paginate(
    conn: Union[Connection, Engine, Session],
    query: Select,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params = resolve_params(params)

    total = conn.scalar(count_query(query))
    items = conn.execute(paginate_query(query, params))

    return create_page(unwrap_scalars(items.unique().all()), total, params)


__all__ = [
    "paginate",
]
