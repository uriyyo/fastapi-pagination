from typing import Any, Optional, TypeVar, Union, cast

__all__ = ["paginate"]

from django.db.models import Model, QuerySet
from django.db.models.base import ModelBase

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, SyncItemsTransformer
from fastapi_pagination.utils import verify_params

T = TypeVar("T", bound=Model)


def paginate(
    query: Union[type[T], QuerySet[T]],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, ModelBase):
        query = cast(type[T], query).objects.all()

    total = query.count() if raw_params.include_total else None
    query = query.all()[raw_params.as_slice()]
    items = [*query]
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
