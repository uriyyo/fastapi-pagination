from typing import Any, Optional, Type, TypeVar, no_type_check, overload

from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams
from ..types import PaginationQueryType
from .sqlalchemy import count_query, paginate_query

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
    params = resolve_params(params)

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    total = session.scalar(count_query(query))
    items = session.exec(paginate_query(query, params, query_type))

    return create_page(items.unique().all(), total, params)


__all__ = [
    "paginate",
]
