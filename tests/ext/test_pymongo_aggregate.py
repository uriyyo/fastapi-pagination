import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.motor import apaginate_aggregate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@mongodb_test
class TestMotorAggregate(BasePaginationTestSuite):
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

    @pytest.fixture(scope="session")
    def app(self, builder, db_client):
        @builder.both.default
        async def route():
            return await apaginate_aggregate(
                db_client.test_agg.users,
                [
                    {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                    {"$sort": {"name": 1}},
                ],
            )

        return builder.build()
