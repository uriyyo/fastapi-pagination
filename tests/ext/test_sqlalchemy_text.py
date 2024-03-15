from typing import Iterator, Type

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def app(sa_user, sa_session: Type[Session], model_cls: Type[object]):
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
        return paginate(db, text("users"))

    return add_pagination(app)


class TestSQLAlchemyRaw(BasePaginationTestCase):
    pagination_types = ["default", "optional"]
