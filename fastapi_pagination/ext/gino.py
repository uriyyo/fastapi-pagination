from __future__ import annotations

__all__ = ["paginate"]

from typing import Any, Optional, Union, no_type_check

from gino.crud import CRUDModel
from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params
from .sqlalchemy import paginate_query


@no_type_check
async def paginate(
    query: Union[Select, CRUDModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, _ = verify_params(params, "limit-offset")

    if isinstance(query, type) and issubclass(query, CRUDModel):
        query = query.query

    total = await func.count(literal_column("*")).select().select_from(query.order_by(None).alias()).gino.scalar()
    query = paginate_query(query, params)
    items = await query.gino.all()
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
