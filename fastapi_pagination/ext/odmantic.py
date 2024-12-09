__all__ = ["paginate"]

from typing import Any, Dict, Optional, Type, Union, overload

from odmantic import AIOEngine, Model, SyncEngine
from odmantic.engine import AIOSessionType, SyncSessionType
from odmantic.query import QueryExpression
from typing_extensions import TypeAlias

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer
from ..utils import verify_params

_Query: TypeAlias = Union[QueryExpression, Dict[Any, Any], bool]


def sync_paginate(
    engine: SyncEngine,
    model: Type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[SyncSessionType] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if raw_params.include_total:  # noqa: SIM108
        total = engine.count(model, *queries, session=session)
    else:
        total = None

    items = engine.find(
        model,
        *queries,
        sort=sort,
        session=session,
        limit=raw_params.limit,
        skip=raw_params.offset or 0,
    )
    t_items = apply_items_transformer([*items], transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )


async def async_paginate(
    engine: AIOEngine,
    model: Type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[AIOSessionType] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if raw_params.include_total:
        total = await engine.count(model, *queries, session=session)
    else:
        total = None

    items = await engine.find(
        model,
        *queries,
        sort=sort,
        session=session,
        limit=raw_params.limit,
        skip=raw_params.offset or 0,
    )
    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )


@overload
async def paginate(
    engine: AIOEngine,
    model: Type[Model],
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
    model: Type[Model],
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
    model: Type[Model],
    *queries: _Query,
    # odmantic related
    sort: Optional[Any] = None,
    session: Optional[Union[SyncSessionType, AIOSessionType]] = None,
    # fastapi-pagination related
    params: Optional[AbstractParams] = None,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    func = async_paginate if isinstance(engine, AIOEngine) else sync_paginate

    return func(
        engine,  # type: ignore[arg-type]
        model,
        *queries,
        sort=sort,
        session=session,  # type: ignore[arg-type]
        params=params,
        transformer=transformer,  # type: ignore[arg-type]
        additional_data=additional_data,
    )
