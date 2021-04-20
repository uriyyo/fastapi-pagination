from typing import Optional, Type, TypeVar, Union, cast

from django.db.models import Model, QuerySet
from django.db.models.base import ModelBase

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", bound=Model)


def paginate(query: Union[Type[T], QuerySet[T]], params: Optional[AbstractParams] = None) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if isinstance(query, ModelBase):
        query = cast(Type[T], query).objects.all()

    total = query.count()
    query = query.all()[raw_params.offset : raw_params.offset + raw_params.limit]

    return create_page([*query], total, params)


__all__ = ["paginate"]
