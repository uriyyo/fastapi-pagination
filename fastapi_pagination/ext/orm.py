from typing import Any, Optional

from orm.models import QuerySet

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params


async def paginate(
    query: QuerySet,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params, raw_params = verify_params(params, "limit-offset")

    total = await query.count()
    items = await query.limit(raw_params.limit).offset(raw_params.offset).all()

    return create_page(items, total, params)


__all__ = [
    "paginate",
]
