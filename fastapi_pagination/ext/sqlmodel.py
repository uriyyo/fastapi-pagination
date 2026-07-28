from __future__ import annotations

__all__ = ["apaginate", "paginate"]

from typing import Any, Generic, TypeAlias, TypeVar

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.types import (
    AdditionalData,
    AsyncItemsTransformer,
    SyncAdditionalData,
    SyncItemsTransformer,
)

from .sqlalchemy import apaginate as _apaginate
from .sqlalchemy import paginate as _paginate

try:
    from sqlmodel.sql._expression_select_cls import SelectBase
except ImportError:  # pragma: no cover
    _T = TypeVar("_T")

    class SelectBase(Generic[_T]):
        pass


T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


_InputQuery: TypeAlias = Select[TSQLModel] | type[TSQLModel] | SelectBase[TSQLModel] | SelectOfScalar[T]
_InputCountQuery: TypeAlias = Select[TSQLModel] | SelectOfScalar[T]


def _prepare_query(query: _InputQuery[TSQLModel, T], /) -> Select[TSQLModel] | SelectOfScalar[T]:
    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)  # type: ignore[ty:no-matching-overload]

    return query


def paginate(
    session: Session,
    query: _InputQuery[TSQLModel, T],
    params: AbstractParams | None = None,
    *,
    count_query: _InputCountQuery[TSQLModel, T] | None = None,
    subquery_count: bool = True,
    transformer: SyncItemsTransformer | None = None,
    additional_data: SyncAdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    query = _prepare_query(query)

    if count_query is not None:
        count_query = _prepare_query(count_query)

    return _paginate(
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


async def apaginate(
    session: AsyncSession | AsyncConnection,
    query: _InputQuery[TSQLModel, T],
    params: AbstractParams | None = None,
    *,
    count_query: _InputCountQuery[TSQLModel, T] | None = None,
    subquery_count: bool = True,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    query = _prepare_query(query)

    if count_query is not None:
        count_query = _prepare_query(count_query)

    return await _apaginate(
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
