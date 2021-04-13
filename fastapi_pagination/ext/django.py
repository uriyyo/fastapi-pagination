from typing import Optional

from django.db.models import QuerySet
from pydantic import BaseModel


# To convert from a django ORM model to a pydantic Model, provide a BaseModel with from_django() method to map fields
# from django to pydantic
from fastapi_pagination import resolve_params, create_page
from fastapi_pagination.bases import AbstractParams, AbstractPage


def paginate(query: QuerySet, schema: BaseModel, params: Optional[AbstractParams] = None) -> AbstractPage:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    total = query.count()
    start = raw_params.limit * raw_params.offset
    end = start + raw_params.limit
    rows = query.all()[start:end]

    items = [schema.from_django(row) for row in rows]

    return create_page(items, total, params)


__all__ = ["paginate"]
