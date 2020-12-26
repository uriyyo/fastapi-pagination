from typing import Optional, Type, Union

from tortoise.models import Model
from tortoise.queryset import QuerySet

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(query: Union[QuerySet, Type[Model]], params: Optional[AbstractParams] = None) -> AbstractPage:
    if not isinstance(query, QuerySet):
        query = query.all()

    params = resolve_params(params)

    limit_offset_params = params.to_limit_offset()

    total = await query.count()
    items = await query.offset(limit_offset_params.offset).limit(limit_offset_params.limit).all()

    return create_page(items, total, params)


__all__ = ["paginate"]
