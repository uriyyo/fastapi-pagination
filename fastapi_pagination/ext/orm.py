from orm.models import QuerySet

from ..page import BasePage, create_page
from ..params import PaginationParamsType


async def paginate(query: QuerySet, params: PaginationParamsType) -> BasePage:
    limit_offset_params = params.to_limit_offset()

    total = await query.count()

    paginated_query = (
        query.limit(limit_offset_params.limit).build_select_expression().offset(limit_offset_params.offset)
    )

    rows = await query.database.fetch_all(paginated_query)
    items = [query.model_cls.from_row(row, select_related=query._select_related) for row in rows]

    return create_page(items, total, params)


__all__ = ["paginate"]
