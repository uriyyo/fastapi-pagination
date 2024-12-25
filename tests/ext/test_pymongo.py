import pytest
from pymongo import MongoClient

from fastapi_pagination.ext.pymongo import paginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@pytest.fixture(scope="session")
def db_client(database_url):
    with MongoClient(database_url) as client:
        yield client


@mongodb_test
class TestPymongo(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db_client):
        @builder.both.default
        async def route():
            return paginate(db_client.test.users)

        return builder.build()
