from typing import Optional

from orm.models import QuerySet
from sqlalchemy import func

from ..page import BasePage, create_page
from ..params import PaginationParamsType, resolve_params


async def paginate(query: QuerySet, params: Optional[PaginationParamsType] = None) -> BasePage:
    params = resolve_params(params)
    limit_offset_params = params.to_limit_offset()

    expr = query.build_select_expression().alias()
    count_expr = func.count().select().select_from(expr)
    total = await query.database.fetch_val(count_expr)

    paginated_query = (
        query.limit(limit_offset_params.limit).build_select_expression().offset(limit_offset_params.offset)
    )

    rows = await query.database.fetch_all(paginated_query)
    items = [query.model_cls.from_row(row, select_related=query._select_related) for row in rows]

    return create_page(items, total, params)


__all__ = ["paginate"]
