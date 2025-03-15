from typing import Any, Optional, TypeVar, Union, cast

__all__ = ["paginate"]

from django.db.models import Model, QuerySet
from django.db.models.base import ModelBase

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_sync_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer

T = TypeVar("T", bound=Model)


def paginate(
    query: Union[type[T], QuerySet[T]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if isinstance(query, ModelBase):
        query = cast(type[T], query).objects.all()

    return run_sync_flow(
        generic_flow(
            total_flow=flow_expr(lambda: query.count()),
            limit_offset_flow=flow_expr(lambda raw_params: [*query[raw_params.as_slice()]]),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
