from typing import Optional

from orm.models import QuerySet

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(query: QuerySet, params: Optional[AbstractParams] = None) -> AbstractPage:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    total = await query.count()
    items = await query.limit(raw_params.limit).offset(raw_params.offset).all()

    return create_page(items, total, params)


__all__ = ["paginate"]
