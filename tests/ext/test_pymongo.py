import pytest
from pymongo import AsyncMongoClient, MongoClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.pymongo import apaginate, apaginate_aggregate, paginate, paginate_aggregate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async

from .utils import mongodb_test


@pytest.fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@async_sync_testsuite
class _BasePymongoSuite:
    @async_fixture(scope="session")
    async def db_client(self, database_url, is_async_db):
        if is_async_db:
            async with AsyncMongoClient(database_url) as client:
                yield client
        else:
            with MongoClient(database_url) as client:
                yield client


@mongodb_test
class TestPymongo(_BasePymongoSuite, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate if is_async_db else paginate

    @pytest.fixture(scope="session")
    def app(self, builder, db_client, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await maybe_async(paginate_func(db_client.test.users))

        return builder.build()


@mongodb_test
class TestPymongoAggregate(_BasePymongoSuite, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate_aggregate if is_async_db else paginate_aggregate

    @async_fixture(scope="session")
    async def entities(self, db_client):
        cursor = await maybe_async(
            db_client.test_agg.users.aggregate(
                [
                    {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                    {"$sort": {"name": 1}},
                ],
            )
        )
        return await maybe_async(cursor.to_list(length=None))

    @pytest.fixture(scope="session")
    def app(self, builder, db_client, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route():
            return await maybe_async(
                paginate_func(
                    db_client.test_agg.users,
                    [
                        {"$group": {"_id": "$name", "name": {"$first": "$name"}}},
                        {"$sort": {"name": 1}},
                    ],
                )
            )

        return builder.build()
