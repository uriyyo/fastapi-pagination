from typing import Optional

from pony.orm.core import Query

from fastapi_pagination import create_page

from ..bases import AbstractPage, AbstractParams
from ..utils import verify_params


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = verify_params(params, "limit-offset")
    raw_params = params.to_raw_params().as_limit_offset()

    total = query.count()
    items = query.fetch(raw_params.limit, raw_params.offset).to_list()

    return create_page(items, total, params)


__all__ = ["paginate"]
