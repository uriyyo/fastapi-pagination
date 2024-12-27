import pytest
from bunnet import Document, init_bunnet
from pymongo import MongoClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.bunnet import paginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def be_user():
    class User(Document):
        name: str

        class Settings:
            name = "users"

    return User


@async_fixture(scope="session")
def db_client(database_url, be_user):
    client = MongoClient(database_url)
    init_bunnet(database=client.test, document_models=[be_user])
    yield
    client.close()


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, be_user):
    if request.param:
        return be_user

    return be_user.find()


@mongodb_test
class TestBunnet(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, query, db_client):
        @builder.both.default
        def route():
            return paginate(query)

        return builder.build()
