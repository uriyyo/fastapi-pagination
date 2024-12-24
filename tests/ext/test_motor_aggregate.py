import pytest
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate_aggregate
from tests.base import BasePaginationTestCase

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def app(db_client, model_cls, raw_data):
    app = FastAPI()

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


@mongodb_test
class TestMotorAggregate(BasePaginationTestCase):
    @async_fixture(scope="session")
    async def entities(self, db_client, raw_data):
        await db_client.test_agg.users.delete_many({})
        await db_client.test_agg.users.insert_many(raw_data)

        cursor = db_client.test_agg.users.aggregate(
            [
                {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                {"$sort": {"name": 1}},
            ],
        )
        return await cursor.to_list(length=None)
