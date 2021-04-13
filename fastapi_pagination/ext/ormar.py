from typing import Optional, Type, Union

from ormar import Model, QuerySet

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(query: Union[QuerySet, Type[Model]], params: Optional[AbstractParams] = None) -> AbstractPage:
    if not isinstance(query, QuerySet):
        query = query.objects

    params = resolve_params(params)

    raw_params = params.to_raw_params()

    total = await query.count()
    items = await query.offset(raw_params.offset).limit(raw_params.limit).all()

    return create_page(items, total, params)


__all__ = ["paginate"]
