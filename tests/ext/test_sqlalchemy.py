from typing import Iterator, Type

from fastapi import Depends, FastAPI
from pytest import fixture, skip
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from ..base import BasePaginationTestCase
from .utils import is_sqlalchemy20, sqlalchemy20


@fixture(
    scope="session",
    params=[True, False],
    ids=["subquery_count", "no_subquery_count"],
)
def use_subquery_count(request):
    if request.param and not is_sqlalchemy20:
        skip("subquery_count is not supported for SQLAlchemy<2.0")

    return request.param


@fixture(scope="session")
def app(sa_user, sa_session: Type[Session], model_cls: Type[object], use_subquery_count: bool):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        db = sa_session()
        try:
            yield db
        finally:
            db.close()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user), subquery_count=use_subquery_count)

    return add_pagination(app)


@sqlalchemy20
class TestSQLAlchemy(BasePaginationTestCase):
    pass
