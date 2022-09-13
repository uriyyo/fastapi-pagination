from typing import Any, Optional

from orm.models import QuerySet

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params


async def paginate(
    query: QuerySet,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params = verify_params(params, "limit-offset")
    raw_params = params.to_raw_params().as_limit_offset()

    total = await query.count()
    items = await query.limit(raw_params.limit).offset(raw_params.offset).all()

    return create_page(items, total, params)


__all__ = [
    "paginate",
]
