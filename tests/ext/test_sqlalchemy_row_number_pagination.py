from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase

try:
    from fastapi_pagination.ext.sqlalchemy_future import paginate
except ImportError:
    paginate = None


@fixture(scope="session")
def app(sa_user, sa_order, sa_session, model_cls):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with sa_session() as db:
            yield db

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user), query_type="row-number")

    return add_pagination(app)


class TestSQLAlchemyRowNumberPagination(BasePaginationTestCase):
    pass
