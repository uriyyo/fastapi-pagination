__all__ = ["paginate"]

from typing import List, Optional, Type, TypeVar, Union, Any

from tortoise.models import Model
from tortoise.query_utils import Prefetch
from tortoise.queryset import QuerySet

from .utils import generic_query_apply_params
from ..api import create_page, apply_items_transformer
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params

TModel = TypeVar("TModel", bound=Model)


def _generate_query(
    query: QuerySet[TModel],
    prefetch_related: Union[bool, List[Union[str, Prefetch]]],
) -> QuerySet[TModel]:
    if prefetch_related:
        if prefetch_related is True:
            prefetch_related = [*query.model._meta.fetch_fields]

        return query.prefetch_related(*prefetch_related)

    return query


async def paginate(
    query: Union[QuerySet[TModel], Type[TModel]],
    params: Optional[AbstractParams] = None,
    prefetch_related: Union[bool, List[Union[str, Prefetch]]] = False,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if not isinstance(query, QuerySet):
        query = query.all()

    total = await query.count()
    items = await generic_query_apply_params(_generate_query(query, prefetch_related), raw_params).all()
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total,
        params,
        **(additional_data or {}),
    )
