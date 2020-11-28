from __future__ import annotations

from typing import Optional, TypeVar

from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType, resolve_params

T = TypeVar("T", Select, Query)


def paginate_query(query: T, params: PaginationParamsType) -> T:
    params = params.to_limit_offset()
    return query.limit(params.limit).offset(params.offset)  # type: ignore


def paginate(query: Query, params: Optional[PaginationParamsType] = None) -> BasePage:
    params = resolve_params(params)

    total = query.count()
    items = paginate_query(query, params).all()

    return create_page(items, total, params)


__all__ = ["paginate_query", "paginate"]
