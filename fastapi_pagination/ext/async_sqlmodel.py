from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractPage, AbstractParams
from ..types import AdditionalData
from ..utils import verify_params
from .sqlalchemy_future import async_exec_pagination

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
async def paginate(
    session: AsyncSession,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[TSQLModel]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[T]:
    pass


@overload
async def paginate(
    session: AsyncSession,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[TSQLModel]:
    pass


@no_type_check
async def paginate(
    session: AsyncSession,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[Any]:
    params, _ = verify_params(params, "limit-offset", "cursor")

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return await async_exec_pagination(query, params, session.exec, additional_data)


__all__ = [
    "paginate",
]
