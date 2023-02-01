__all__ = ["paginate"]

from typing import Optional, Any

from pony.orm.core import Query

from fastapi_pagination import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    total = query.count()
    items = query.fetch(raw_params.limit, raw_params.offset).to_list()

    return create_page(items, total, params, **(additional_data or {}))
