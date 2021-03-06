from typing import Optional

from orm.models import QuerySet
from sqlalchemy import func

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams


async def paginate(query: QuerySet, params: Optional[AbstractParams] = None) -> AbstractPage:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    expr = query.build_select_expression().alias()
    count_expr = func.count().select().select_from(expr)
    total = await query.database.fetch_val(count_expr)

    paginated_query = query.limit(raw_params.limit).build_select_expression().offset(raw_params.offset)

    rows = await query.database.fetch_all(paginated_query)
    items = [query.model_cls.from_row(row, select_related=query._select_related) for row in rows]

    return create_page(items, total, params)


__all__ = ["paginate"]
