__all__ = ["paginate"]

from typing import Any, Literal, Optional, TypeVar, Union

from bunnet import Document
from bunnet.odm.enums import SortDirection
from bunnet.odm.interfaces.aggregate import ClientSession, DocumentProjectionType
from bunnet.odm.queries.aggregation import AggregationQuery
from bunnet.odm.queries.find import FindMany

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.ext.utils import get_mongo_pipeline_filter_end
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

TDocument = TypeVar("TDocument", bound=Document)


def paginate(
    query: Union[TDocument, FindMany[TDocument], AggregationQuery[TDocument]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    projection_model: Optional[type[DocumentProjectionType]] = None,
    sort: Union[None, str, list[tuple[str, SortDirection]]] = None,
    session: Optional[ClientSession] = None,
    ignore_cache: bool = False,
    fetch_links: bool = False,
    lazy_parse: bool = False,
    aggregation_filter_end: Optional[Union[int, Literal["auto"]]] = None,
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

        if aggregation_filter_end is not None:
            if aggregation_filter_end == "auto":
                aggregation_filter_end = get_mongo_pipeline_filter_end(aggregation_query.aggregation_pipeline)
            filter_part = aggregation_query.aggregation_pipeline[:aggregation_filter_end]
            transform_part = aggregation_query.aggregation_pipeline[aggregation_filter_end:]
            aggregation_query.aggregation_pipeline = [
                *filter_part,
                {"$facet": {"metadata": [{"$count": "total"}], "data": [*paginate_data, *transform_part]}},
            ]
        else:
            aggregation_query.aggregation_pipeline.extend(
                [
                    {"$facet": {"metadata": [{"$count": "total"}], "data": paginate_data}},
                ],
            )

        data = aggregation_query.to_list()[0]
        items = data["data"]
        try:
            total = data["metadata"][0]["total"]
        except IndexError:
            total = 0
    else:
        items = query.find_many(
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

        if raw_params.include_total:
            total = query.find(
                {},
                session=session,
                ignore_cache=ignore_cache,
                fetch_links=False,
                **pymongo_kwargs,
            ).count()
        else:
            total = None

    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
