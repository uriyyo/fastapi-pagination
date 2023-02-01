from __future__ import annotations

__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
    "paginate_using_cursor",
    "paginate_cursor_process_items",
]

from typing import Any, Optional, Sequence, Tuple, TypeVar, cast, no_type_check

from fastapi import HTTPException
from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Query, noload
from sqlalchemy.sql import Select

from ..api import create_page
from ..bases import AbstractParams, CursorRawParams
from ..types import AdditionalData
from ..utils import verify_params

try:
    from sqlakeyset import paging
except ImportError:
    paging = None


T = TypeVar("T", Select, "Query[Any]")


# adapted from  sqlakeyset.paging.perform_paging
@no_type_check
def paginate_using_cursor(
    q: Select,
    raw_params: CursorRawParams,
) -> Tuple[Any, Tuple[Any, ...]]:
    if paging is None:
        raise ImportError("sqlakeyset is not installed")

    try:
        place, backwards = paging.process_args(page=raw_params.cursor)
    except paging.InvalidPage:
        raise HTTPException(status_code=400, detail="Invalid cursor")

    try:
        dialect = q.bind.dialect
    except AttributeError:
        dialect = None

    selectable = q.selectable
    column_descriptions = q.column_descriptions
    keys = paging.orm_query_keys(q)

    order_cols = paging.parse_ob_clause(selectable)
    if backwards:
        order_cols = [c.reversed for c in order_cols]

    mapped_ocols = [paging.find_order_key(ocol, column_descriptions) for ocol in order_cols]

    clauses = [col.ob_clause for col in mapped_ocols]

    if not clauses:
        raise ValueError("Order by clause is required for cursor pagination")

    q = q.order_by(None).order_by(*clauses)

    extra_columns = [col.extra_column for col in mapped_ocols if col.extra_column is not None]
    q = q.add_columns(*extra_columns)

    if place:
        condition = paging.where_condition_for_page(order_cols, place, dialect)
        groupby = paging.group_by_clauses(selectable)
        if groupby:
            q = q.having(condition)
        else:
            q = q.where(condition)

    pagination_info = order_cols, mapped_ocols, extra_columns, keys, backwards, place
    return q.limit(raw_params.size + 1), pagination_info  # 1 extra to check if there's a further page


def paginate_cursor_process_items(
    items: Sequence[Any],
    pagination_info: Tuple[Any, ...],
    raw_params: CursorRawParams,
) -> Tuple[Sequence[Any], Optional[str], Optional[str]]:
    order_cols, mapped_ocols, extra_columns, keys, backwards, current_place = pagination_info

    page = paging.core_page_from_rows(
        (
            order_cols,
            mapped_ocols,
            extra_columns,
            items,
            None,
        ),
        None,
        raw_params.size,
        backwards,
        current_place,
    )

    next_ = page.paging.bookmark_next if page.paging.has_next else None
    previous = page.paging.bookmark_previous if page.paging.has_previous else None

    return [*page], previous, next_


def paginate_query(query: T, params: AbstractParams) -> T:
    raw_params = params.to_raw_params().as_limit_offset()
    return query.limit(raw_params.limit).offset(raw_params.offset)


def count_query(query: Select) -> Select:
    count_subquery = cast(Any, query.order_by(None)).options(noload("*")).subquery()
    return select(func.count(literal_column("*"))).select_from(count_subquery)


def paginate(
    query: Query[Any],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, _ = verify_params(params, "limit-offset")

    total = query.count()
    items = paginate_query(query, params).all()

    return create_page(items, total, params, **(additional_data or {}))
