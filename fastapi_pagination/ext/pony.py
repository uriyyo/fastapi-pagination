__all__ = ["paginate"]

from typing import Any, Optional

from pony.orm.core import Query

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_sync_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return run_sync_flow(
        generic_flow(
            total_flow=flow_expr(lambda: query.count()),
            limit_offset_flow=flow_expr(lambda raw_params: query.fetch(raw_params.limit, raw_params.offset).to_list()),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
