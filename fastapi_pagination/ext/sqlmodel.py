__all__ = ["paginate"]

from typing import Any, Generic, Optional, Type, TypeVar, Union, overload

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer
from .sqlalchemy import paginate as _paginate

try:
    from sqlmodel.sql._expression_select_cls import SelectBase
except ImportError:
    _T = TypeVar("_T")

    class SelectBase(Generic[_T]):  # type: ignore[no-redef]
        pass


T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
def paginate(
    session: Session,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[Select[TSQLModel]] = None,
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
    count_query: Optional[SelectOfScalar[T]] = None,
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
    count_query: Optional[TSQLModel] = None,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    pass


@overload
def paginate(
    session: Session,
    query: SelectBase[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[TSQLModel] = None,
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
    count_query: Optional[Select[TSQLModel]] = None,
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
    count_query: Optional[SelectOfScalar[T]] = None,
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
    count_query: Optional[Type[TSQLModel]] = None,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    pass


@overload
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: SelectBase[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[Type[TSQLModel]] = None,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    pass


def paginate(
    session: Union[AsyncSession, AsyncConnection, Session],
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[Any] = None,
    subquery_count: bool = True,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
) -> Any:
    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return _paginate(  # type: ignore
        session,  # type: ignore[arg-type]
        query,
        params,
        count_query=count_query,
        subquery_count=subquery_count,
        transformer=transformer,  # type: ignore[arg-type]
        additional_data=additional_data,
        unique=unique,
    )
