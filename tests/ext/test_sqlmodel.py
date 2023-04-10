from functools import partial

from fastapi import FastAPI
from pytest import fixture
from sqlalchemy.orm import selectinload

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase

try:
    from sqlmodel import Session, select

    from fastapi_pagination.ext.sqlmodel import paginate
except ImportError:
    Session = None
    select = None


@fixture(scope="session")
def session(sa_engine):
    return partial(Session, sa_engine)


@fixture(scope="session")
def app():
    return FastAPI()


class TestSQLModelDefault(BasePaginationTestCase):
    @fixture(
        scope="session",
        params=[True, False],
        ids=["model", "query"],
    )
    def query(self, request, sm_user):
        if request.param:
            return sm_user

        return select(sm_user)

    @fixture(scope="session")
    def app(self, app, query, session, model_cls):
        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        def route():
            with session() as db:
                return paginate(db, query)

        return add_pagination(app)


class TestSQLModelRelationship(BasePaginationTestCase):
    pagination_types = ["relationship"]

    @fixture(scope="session")
    def app(self, app, session, sm_user, model_with_rel_cls):
        @app.get("/relationship/default", response_model=Page[model_with_rel_cls])
        @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_with_rel_cls])
        def route():
            with session() as db:
                return paginate(db, select(sm_user).options(selectinload(sm_user.orders)))

        return add_pagination(app)
