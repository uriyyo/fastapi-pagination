from __future__ import annotations

__all__ = [
    "paginate_query",
    "count_query",
    "paginate",
]

from typing import Any, Optional, TypeVar, cast

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Query, noload
from sqlalchemy.sql import Select

from .utils import generic_query_apply_params
from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T", Select, "Query[Any]")


def paginate_query(query: T, params: AbstractParams) -> T:
    return generic_query_apply_params(query, params.to_raw_params().as_limit_offset())


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
