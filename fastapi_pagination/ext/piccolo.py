__all__ = ["apaginate", "paginate"]

from contextlib import suppress
from copy import copy
from functools import partial
from typing import Any, Optional, TypeVar, Union, cast

from piccolo.query import Select
from piccolo.query.methods.select import Count
from piccolo.table import Table
from typing_extensions import deprecated

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, flow_expr, run_async_flow
from fastapi_pagination.flows import TotalFlow, generic_flow
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer

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


@flow
def _total_flow(query: Select[TTable_co]) -> TotalFlow:
    # need another copy for count query
    count_query = _copy_query(query)
    count_query.columns_delegate.selected_columns = []
    # reset order by to avoid errors in count query
    count_query.order_by_delegate._order_by.order_by_items = []

    row = yield count_query.columns(Count()).first()

    if row:
        return cast(int, row["count"])

    return None


async def apaginate(
    query: Union[Select[TTable_co], type[TTable_co]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if not isinstance(query, Select):
        query = query.select()

    return await run_async_flow(
        generic_flow(
            async_=True,
            total_flow=partial(_total_flow, query),
            limit_offset_flow=flow_expr(lambda raw_params: generic_query_apply_params(_copy_query(query), raw_params)),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


@deprecated("Use `apaginate` instead. This function will be removed in v0.14.0")
async def paginate(
    query: Union[Select[TTable_co], type[TTable_co]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return await apaginate(
        query,
        params=params,
        transformer=transformer,
        additional_data=additional_data,
        config=config,
    )
