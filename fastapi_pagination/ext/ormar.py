from typing import Optional, Type, TypeVar, Union

from ormar import Model, QuerySet

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

TModel = TypeVar("TModel", bound=Model)


async def paginate(
    query: Union[QuerySet[TModel], Type[TModel]],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[TModel]:
    params, raw_params = verify_params(params, "limit-offset")

    if not isinstance(query, QuerySet):
        query = query.objects

    total = await query.count()
    items = await query.offset(raw_params.offset).limit(raw_params.limit).all()

    return create_page(items, total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
