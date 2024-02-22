__all__ = ["paginate"]

from contextlib import suppress
from copy import copy
from typing import Any, Optional, Type, TypeVar, Union

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, SyncItemsTransformer
from ..utils import verify_params
from .utils import generic_query_apply_params

T = TypeVar("T", bound=Table, covariant=True)


# TODO: there should be a better way to copy query object
def _copy_query(query: Select[T]) -> Select[T]:
    select_cls = type(query)
    q = select_cls(query.table)

    for s in select_cls.__slots__:
        with suppress(AttributeError):
            setattr(q, s, copy(getattr(query, s)))

    return q


async def paginate(
    query: Union[Select[T], Type[T]],
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
    count_query.order_by_delegate._order_by.order_by_items = []  # noqa

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
