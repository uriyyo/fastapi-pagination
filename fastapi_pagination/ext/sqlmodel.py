__all__ = ["paginate"]

from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from .sqlalchemy_future import exec_pagination
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
def paginate(
    session: Session,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
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
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    pass


@no_type_check
def paginate(
    session: Session,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    unique: bool = True,
) -> Any:
    params, _ = verify_params(params, "limit-offset", "cursor")

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return exec_pagination(query, params, session.exec, additional_data, unique)
