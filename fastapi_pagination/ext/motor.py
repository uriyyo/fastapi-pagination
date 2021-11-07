from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(
    collection: AsyncIOMotorCollection,
    query_filter: dict = {},
    params: Optional[AbstractParams] = None,
    **kwargs: Any,
) -> AbstractPage:
    params = resolve_params(params)

    raw_params = params.to_raw_params()
    total = await collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)
    items = await cursor.to_list(length=raw_params.limit)

    return create_page(items, total, params)


__all__ = ["paginate"]
