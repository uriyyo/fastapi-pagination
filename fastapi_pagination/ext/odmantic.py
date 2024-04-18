__all__ = ["paginate"]

from typing import Any, Dict, Optional, Type, Union

from odmantic import AIOEngine, Model
from odmantic.engine import AIOSessionType
from odmantic.query import QueryExpression
from typing_extensions import TypeAlias

from ..api import apply_items_transformer, create_page
from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from ..utils import verify_params

_Query: TypeAlias = Union[QueryExpression, Dict[Any, Any], bool]


async def paginate(
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
