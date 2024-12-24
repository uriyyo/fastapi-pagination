__all__ = ["paginate"]

from contextlib import suppress
from copy import copy
from typing import Any, Optional, TypeVar, Union

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

from .utils import generic_query_apply_params

TTable_co = TypeVar("TTable_co", bound=Table, covariant=True)


# TODO: there should be a better way to copy query object
def _copy_query(query: Select[TTable_co]) -> Select[TTable_co]:
    select_cls = type(query)
    q = select_cls(query.table)

    for s in select_cls.__slots__:
        with suppress(AttributeError):
            setattr(q, s, copy(getattr(query, s)))

    return q


async def paginate(
    query: Union[Select[TTable_co], type[TTable_co]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if not isinstance(query, Select):
        query = query.select()

    # query object is mutable, so we need deepcopy of it
    query = _copy_query(query)

    # need another copy for count query
    count_query = _copy_query(query)
    count_query.columns_delegate.selected_columns = []
    # reset order by to avoid errors in count query
    count_query.order_by_delegate._order_by.order_by_items = []

    total = None
    if raw_params.include_total and (row := await count_query.columns(Count()).first()):
        total = row["count"]

    items = await generic_query_apply_params(query, raw_params)
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
