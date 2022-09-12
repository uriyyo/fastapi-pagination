from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..api import resolve_params
from ..bases import AbstractPage, AbstractParams
from ..types import PaginationQueryType
from .sqlalchemy_future import async_exec_pagination

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
async def paginate(
    session: AsyncSession,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[TSQLModel]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[T]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[TSQLModel]:
    pass


@no_type_check
async def paginate(
    session: AsyncSession,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[Any]:
    params = resolve_params(params)

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return await async_exec_pagination(query, params, session.exec, query_type)


__all__ = [
    "paginate",
]
