from __future__ import annotations

from typing import Any, Optional, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", Select, Query)


def paginate_query(query: T, params: AbstractParams) -> T:
    raw_params = params.to_raw_params()
    return query.limit(raw_params.limit).offset(raw_params.offset)

def get_count(query: T):
    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = query.session.execute(count_q).scalar()
    return count


def _to_dict(obj: Any) -> Any:
    try:
        return obj._asdict()
    except AttributeError:
        return obj


def paginate(query: Query, params: Optional[AbstractParams] = None) -> AbstractPage:
    params = resolve_params(params)

    total = get_count(query)
    items = [_to_dict(item) for item in paginate_query(query, params)]

    return create_page(items, total, params)


__all__ = ["paginate_query", "paginate"]
