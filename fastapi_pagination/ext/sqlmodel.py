__all__ = ["paginate"]

from typing import Any, Optional, Type, TypeVar, Union, no_type_check, overload

from sqlmodel import Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncConnection, AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer
from .sqlalchemy import paginate as _paginate

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
def paginate(
    session: Session,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    session: Session,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    session: Session,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    pass


@no_type_check
def paginate(
    session: Session,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    subquery_count: bool = True,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return _paginate(
        session,
        query,
        params,
        subquery_count=subquery_count,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
    )
