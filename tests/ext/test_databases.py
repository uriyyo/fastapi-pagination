from databases import Database
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.databases import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def db(database_url):
    return Database(database_url)


@fixture(scope="session")
def app(db, sa_user, model_cls):
    app = FastAPI()

    app.add_event_handler("startup", db.connect)
    app.add_event_handler("shutdown", db.disconnect)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db, sa_user.__table__.select())

    return add_pagination(app)


class TestDatabases(BasePaginationTestCase):
    pass
