from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.engine import Connection
from sqlalchemy.sql import Select

from fastapi_pagination.api import apply_items_transformer, create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData, ItemsTransformer
from fastapi_pagination.utils import verify_params


def paginate(
    conn: Connection,
    stmt: Select,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    total = conn.scalar(stmt.with_only_columns(func.count()))
    q = stmt.offset(raw_params.offset).limit(raw_params.limit)
    items = conn.execute(q).all()

    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total,
        params,
        **(additional_data or {}),
    )
