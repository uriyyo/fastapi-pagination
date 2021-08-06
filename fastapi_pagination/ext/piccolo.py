from copy import deepcopy
from typing import Optional, Type, Union

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(query: Union[Select, Type[Table]], params: Optional[AbstractParams] = None) -> AbstractPage:
    if not isinstance(query, Select):
        query = query.select()

    # query object is mutable, so we need deepcopy of it
    query = deepcopy(query)

    params = resolve_params(params)
    raw_params = params.to_raw_params()

    # need another copy for count query
    count_query = deepcopy(query)
    count_query.columns_delegate.selected_columns.clear()

    total = (await count_query.columns(Count()).first())["count"]
    items = await query.offset(raw_params.offset).limit(raw_params.limit)

    return create_page(items, total, params)


__all__ = ["paginate"]
