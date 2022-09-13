from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params


async def paginate(
    collection: AsyncIOMotorCollection,
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    **kwargs: Any,
) -> AbstractPage:
    params = verify_params(params, "limit-offset")
    query_filter = query_filter or {}

    raw_params = params.to_raw_params().as_limit_offset()
    total = await collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)
    items = await cursor.to_list(length=raw_params.limit)

    return create_page(items, total, params)


async def paginate_aggregate(
    collection: AsyncIOMotorCollection,
    aggregate_pipeline: Optional[List[Dict[Any, Any]]] = None,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = verify_params(params, "limit-offset")
    aggregate_pipeline = aggregate_pipeline or []

    raw_params = params.to_raw_params().as_limit_offset()
    cursor = collection.aggregate(
        [
            *aggregate_pipeline,
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": [
                        {"$limit": raw_params.limit + raw_params.offset},
                        {"$skip": raw_params.offset},
                    ],
                }
            },
        ]
    )

    data = (await cursor.to_list(length=None))[0]
    total = data["metadata"][0]["total"]
    items = data["data"]

    return create_page(items, total, params)


__all__ = [
    "paginate",
    "paginate_aggregate",
]
