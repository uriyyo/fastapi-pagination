from typing import Optional, Type, TypeVar, Union, cast

from django.db.models import Model, QuerySet
from django.db.models.base import ModelBase

from ..api import create_page
from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T", bound=Model)


def paginate(
    query: Union[Type[T], QuerySet[T]],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[T]:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, ModelBase):
        query = cast(Type[T], query).objects.all()

    total = query.count()
    query = query.all()[raw_params.offset : raw_params.offset + raw_params.limit]

    return create_page([*query], total, params, **(additional_data or {}))


__all__ = [
    "paginate",
]
