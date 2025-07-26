__all__ = ["apaginate", "paginate"]

from typing import Any, Optional, TypeVar, Union

from tortoise.models import Model
from tortoise.query_utils import Prefetch
from tortoise.queryset import QuerySet
from typing_extensions import deprecated

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.flow import flow_expr, run_async_flow
from fastapi_pagination.flows import generic_flow
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer

from .utils import generic_query_apply_params

TModel = TypeVar("TModel", bound=Model)


def _generate_query(
    query: QuerySet[TModel],
    prefetch_related: Union[bool, list[Union[str, Prefetch]]],
) -> QuerySet[TModel]:
    if prefetch_related:
        if prefetch_related is True:
            prefetch_related = [*query.model._meta.fetch_fields]

        return query.prefetch_related(*prefetch_related)

    return query


async def apaginate(
    query: Union[QuerySet[TModel], type[TModel]],
    params: Optional[AbstractParams] = None,
    prefetch_related: Union[bool, list[Union[str, Prefetch]]] = False,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    total: Optional[int] = None,
    config: Optional[Config] = None,
) -> Any:
    if not isinstance(query, QuerySet):
        query = query.all()

    return await run_async_flow(
        generic_flow(
            async_=True,
            total_flow=flow_expr(lambda: query.count() if total is None else total),
            limit_offset_flow=flow_expr(
                lambda raw_params: generic_query_apply_params(
                    _generate_query(query, prefetch_related),
                    raw_params,
                ).all()
            ),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        ),
    )


@deprecated("Use `apaginate` instead. This function will be removed in v0.15.0")
async def paginate(
    query: Union[QuerySet[TModel], type[TModel]],
    params: Optional[AbstractParams] = None,
    prefetch_related: Union[bool, list[Union[str, Prefetch]]] = False,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    total: Optional[int] = None,
    config: Optional[Config] = None,
) -> Any:
    return await apaginate(
        query,
        params=params,
        prefetch_related=prefetch_related,
        transformer=transformer,
        additional_data=additional_data,
        total=total,
        config=config,
    )
