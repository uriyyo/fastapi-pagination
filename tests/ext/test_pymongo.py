import pytest
from pymongo import AsyncMongoClient, MongoClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.pymongo import apaginate, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async

from .utils import mongodb_test


@pytest.fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@mongodb_test
@async_sync_testsuite
class TestPymongo(BasePaginationTestSuite):
    @async_fixture(scope="session")
    async def db_client(self, database_url, is_async_db):
        if is_async_db:
            async with AsyncMongoClient(database_url) as client:
                yield client
        else:
            with MongoClient(database_url) as client:
                yield client

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
