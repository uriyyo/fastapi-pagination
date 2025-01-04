__all__ = [
    "apaginate",
    "paginate",
]

from typing import Any, Optional, TypeVar, Union

from google.cloud.firestore_v1 import (
    AsyncCollectionReference,
    AsyncQuery,
    AsyncTransaction,
    CollectionReference,
    DocumentSnapshot,
    Query,
    Transaction,
)
from google.cloud.firestore_v1.aggregation import AggregationQuery
from google.cloud.firestore_v1.async_aggregation import AsyncAggregationQuery

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.types import AdditionalData, ItemsTransformer, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

TQuery = TypeVar("TQuery", Query, AsyncQuery)


def _apply_limit_offset(query: TQuery, params: RawParams) -> TQuery:
    if params.offset is not None:
        query = query.offset(params.offset)
    if params.limit is not None:
        query = query.limit(params.limit)
    return query


def _convert_raw_items(
    items: list[DocumentSnapshot], *, raw: bool
) -> Union[list[DocumentSnapshot], list[dict[str, Any]]]:
    if raw:
        return items

    return [(doc.to_dict() or {}) | {"id": str(doc.id)} for doc in items]


def paginate(
    src: Union[CollectionReference, Query],
    /,
    params: Optional[AbstractParams] = None,
    *,
    raw: bool = False,
    transaction: Optional[Transaction] = None,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(src, CollectionReference):
        src = Query(src)

    total = None
    if raw_params.include_total:
        total_res = AggregationQuery(src).count("total").get(transaction=transaction)
        total = total_res[0][0].value

    query = _apply_limit_offset(src, raw_params)
    raw_items = query.get(transaction=transaction)
    items = _convert_raw_items(raw_items, raw=raw)
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )


async def apaginate(
    src: Union[AsyncCollectionReference, AsyncQuery],
    /,
    params: Optional[AbstractParams] = None,
    *,
    raw: bool = False,
    transaction: Optional[AsyncTransaction] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(src, AsyncCollectionReference):
        src = AsyncQuery(src)

    total = None
    if raw_params.include_total:
        total_res = await AsyncAggregationQuery(src).count("total").get(transaction=transaction)
        total = total_res[0][0].value

    query = _apply_limit_offset(src, raw_params)
    raw_items = await query.get(transaction=transaction)  # type: ignore[arg-type]
    items = _convert_raw_items(raw_items, raw=raw)
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
