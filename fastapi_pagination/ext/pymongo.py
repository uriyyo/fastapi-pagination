from __future__ import annotations

__all__ = [
    "apaginate",
    "paginate",
]


from collections.abc import Mapping, Sequence
from typing import Any, Optional, TypeVar

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.collection import Collection

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_async_flow, run_sync_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, ItemsTransformer, SyncItemsTransformer

T = TypeVar("T", bound=Mapping[str, Any])


def paginate(
    collection: Collection[T],
    query_filter: Optional[dict[Any, Any]] = None,
    filter_fields: Optional[dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    sort: Optional[Sequence[Any]] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
    **kwargs: Any,
) -> Any:
    query_filter = query_filter or {}

    return run_sync_flow(
        generic_flow(
            total_flow=flow_expr(lambda: collection.count_documents(query_filter)),
            limit_offset_flow=flow_expr(
                lambda raw_params: collection.find(
                    query_filter,
                    filter_fields,
                    skip=raw_params.offset,
                    limit=raw_params.limit,
                    sort=sort,
                    **kwargs,
                ).to_list()
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )


async def apaginate(
    collection: AsyncCollection[T],
    query_filter: Optional[dict[Any, Any]] = None,
    filter_fields: Optional[dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    sort: Optional[Sequence[Any]] = None,
    *,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
    **kwargs: Any,
) -> Any:
    query_filter = query_filter or {}

    return await run_async_flow(
        generic_flow(
            total_flow=flow_expr(lambda: collection.count_documents(query_filter)),
            limit_offset_flow=flow_expr(
                lambda raw_params: collection.find(
                    query_filter,
                    filter_fields,
                    skip=raw_params.offset,
                    limit=raw_params.limit,
                    sort=sort,
                    **kwargs,
                ).to_list()
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
