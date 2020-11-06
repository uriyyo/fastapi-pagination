from __future__ import annotations
from typing import Tuple, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType, PaginationParams

T = TypeVar("T")


def transform_query(
    query: Select[T], params: PaginationParamsType
) -> Tuple[Select[int], Select[T]]:
    params = params.to_limit_offset()

    return (
        query.with_only_columns([func.count()]),
        query.limit(params.limit).offset(params.offset),
    )


def paginate(
    query: Select[T], params: PaginationParams, session: Session
) -> BasePage[T]:
    count, select = transform_query(query, params)

    total = select.scalar(count)
    items = session.execute(select)

    return create_page(items, total, params)


__all__ = ["transform_query", "paginate"]
