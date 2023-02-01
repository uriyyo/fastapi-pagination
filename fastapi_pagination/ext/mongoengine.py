__all__ = ["paginate"]

from typing import Optional, Type, TypeVar, Union, cast, Any

from mongoengine import QuerySet
from mongoengine.base.metaclasses import TopLevelDocumentMetaclass

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T", bound=TopLevelDocumentMetaclass)


def paginate(
    query: Union[Type[T], QuerySet],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, TopLevelDocumentMetaclass):
        query = cast(Type[T], query).objects().all()

    total = query.count()
    cursor = query.skip(raw_params.offset).limit(raw_params.limit)
    items = [item.to_mongo() for item in cursor]

    return create_page(items, total, params, **(additional_data or {}))
