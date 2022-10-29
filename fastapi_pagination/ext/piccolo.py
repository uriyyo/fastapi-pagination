from copy import deepcopy
from typing import Optional, Type, Union

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


async def paginate(
    query: Union[Select, Type[Table]],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage:
    params, raw_params = verify_params(params, "limit-offset")

    if not isinstance(query, Select):
        query = query.select()

    # query object is mutable, so we need deepcopy of it
    query = deepcopy(query)

    # need another copy for count query
    count_query = deepcopy(query)
    count_query.columns_delegate.selected_columns = []

    total = (await count_query.columns(Count()).first())["count"]
    items = await query.offset(raw_params.offset).limit(raw_params.limit)

    return create_page(items, total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
