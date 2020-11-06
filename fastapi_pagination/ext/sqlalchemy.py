from __future__ import annotations

from typing import TypeVar, overload, Any

from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType, PaginationParams

T = TypeVar("T")


@overload
def paginate_query(query: Select[T], params: PaginationParamsType) -> Select[T]:
    pass


@overload
def paginate_query(query: Query[T], params: PaginationParamsType) -> Query[T]:
    pass


def paginate_query(query: Any, params: PaginationParamsType) -> Any:
    params = params.to_limit_offset()
    return query.limit(params.limit).offset(params.offset)


def paginate(query: Query[T], params: PaginationParams) -> BasePage[T]:
    total = query.count()
    items = paginate_query(query, params).all()

    return create_page(items, total, params)


__all__ = ["paginate_query", "paginate"]
