from typing import List, Optional, Type, Union

from tortoise.models import Model
from tortoise.query_utils import Prefetch
from tortoise.queryset import QuerySet

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


def _generate_query(
    query: QuerySet,
    prefetch_related: Union[bool, List[Union[str, Prefetch]]],
) -> QuerySet:
    if prefetch_related:
        if prefetch_related is True:
            prefetch_related = [*query.model._meta.fetch_fields]

        return query.prefetch_related(*prefetch_related)

    return query


async def paginate(
    query: Union[QuerySet, Type[Model]],
    params: Optional[AbstractParams] = None,
    prefetch_related: Union[bool, List[Union[str, Prefetch]]] = False,
) -> AbstractPage:
    if not isinstance(query, QuerySet):
        query = query.all()

    params = resolve_params(params)

    raw_params = params.to_raw_params()

    total = await query.count()
    items = await _generate_query(query, prefetch_related).offset(raw_params.offset).limit(raw_params.limit).all()

    return create_page(items, total, params)


__all__ = ["paginate"]
