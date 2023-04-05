__all__ = ["paginate"]

from typing import Any, Optional

from orm.models import QuerySet

from .utils import generic_query_apply_params
from ..api import create_page, apply_items_transformer
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params


async def paginate(
    query: QuerySet,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    total = await query.count()
    items = await generic_query_apply_params(query, raw_params).all()
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total,
        params,
        **(additional_data or {}),
    )
