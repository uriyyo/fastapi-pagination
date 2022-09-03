from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate_aggregate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase


class Model(BaseModel):
    name: str


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@fixture(scope="session")
def app(db_client, model_cls, raw_data):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        await db_client.test_agg.users.delete_many({})
        await db_client.test_agg.users.insert_many(raw_data)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate_aggregate(
            db_client.test_agg.users,
            [
                {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                {"$sort": {"name": 1}},
            ],
        )

    return add_pagination(app)


class TestMotorAggregate(BasePaginationTestCase):
    @fixture(scope="session")
    def model_cls(self):
        return Model

    @async_fixture(scope="session")
    async def entities(self, db_client):
        cursor = db_client.test_agg.users.aggregate(
            [
                {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                {"$sort": {"name": 1}},
            ]
        )
        return await cursor.to_list(length=None)
