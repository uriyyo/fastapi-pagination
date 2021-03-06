from __future__ import annotations

from typing import Optional, Union

from gino.crud import CRUDModel
from sqlalchemy import func
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import paginate_query


async def paginate(query: Union[Select, CRUDModel], params: Optional[AbstractParams] = None) -> AbstractPage:
    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query  # type: ignore

    params = resolve_params(params)

    total = await func.count().select().select_from(query.alias()).gino.scalar()
    items = await paginate_query(query, params).gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
