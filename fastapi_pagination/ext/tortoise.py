from typing import Optional, Type, Union

from tortoise import Model, QuerySet

from ..page import BasePage, create_page
from ..params import PaginationParamsType, resolve_params


async def paginate(query: Union[QuerySet, Type[Model]], params: Optional[PaginationParamsType] = None) -> BasePage:
    if not isinstance(query, QuerySet):
        query = query.all()

    params = resolve_params(params)

    limit_offset_params = params.to_limit_offset()

    total = await query.count()
    items = await query.offset(limit_offset_params.offset).limit(limit_offset_params.limit).all()

    return create_page(items, total, params)


__all__ = ["paginate"]
