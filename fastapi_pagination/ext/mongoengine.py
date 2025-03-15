__all__ = ["paginate"]

from functools import partial
from typing import Any, Optional, TypeVar, Union, cast

from mongoengine import QuerySet
from mongoengine.base.metaclasses import TopLevelDocumentMetaclass

from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, flow_expr, run_sync_flow
from fastapi_pagination.flows import LimitOffsetFlow, generic_flow
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer

T = TypeVar("T", bound=TopLevelDocumentMetaclass)


@flow
def _limit_offset_flow(query: QuerySet, raw_params: RawParams) -> LimitOffsetFlow:
    cursor = yield query.skip(raw_params.offset).limit(raw_params.limit)

    return [item.to_mongo() for item in cursor]


def paginate(
    query: Union[type[T], QuerySet],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if isinstance(query, TopLevelDocumentMetaclass):
        query = cast(type[T], query).objects().all()

    return run_sync_flow(
        generic_flow(
            total_flow=flow_expr(lambda: query.count()),
            limit_offset_flow=partial(_limit_offset_flow, query),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
