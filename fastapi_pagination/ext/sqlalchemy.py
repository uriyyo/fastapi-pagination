from __future__ import annotations

from typing import Any, Optional, TypeVar, cast

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Query, noload
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", Select, Query)


def paginate_query(query: T, params: AbstractParams) -> T:
    raw_params = params.to_raw_params()
    return query.limit(raw_params.limit).offset(raw_params.offset)


def count_query(query: Select) -> Select:
    count_subquery = cast(Any, query.order_by(None)).options(noload("*")).subquery()
    return select(func.count(literal_column("*"))).select_from(count_subquery)


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = query.count()
    items = paginate_query(query, params).all()

    return create_page(items, total, params)


__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
]
