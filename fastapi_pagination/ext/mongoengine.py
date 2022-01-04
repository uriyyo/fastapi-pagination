from typing import Optional, Type, TypeVar, Union, cast

from mongoengine import QuerySet
from mongoengine.base.metaclasses import TopLevelDocumentMetaclass

from fastapi_pagination.api import create_page, resolve_params
from fastapi_pagination.bases import AbstractPage, AbstractParams

T = TypeVar("T", bound=TopLevelDocumentMetaclass)


def paginate(
    query: Union[Type[T], QuerySet],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if isinstance(query, TopLevelDocumentMetaclass):
        query = cast(Type[T], query).objects().all()

    total = query.count()
    cursor = query.skip(raw_params.offset).limit(raw_params.limit)
    items = [item.to_mongo() for item in cursor]

    return create_page(items, total, params)


__all__ = ["paginate"]
