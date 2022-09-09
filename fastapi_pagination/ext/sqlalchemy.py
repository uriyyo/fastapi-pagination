from __future__ import annotations

from typing import Any, Optional, TypeVar, cast, no_type_check

from sqlalchemy import func, literal, literal_column, select
from sqlalchemy.orm import Query, noload
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams, RawParams
from ..types import PaginationQueryType

T = TypeVar("T", Select, Query)


@no_type_check
def paginate_query_using_row_number(query: Select, raw_params: RawParams) -> T:
    subquery = query.add_columns(func.row_number().over().label("__row_number__")).subquery()

    return query.from_statement(
        select(subquery).where(
            subquery.c.__row_number__.between(
                literal(raw_params.offset + 1),
                literal(raw_params.offset + raw_params.limit),
            )
        )
    )


def paginate_query(
    query: T,
    params: AbstractParams,
    query_type: PaginationQueryType = None,
) -> T:
    raw_params = params.to_raw_params()

    if query_type == "row-number":
        return paginate_query_using_row_number(query, raw_params)  # type: ignore

    return query.limit(raw_params.limit).offset(raw_params.offset)


def count_query(query: Select) -> Select:
    count_subquery = cast(Any, query.order_by(None)).options(noload("*")).subquery()
    return select(func.count(literal_column("*"))).select_from(count_subquery)


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage:
    params = resolve_params(params)

    total = query.count()
    items = paginate_query(query, params, query_type).all()

    return create_page(items, total, params)


__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
    "paginate_query_using_row_number",
]
