from __future__ import annotations

from contextlib import suppress
from typing import Sequence

from gino.loader import ModelLoader
from sqlalchemy import func
from sqlalchemy.sql import Select

from ..page import BasePage, create_page
from ..params import PaginationParamsType
from .sqlalchemy import paginate_query


async def _fetch_items(query: Select, params: PaginationParamsType) -> Sequence:
    params = params.to_limit_offset()
    items = []

    gino = query._execution_options["loader"].model.__metadata__  # type: ignore

    with suppress(StopAsyncIteration):
        async with gino.transaction():
            iterator = query.gino.iterate().__aiter__()  # type: ignore

            for _ in range(params.offset):
                await iterator.__anext__()

            for _ in range(params.limit):
                items.append(await iterator.__anext__())

    return items


async def paginate(query: Select, params: PaginationParamsType) -> BasePage:
    count_query = query
    using_loader = False

    # FIXME: Should be better solution for this problem
    # Check if it's a ModelLoader to add distinct columns to have correct count value
    if isinstance(count_query, ModelLoader) and count_query._distinct:
        count_query = count_query.query.distinct(*count_query._distinct)
        using_loader = True
    else:
        loader = getattr(query, "_execution_options", {}).get("loader")
        if loader and loader._distinct:
            count_query = query.distinct(*loader._distinct)
            using_loader = True

    total = await func.count().select().select_from(count_query.alias()).gino.scalar()

    if using_loader:
        items = await _fetch_items(query, params)
    else:
        items = await paginate_query(query, params).gino.all()  # type: ignore

    return create_page(items, total, params)


__all__ = ["paginate"]
