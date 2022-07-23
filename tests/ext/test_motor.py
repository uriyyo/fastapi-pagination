from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    return AsyncIOMotorClient(database_url)


@fixture(scope="session")
def app(db_client, model_cls):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        await db_client.test.users.delete_many({})
        await db_client.drop_database("test")

    @app.on_event("shutdown")
    def on_shutdown() -> None:
        db_client.close()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db_client.test.users)

    return add_pagination(app)


class TestMotor(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, db_client):
        cursor = db_client.test.users.find()

        return await cursor.to_list(length=None)
