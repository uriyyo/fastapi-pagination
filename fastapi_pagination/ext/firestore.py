__all__ = [
    "apaginate",
    "paginate",
]

from typing import Any, Optional, TypeVar, Union, cast

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
from fastapi_pagination.bases import AbstractParams, CursorRawParams, RawParams, is_cursor
from fastapi_pagination.types import AdditionalData, ItemsTransformer, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

TQuery = TypeVar("TQuery", Query, AsyncQuery)


def _apply_limit_offset(query: TQuery, params: RawParams) -> TQuery:
    if params.offset is not None:
        query = query.offset(params.offset)
    if params.limit is not None:
        query = query.limit(params.limit)
    return query


def _apply_cursor(
    query: TQuery,
    params: CursorRawParams,
    snapshot: Optional[DocumentSnapshot],
) -> TQuery:
    if snapshot is not None:
        query = query.start_after(snapshot)
    if params.size is not None:
        query = query.limit(params.size)
    return query


def _convert_raw_items(
    items: list[DocumentSnapshot],
    *,
    raw: bool,
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
    params, raw_params = verify_params(params, "limit-offset", "cursor")
    additional_data = additional_data or {}

    if isinstance(src, CollectionReference):  # noqa: SIM108
        query = Query(src)
    else:
        query = src

    total = None
    if raw_params.include_total:
        total_res = AggregationQuery(query).count("total").get(transaction=transaction)
        total = total_res[0][0].value

    if is_cursor(raw_params):
        snapshot = None
        if cursor := raw_params.cursor:
            snapshot = cast(DocumentSnapshot, query._parent.document(cursor).get(transaction=transaction))

        query = _apply_cursor(query, raw_params, snapshot)
    else:
        query = _apply_limit_offset(query, raw_params.as_limit_offset())

    raw_items = query.get(transaction=transaction)

    if is_cursor(raw_params) and raw_items:
        additional_data["next_"] = raw_items[-1].id

    items = _convert_raw_items(raw_items, raw=raw)
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **additional_data,
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
    params, raw_params = verify_params(params, "limit-offset", "cursor")
    additional_data = additional_data or {}

    if isinstance(src, AsyncCollectionReference):  # noqa: SIM108
        query = AsyncQuery(src)
    else:
        query = src

    total = None
    if raw_params.include_total:
        total_res = await AsyncAggregationQuery(query).count("total").get(transaction=transaction)
        total = total_res[0][0].value

    if is_cursor(raw_params):  # noqa: SIM108
        snapshot = None
        if cursor := raw_params.cursor:
            snapshot = cast(DocumentSnapshot, await query._parent.document(cursor).get(transaction=transaction))

        query = _apply_cursor(query, raw_params, snapshot)
    else:
        query = _apply_limit_offset(query, raw_params.as_limit_offset())

    raw_items = await query.get(transaction=transaction)  # type: ignore[arg-type]

    if is_cursor(raw_params) and raw_items:
        additional_data["next_"] = raw_items[-1].id

    items = _convert_raw_items(raw_items, raw=raw)
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **additional_data,
    )
