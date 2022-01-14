from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate_aggregate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, SafeTestClient, UserOut
from ..utils import faker


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
        for _ in range(100):
            await db_client.test.users.insert_one({"name": faker.name()})

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        db_client.close()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate_aggregate(
            db_client.test.users, [{"$group": {"_id": "$name", "name": {"$first": "$name"}}}, {"$sort": {"name": 1}}]
        )

    add_pagination(app)
    return app


class TestMotorAggregate(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, db_client):
        cursor = db_client.test.users.aggregate(
            [{"$group": {"_id": "$name", "name": {"$first": "$name"}}}, {"$sort": {"name": 1}}]
        )
        items = await cursor.to_list(length=None)
        return items
