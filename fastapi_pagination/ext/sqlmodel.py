from __future__ import annotations

__all__ = ["apaginate", "paginate"]

from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar
from typing_extensions import TypeAliasType

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


_InputQuery = TypeAliasType(
    "_InputQuery",
    "type[TSQLModel] | SelectBase[T]",
    type_params=(TSQLModel, T),
)
_InputCountQuery = TypeAliasType(
    "_InputCountQuery",
    "type[TSQLModel] | SelectBase[T]",
    type_params=(TSQLModel, T),
)


def _prepare_query(query: _InputQuery[TSQLModel, T], /) -> Any:
    if not isinstance(query, (Select, SelectOfScalar)):
        return select(query)  # type: ignore[ty:no-matching-overload]

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
    prepared_query = _prepare_query(query)
    prepared_count_query = _prepare_query(count_query) if count_query is not None else None

    return _paginate(
        session,
        prepared_query,
        params,
        count_query=prepared_count_query,
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
    prepared_query = _prepare_query(query)
    prepared_count_query = _prepare_query(count_query) if count_query is not None else None

    return await _apaginate(
        session,
        prepared_query,
        params,
        count_query=prepared_count_query,
        subquery_count=subquery_count,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
        config=config,
    )
