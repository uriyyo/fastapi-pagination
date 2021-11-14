from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, UserOut


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    return AsyncIOMotorClient(database_url)


@fixture(scope="session")
def app(db_client):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        await db_client.test.users.delete_many({})
        db_client.drop_database("test")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        db_client.close()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(db_client.test.users)

    add_pagination(app)
    return app


class TestMotor(BasePaginationTestCase):
    @fixture(scope="session")
    async def entities(self, db_client):
        cursor = db_client.test.users.find()
        return await cursor.to_list(length=None)
