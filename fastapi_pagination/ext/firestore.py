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
from fastapi_pagination.bases import AbstractParams, CursorRawParams, is_cursor
from fastapi_pagination.ext.utils import generic_query_apply_params
from fastapi_pagination.flow import Flow, flow, run_async_flow, run_sync_flow
from fastapi_pagination.types import AdditionalData, ItemsTransformer, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

TQuery = TypeVar("TQuery", Query, AsyncQuery)


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
    if raw:  # pragma: no cover
        return items

    return [(doc.to_dict() or {}) | {"id": str(doc.id)} for doc in items]


@flow
def _get_total(
    async_: bool,
    query: Union[Query, AsyncQuery],
    transaction: Optional[Union[Transaction, AsyncTransaction]],
) -> Flow[Any, int]:
    aggr_query = AsyncAggregationQuery if async_ else AggregationQuery
    total_res = yield aggr_query(query).count("total").get(transaction=transaction)

    return cast(int, total_res[0][0].value)


@flow
def _fetch_cursor(
    query: TQuery,
    params: CursorRawParams,
    transaction: Optional[Union[Transaction, AsyncTransaction]],
) -> Flow[Any, Optional[DocumentSnapshot]]:
    if cursor := params.cursor:
        raw_doc = yield query._parent.document(cursor).get(transaction=transaction)
        return cast(DocumentSnapshot, raw_doc)

    return None


@flow
def _firebase_flow(
    src: Union[
        CollectionReference,
        Query,
        AsyncCollectionReference,
        AsyncQuery,
    ],
    /,
    params: Optional[AbstractParams],
    *,
    raw: bool,
    transaction: Optional[Transaction],
    transformer: Optional[ItemsTransformer],
    additional_data: Optional[AdditionalData],
    async_: bool,
) -> Flow[Any, Any]:
    params, raw_params = verify_params(params, "limit-offset", "cursor")
    additional_data = additional_data or {}

    query: Union[Query, AsyncQuery]
    if isinstance(src, AsyncCollectionReference):
        query = AsyncQuery(src)
    elif isinstance(src, CollectionReference):
        query = Query(src)
    else:
        query = src

    total = None
    if raw_params.include_total:
        total = yield from _get_total(async_, query, transaction)

    if is_cursor(raw_params):
        snapshot = yield from _fetch_cursor(query, raw_params, transaction)  # type: ignore[type-var]
        query = _apply_cursor(query, raw_params, snapshot)  # type: ignore[type-var]
    else:
        query = generic_query_apply_params(query, raw_params.as_limit_offset())

    raw_items = yield query.get(transaction=transaction)  # type: ignore[arg-type]

    if is_cursor(raw_params) and raw_items:
        additional_data["next_"] = raw_items[-1].id

    items = _convert_raw_items(raw_items, raw=raw)
    t_items = yield apply_items_transformer(items, transformer, async_=async_)  # type: ignore[call-overload]

    return create_page(
        t_items,
        total=total,
        params=params,
        **additional_data,
    )


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
    return run_sync_flow(
        _firebase_flow(
            src,
            params=params,
            raw=raw,
            transaction=transaction,
            transformer=transformer,
            additional_data=additional_data,
            async_=False,
        ),
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
    return await run_async_flow(
        _firebase_flow(
            src,
            params=params,
            raw=raw,
            transaction=transaction,  # type: ignore[arg-type]
            transformer=transformer,
            additional_data=additional_data,
            async_=True,
        ),
    )
