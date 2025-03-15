__all__ = ["paginate"]

from functools import partial
from typing import Any, Optional, Union, overload

from odmantic import AIOEngine, Model, SyncEngine
from odmantic.engine import AIOSessionType, SyncSessionType
from odmantic.query import QueryExpression
from typing_extensions import TypeAlias

from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow, flow_expr, run_async_flow, run_sync_flow
from fastapi_pagination.flows import LimitOffsetFlow, generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer

_Query: TypeAlias = Union[QueryExpression, dict[Any, Any], bool]


@flow
def _limit_offset_flow(
    model: type[Model],
    queries: tuple[_Query, ...],
    sort: Optional[Any],
    engine: Union[SyncEngine, AIOEngine],
    session: Optional[Union[SyncSessionType, AIOSessionType]],
    raw_params: RawParams,
) -> LimitOffsetFlow:
    result = yield engine.find(
        model,
        *queries,
        sort=sort,
        session=session,  # type: ignore[arg-type]
        limit=raw_params.limit,
        skip=raw_params.offset or 0,
    )

    return [*result]


@overload
async def paginate(
    engine: AIOEngine,
    model: type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[SyncSessionType] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    pass


@overload
def paginate(
    engine: SyncEngine,
    model: type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[AIOSessionType] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    pass


def paginate(
    engine: Union[SyncEngine, AIOEngine],
    model: type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[Union[SyncSessionType, AIOSessionType]] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    is_async = isinstance(engine, AIOEngine)
    run_flow = run_async_flow if is_async else run_sync_flow

    return run_flow(
        generic_flow(
            total_flow=flow_expr(
                lambda: engine.count(
                    model,
                    *queries,
                    session=session,  # type: ignore[arg-type]
                ),
            ),
            limit_offset_flow=partial(
                _limit_offset_flow,
                model,
                queries,
                sort,
                engine,
                session,
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
            async_=is_async,
        )
    )
