from fastapi import FastAPI
from pymongo import MongoClient
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    return MongoClient(database_url)


@fixture(scope="session")
def app(db_client):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        for _ in range(100):
            db_client.test.users.insert_one({"name": faker.name()})

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        db_client.close()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return paginate(db_client.test.users)

    return add_pagination(app)


class TestPymongo(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, db_client):
        cursor = db_client.test.users.find()
        return list(cursor)
