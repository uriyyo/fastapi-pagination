from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from ..base import BasePaginationTestCase
from .utils import sqlalchemy20


@fixture(scope="session")
def app(sa_user, sa_session, model_cls):
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
        return paginate(db.query(sa_user))

    return add_pagination(app)


@sqlalchemy20
class TestSQLAlchemy(BasePaginationTestCase):
    pass
