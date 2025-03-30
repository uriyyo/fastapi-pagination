from __future__ import annotations

__all__ = ["apaginate", "paginate"]

import warnings
from typing import Any, Generic, Optional, TypeVar, Union, overload

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar
from typing_extensions import TypeAlias, deprecated

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.types import AdditionalData, AsyncItemsTransformer, ItemsTransformer, SyncItemsTransformer

from .sqlalchemy import apaginate as _apaginate
from .sqlalchemy import paginate as _paginate

try:
    from sqlmodel.sql._expression_select_cls import SelectBase
except ImportError:  # pragma: no cover
    _T = TypeVar("_T")

    class SelectBase(Generic[_T]):  # type: ignore[no-redef]
        pass


T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


_InputQuery: TypeAlias = Union[
    Select[TSQLModel],
    type[TSQLModel],
    SelectBase[TSQLModel],
    SelectOfScalar[T],
]
_InputCountQuery: TypeAlias = Union[
    Select[TSQLModel],
    SelectOfScalar[T],
]


def _prepare_query(query: _InputQuery[TSQLModel, T], /) -> _InputQuery[TSQLModel, T]:
    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)  # type: ignore[arg-type]

    return query


@overload
def paginate(
    session: Session,
    query: _InputQuery[TSQLModel, T],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[_InputCountQuery[TSQLModel, T]] = None,
    subquery_count: bool = True,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
    config: Optional[Config] = None,
) -> Any:
    pass


@overload
@deprecated("Use `apaginate` instead. This function will be removed in v0.14.0")
async def paginate(
    session: Union[AsyncSession, AsyncConnection],
    query: _InputQuery[TSQLModel, T],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[_InputCountQuery[TSQLModel, T]] = None,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
    config: Optional[Config] = None,
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
    config: Optional[Config] = None,
) -> Any:
    query = _prepare_query(query)

    if count_query:
        count_query = _prepare_query(count_query)

    if isinstance(session, (AsyncSession, AsyncConnection)):
        warnings.warn(
            "Use `apaginate` instead. This function overload will be removed in v0.14.0",
            DeprecationWarning,
            stacklevel=2,
        )

        return apaginate(
            session,
            query,
            params,
            count_query=count_query,
            subquery_count=subquery_count,
            transformer=transformer,
            additional_data=additional_data,
            unique=unique,
            config=config,
        )

    return _paginate(  # type: ignore[misc]
        session,
        query,
        params,
        count_query=count_query,
        subquery_count=subquery_count,
        transformer=transformer,  # type: ignore[arg-type]
        additional_data=additional_data,
        unique=unique,
        config=config,
    )


async def apaginate(
    session: Union[AsyncSession, AsyncConnection],
    query: _InputQuery[TSQLModel, T],
    params: Optional[AbstractParams] = None,
    *,
    count_query: Optional[_InputCountQuery[TSQLModel, T]] = None,
    subquery_count: bool = True,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    unique: bool = True,
    config: Optional[Config] = None,
) -> Any:
    query = _prepare_query(query)

    if count_query:
        count_query = _prepare_query(count_query)  # type: ignore[assignment]

    return await _apaginate(
        session,
        query,  # type: ignore[arg-type]
        params,
        count_query=count_query,
        subquery_count=subquery_count,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
        config=config,
    )
