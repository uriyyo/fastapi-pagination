from __future__ import annotations

import warnings
from typing import Any, Callable, Optional, Tuple, TypeVar, cast, no_type_check

from fastapi import HTTPException
from sqlakeyset.paging import (
    InvalidPage,
    core_page_from_rows,
    find_order_key,
    group_by_clauses,
    orm_query_keys,
    parse_ob_clause,
    process_args,
    where_condition_for_page,
)
from sqlalchemy import func, literal, literal_column, select
from sqlalchemy.orm import Query, noload
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams, RawParams
from ..types import PaginationQueryType

T = TypeVar("T", Select, Query)


class ExperimentalWarning(Warning):
    pass


# adapted from  sqlakeyset.paging.perform_paging
@no_type_check
def paginate_using_cursor(q: Select, raw_params: RawParams) -> Any:
    try:
        place, backwards = process_args(page=raw_params.metadata.get("cursor"))
    except InvalidPage:
        raise HTTPException(status_code=400, detail="Invalid cursor")

    dialect = q.bind.dialect
    selectable = q.selectable
    column_descriptions = q.column_descriptions
    keys = orm_query_keys(q)

    order_cols = parse_ob_clause(selectable)
    if backwards:
        order_cols = [c.reversed for c in order_cols]

    mapped_ocols = [find_order_key(ocol, column_descriptions) for ocol in order_cols]

    clauses = [col.ob_clause for col in mapped_ocols]

    if not clauses:
        raise ValueError("Order by clause is required for cursor pagination")

    q = q.order_by(None).order_by(*clauses)

    extra_columns = [col.extra_column for col in mapped_ocols if col.extra_column is not None]
    q = q.add_columns(*extra_columns)

    if place:
        condition = where_condition_for_page(order_cols, place, dialect)
        groupby = group_by_clauses(selectable)
        if groupby:
            q = q.having(condition)
        else:
            q = q.where(condition)

    raw_params.metadata.update(
        order_cols=order_cols,
        mapped_ocols=mapped_ocols,
        extra_columns=extra_columns,
        keys=keys,
        backwards=backwards,
        current_place=place,
    )

    return q.limit(raw_params.limit + 1)  # 1 extra to check if there's a further page


def _cursor_pagination_process_items(items: Any, params: AbstractParams) -> Any:
    raw_params = params.to_raw_params()

    page = core_page_from_rows(
        (
            raw_params.metadata["order_cols"],
            raw_params.metadata["mapped_ocols"],
            raw_params.metadata["extra_columns"],
            items,
            None,
        ),
        None,
        raw_params.limit,
        raw_params.metadata["backwards"],
        raw_params.metadata["current_place"],
    )

    raw_params.metadata.update(
        next=page.paging.bookmark_next if page.paging.has_next else None,
        previous=page.paging.bookmark_previous if page.paging.has_previous else None,
    )

    return [*page]


@no_type_check
def paginate_using_row_number(query: Select, raw_params: RawParams) -> T:
    subquery = query.add_columns(func.row_number().over().label("__row_number__")).subquery()

    return query.from_statement(
        select(subquery).where(
            subquery.c.__row_number__.between(
                literal(raw_params.offset + 1),
                literal(raw_params.offset + raw_params.limit),
            )
        )
    )


def _noop(items: Any, _: AbstractParams) -> Any:
    return items


def paginate_query(
    query: T,
    params: AbstractParams,
    query_type: PaginationQueryType = None,
) -> Tuple[T, Callable[[Any, AbstractParams], Any]]:
    raw_params = params.to_raw_params()

    if params.metadata.get("type") == "cursor":
        if isinstance(query, Query):
            raise ValueError("Cursor pagination is not supported for old ORM Query queries")

        warnings.warn("Cursor pagination is experimental", ExperimentalWarning)
        return paginate_using_cursor(query, raw_params), _cursor_pagination_process_items

    if query_type == "row-number":
        return paginate_using_row_number(query, raw_params), _noop

    return query.limit(raw_params.limit).offset(raw_params.offset), _noop


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
    raw_params = params.to_raw_params()

    total = query.count() if raw_params.need_total else None
    query, process_items = paginate_query(query, params, query_type)
    items = process_items(query.all(), params)

    return create_page(items, total, params)


__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
    "paginate_using_row_number",
]
