from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..bases import AbstractPage, AbstractParams
from ..types import PaginationQueryType
from ..utils import verify_params
from .sqlalchemy_future import exec_pagination

T = TypeVar("T")
TSQLModel = TypeVar("TSQLModel", bound=SQLModel)


@overload
def paginate(
    session: Session,
    query: Select[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[TSQLModel]:
    pass


@overload
def paginate(
    session: Session,
    query: SelectOfScalar[T],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[T]:
    pass


@overload
def paginate(
    session: Session,
    query: Type[TSQLModel],
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[TSQLModel]:
    pass


@no_type_check
def paginate(
    session: Session,
    query: Any,
    params: Optional[AbstractParams] = None,
    *,
    query_type: PaginationQueryType = None,
) -> AbstractPage[Any]:
    params = verify_params(params, "limit-offset", "cursor")

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    return exec_pagination(query, params, session.exec, query_type, unwrap=False)


__all__ = [
    "paginate",
]
