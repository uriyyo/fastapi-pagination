from __future__ import annotations

__all__ = ["paginate"]

from copy import copy
from typing import Any, Optional, TypeVar, Union

from beanie import Document
from beanie.odm.enums import SortDirection
from beanie.odm.interfaces.aggregate import DocumentProjectionType
from beanie.odm.queries.aggregation import AggregationQuery
from beanie.odm.queries.find import FindMany
from motor.motor_asyncio import AsyncIOMotorClientSession

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer
from fastapi_pagination.utils import verify_params

TDocument = TypeVar("TDocument", bound=Document)


async def paginate(
    query: Union[TDocument, FindMany[TDocument], AggregationQuery[TDocument]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    projection_model: Optional[type[DocumentProjectionType]] = None,
    sort: Union[None, str, list[tuple[str, SortDirection]]] = None,
    session: Optional[AsyncIOMotorClientSession] = None,
    ignore_cache: bool = False,
    fetch_links: bool = False,
    lazy_parse: bool = False,
    **pymongo_kwargs: Any,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, AggregationQuery):
        aggregation_query = query.clone()  # type: ignore[no-untyped-call]
        paginate_data = []
        if raw_params.limit is not None:
            paginate_data.append({"$limit": raw_params.limit + (raw_params.offset or 0)})
        if raw_params.offset is not None:
            paginate_data.append({"$skip": raw_params.offset})

        aggregation_query.aggregation_pipeline.extend(
            [
                {"$facet": {"metadata": [{"$count": "total"}], "data": paginate_data}},
            ],
        )
        data = (await aggregation_query.to_list())[0]
        items = data["data"]
        try:
            total = data["metadata"][0]["total"]
        except IndexError:
            total = 0
    else:
        # avoid original query mutation
        count_query = copy(query)
        query = copy(query)

        if raw_params.include_total:
            total = await count_query.find(
                {},
                session=session,
                ignore_cache=ignore_cache,
                fetch_links=fetch_links,
                **pymongo_kwargs,
            ).count()
        else:
            total = None

        items = await query.find_many(
            limit=raw_params.limit,
            skip=raw_params.offset,
            projection_model=projection_model,
            sort=sort,
            session=session,
            ignore_cache=ignore_cache,
            fetch_links=fetch_links,
            lazy_parse=lazy_parse,
            **pymongo_kwargs,
        ).to_list()

    t_items = await apply_items_transformer(items, transformer, async_=True)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
