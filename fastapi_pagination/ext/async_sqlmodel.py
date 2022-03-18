from typing import Optional, TypeVar, Union

from sqlmodel import SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", bound=SQLModel)


async def paginate(
    session: AsyncSession,
    query: Union[T, Select[T], SelectOfScalar[T]],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    total = await session.scalar(select(func.count("*")).select_from(query.subquery()))
    query_response = await session.exec(query.limit(raw_params.limit).offset(raw_params.offset))
    items = query_response.unique().all()

    return create_page(items, total, params)


__all__ = ["paginate"]
