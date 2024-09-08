from typing import Iterator, Type

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import select, text
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from ..base import BasePaginationTestCase
from ..utils import OptionalLimitOffsetPage, OptionalPage


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
    @app.get("/optional/default", response_model=OptionalPage[model_cls])
    @app.get("/optional/limit-offset", response_model=OptionalLimitOffsetPage[model_cls])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).from_statement(text("SELECT * FROM users")))

    return add_pagination(app)


class TestSQLAlchemyFromStatement(BasePaginationTestCase):
    pagination_types = ["default", "optional"]
