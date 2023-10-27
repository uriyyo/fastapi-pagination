__all__ = ["paginate"]

from typing import Any, Optional

from pony.orm.core import Query

from fastapi_pagination import create_page

from ..api import apply_items_transformer
from ..bases import AbstractParams
from ..types import AdditionalData, SyncItemsTransformer
from ..utils import verify_params


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    total = query.count() if raw_params.include_total else None
    items = query.fetch(raw_params.limit, raw_params.offset).to_list()
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
