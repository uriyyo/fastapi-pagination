from __future__ import annotations

from typing import Tuple, TypeVar, overload, Any

from sqlalchemy import func
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType, PaginationParams

T = TypeVar("T")


@overload
def transform_query(
        query: Query[T], params: PaginationParamsType
) -> Query[T]:
    pass


@overload
def transform_query(
        query: Select[T], params: PaginationParamsType
) -> Tuple[Select[int], Select[T]]:
    pass


def transform_query(
        query: Any, params: PaginationParamsType
) -> Any:
    params = params.to_limit_offset()
    select = query.limit(params.limit).offset(params.offset)

    if isinstance(query, Query):
        return select

    return (
        query.with_only_columns([func.count()]),
        select,
    )


def paginate(query: Query[T], params: PaginationParams) -> BasePage[T]:
    total = query.count()
    items = transform_query(query, params).all()

    return create_page(items, total, params)


__all__ = ["transform_query", "paginate"]
