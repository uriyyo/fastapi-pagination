from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from .sqlalchemy import count_query, paginate_query

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
async def paginate(
    session: AsyncSession,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[TSQLModel]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[T]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[TSQLModel]:
    pass


@no_type_check
async def paginate(
    session: AsyncSession,
    query: Any,
    params: Optional[AbstractParams] = None,
) -> AbstractPage[Any]:
    params = resolve_params(params)

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    total = await session.scalar(count_query(query))
    items = await session.exec(paginate_query(query, params))

    return create_page(items.unique().all(), total, params)


__all__ = [
    "paginate",
]
