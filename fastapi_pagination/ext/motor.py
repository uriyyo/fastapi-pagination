__all__ = ["paginate"]

from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


async def paginate(
    collection: AsyncIOMotorCollection,
    query_filter: Optional[Dict[Any, Any]] = None,
    params: Optional[AbstractParams] = None,
    additional_data: AdditionalData = None,
    **kwargs: Any,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")
    query_filter = query_filter or {}

    total = await collection.count_documents(query_filter)
    cursor = collection.find(query_filter, skip=raw_params.offset, limit=raw_params.limit, **kwargs)
    items = await cursor.to_list(length=raw_params.limit)

    return create_page(items, total, params, **(additional_data or {}))


async def paginate_aggregate(
    collection: AsyncIOMotorCollection,
    aggregate_pipeline: Optional[List[Dict[Any, Any]]] = None,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")
    aggregate_pipeline = aggregate_pipeline or []

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

    items = data["data"]
    try:
        total = data["metadata"][0]["total"]
    except IndexError:
        total = 0

    return create_page(items, total, params, **(additional_data or {}))
