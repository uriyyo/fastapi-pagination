from typing import Optional

from pony.orm.core import Query

from fastapi_pagination import create_page, resolve_params

from ..bases import AbstractPage, AbstractParams


def paginate(
    query: Query,
    params: Optional[AbstractParams] = None,
) -> AbstractPage:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    total = query.count()
    items = query.fetch(raw_params.limit, raw_params.offset).to_list()

    return create_page(items, total, params)


__all__ = ["paginate"]
