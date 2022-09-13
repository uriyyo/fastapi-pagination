from typing import Optional, Type, TypeVar, Union

from ormar import Model, QuerySet

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params

TModel = TypeVar("TModel", bound=Model)


async def paginate(
    query: Union[QuerySet[TModel], Type[TModel]],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[TModel]:
    params = verify_params(params, "limit-offset")

    if not isinstance(query, QuerySet):
        query = query.objects

    raw_params = params.to_raw_params().as_limit_offset()

    total = await query.count()
    items = await query.offset(raw_params.offset).limit(raw_params.limit).all()

    return create_page(items, total, params)


__all__ = [
    "paginate",
]
