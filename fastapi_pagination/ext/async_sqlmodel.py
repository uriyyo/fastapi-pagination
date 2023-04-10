__all__ = ["paginate"]

import warnings
from typing import Any, Optional, Type, TypeVar, overload

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractParams
from ..types import AdditionalData, AsyncItemsTransformer
from .sqlmodel import paginate as _paginate

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
async def paginate(
    session: AsyncSession,
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
    session: AsyncSession,
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
    session: AsyncSession,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    pass


async def paginate(
    session: AsyncSession,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    transformer: Optional[AsyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    warnings.warn(
        "fastapi_pagination.ext.async_sqlmodel module is deprecated, "
        "please use fastapi_pagination.ext.sqlmodel module instead"
        "This module will be removed in the next major release (0.13.0).",
        DeprecationWarning,
        stacklevel=2,
    )

    return await _paginate(
        session,
        query,
        params,
        transformer=transformer,
        additional_data=additional_data,
        unique=unique,
    )
