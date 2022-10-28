from __future__ import annotations

from typing import Any, Optional, Union, no_type_check

from gino.crud import CRUDModel
from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params
from .sqlalchemy import paginate_query


@no_type_check
async def paginate(
    query: Union[Select, CRUDModel],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:
    params, _ = verify_params(params, "limit-offset")

    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query

    total = await func.count(literal_column("*")).select().select_from(query.order_by(None).alias()).gino.scalar()
    query = paginate_query(query, params)
    items = await query.gino.all()

    return create_page(items, total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
