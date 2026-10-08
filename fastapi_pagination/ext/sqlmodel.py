from __future__ import annotations

__all__ = ["apaginate", "paginate"]

from collections.abc import Awaitable, Callable, Mapping
from functools import wraps
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_scoped_session
from sqlalchemy.util import await_only
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar
from typing_extensions import ParamSpec, TypeAliasType

from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.config import Config
from fastapi_pagination.types import (
    AdditionalData,
    AdditionalDataResult,
    AsyncItemsTransformer,
    SyncAdditionalData,
    SyncItemsTransformer,
)

from .sqlalchemy import apaginate as _apaginate
from .sqlalchemy import paginate as _paginate

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import CoreExecuteOptionsParameter

try:
    from sqlmodel.sql._expression_select_cls import SelectBase
except ImportError:  # pragma: no cover
    _T = TypeVar("_T")

    class SelectBase(Generic[_T]):
        pass


T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")
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

_BindParams = TypeAliasType(
    "_BindParams",
    "Mapping[str, Any]",
)


def _prepare_query(query: _InputQuery[TSQLModel, T], /) -> Any:
    if not isinstance(query, (Select, SelectOfScalar)):
        return select(query)  # type: ignore[ty:no-matching-overload]

    return query


@overload
def _to_sync(func: None, /) -> None:
    pass


@overload
def _to_sync(func: AdditionalDataResult, /) -> AdditionalDataResult:
    pass


@overload
def _to_sync(func: Callable[P, Awaitable[R]], /) -> Callable[P, R]:
    pass


@overload
def _to_sync(func: Callable[P, Awaitable[R] | R], /) -> Callable[P, R]:
    pass


def _to_sync(
    func: Callable[P, Awaitable[R] | R] | AdditionalDataResult | None,
    /,
) -> Callable[P, R] | AdditionalDataResult | None:
    if func is None or isinstance(func, dict):
        return func

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        res = func(*args, **kwargs)

        return await_only(res) if isinstance(res, Awaitable) else res

    return wrapper


def paginate(
    session: Session,
    query: _InputQuery[TSQLModel, T],
    params: AbstractParams | None = None,
    *,
    count_query: _InputCountQuery[TSQLModel, T] | None = None,
    subquery_count: bool = True,
    bind_params: _BindParams | None = None,
    execute_options: CoreExecuteOptionsParameter | None = None,
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
        bind_params=bind_params,
        execute_options=execute_options,
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
    bind_params: _BindParams | None = None,
    execute_options: CoreExecuteOptionsParameter | None = None,
    transformer: AsyncItemsTransformer | None = None,
    additional_data: AdditionalData | None = None,
    unique: bool = True,
    config: Config | None = None,
) -> Any:
    # async_scoped_session does not proxy `run_sync`
    if isinstance(session, async_scoped_session):
        session = session()

    # sqlmodel marks `AsyncSession.execute` as deprecated in favour of `exec` and emits a warning,
    # so we run sync version of pagination within async session/connection
    if isinstance(session, (AsyncSession, AsyncConnection)):
        return await session.run_sync(
            paginate,  # type: ignore[ty:invalid-argument-type]
            query,
            params,
            count_query=count_query,
            subquery_count=subquery_count,
            bind_params=bind_params,
            execute_options=execute_options,
            transformer=_to_sync(transformer),
            additional_data=_to_sync(additional_data),
            unique=unique,
            config=config,
        )

    prepared_query = _prepare_query(query)
    prepared_count_query = _prepare_query(count_query) if count_query is not None else None

    return await _apaginate(
        session,
        prepared_query,
        params,
        count_query=prepared_count_query,
        subquery_count=subquery_count,
        bind_params=bind_params,
        execute_options=execute_options,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
        config=config,
    )
