from __future__ import annotations

from typing import Any, Optional, Union, no_type_check

from gino.crud import CRUDModel
from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import paginate_query


@no_type_check
async def paginate(
    query: Union[Select, CRUDModel],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query

    params = resolve_params(params)

    total = await func.count(literal_column("*")).select().select_from(query.order_by(None).alias()).gino.scalar()
    items = await paginate_query(query, params).gino.all()

    return create_page(items, total, params)


__all__ = [
    "paginate",
]
