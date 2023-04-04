from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase
from .utils import sqlalchemy20

try:
    from fastapi_pagination.ext.sqlalchemy_future import paginate
except ImportError:
    paginate = None


@fixture(scope="session")
def app(sa_user, sa_order, sa_session, model_cls, model_with_rel_cls):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with sa_session() as db:
            yield db

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route_1(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user))

    @app.get("/relationship/default", response_model=Page[model_with_rel_cls])
    @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_with_rel_cls])
    def route_2(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).options(selectinload(sa_user.orders)))

    @app.get("/non-scalar/default", response_model=Page[model_cls])
    @app.get("/non-scalar/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route_3(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user.id, sa_user.name))

    return add_pagination(app)


@sqlalchemy20
class TestSQLAlchemyFuture(BasePaginationTestCase):
    pagination_types = ["default", "non-scalar", "relationship"]
