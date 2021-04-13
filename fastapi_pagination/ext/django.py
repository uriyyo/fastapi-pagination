from typing import Optional

from django.db.models import QuerySet
from pydantic import BaseModel

from ..page import BasePage, create_page
from ..params import PaginationParamsType, resolve_params


# To convert from a django ORM model to a pydantic Model, provide a BaseModel with from_django() method to map fields
# from django to pydantic
def paginate(query: QuerySet, schema: BaseModel, params: Optional[PaginationParamsType] = None) -> BasePage:
    params = resolve_params(params)
    limit_offset_params = params.to_limit_offset()

    total = query.count()
    start = limit_offset_params.limit * limit_offset_params.offset
    end = start + limit_offset_params.limit
    rows = query.all()[start:end]

    items = [schema.from_django(row) for row in rows]

    return create_page(items, total, params)


__all__ = ["paginate"]
