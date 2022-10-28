from typing import Any, Optional

from orm.models import QuerySet

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


async def paginate(
    query: QuerySet,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:
    params, raw_params = verify_params(params, "limit-offset")

    total = await query.count()
    items = await query.limit(raw_params.limit).offset(raw_params.offset).all()

    return create_page(items, total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
