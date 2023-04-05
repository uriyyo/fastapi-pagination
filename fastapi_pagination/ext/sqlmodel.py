__all__ = ["paginate"]

from typing import Any, Optional, Type, TypeVar, no_type_check, overload, Union

from sqlmodel import Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession, AsyncConnection
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractParams
from ..types import AdditionalData, ItemsTransformer, AsyncItemsTransformer, SyncItemsTransformer
from .sqlalchemy import paginate as _paginate

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
def paginate(
    session: Session,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    session: Session,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    session: Session,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    pass


@no_type_check
def paginate(
    session: Session,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return _paginate(
        session,
        query,
        params,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
    )
