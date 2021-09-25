from typing import Optional, TypeVar, Union

from sqlmodel import Session, SQLModel, func, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from ..api import create_page, resolve_params
from ..bases import AbstractPage, AbstractParams

T = TypeVar("T", bound=SQLModel)


def paginate(
    session: Session,
    query: Union[T, Select[T], SelectOfScalar[T]],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if not isinstance(query, (Select, SelectOfScalar)):
        query = select(query)

    total = session.scalar(select(func.count("*")).select_from(query.subquery()))
    items = session.exec(query.limit(raw_params.limit).offset(raw_params.offset)).unique().all()

    return create_page(items, total, params)


__all__ = ["paginate"]
