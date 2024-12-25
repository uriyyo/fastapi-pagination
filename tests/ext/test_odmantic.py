import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine, Model, SyncEngine
from pymongo import MongoClient

from fastapi_pagination.ext.odmantic import paginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_model():
    class User(Model):
        name: str

        model_config = {
            "collection": "users",
        }

    return User


@pytest.mark.odmantic
@mongodb_test
class TestOdmanticAsync(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def db_client(self, database_url):
        client = AsyncIOMotorClient(database_url)
        yield client
        client.close()

    @pytest.fixture(scope="session")
    def db_engine(self, db_client):
        return AIOEngine(db_client, database="test")

    @pytest.fixture(scope="session")
    def app(self, builder, db_engine, db_model):
        @builder.both.default
        async def route():
            return await paginate(db_engine, db_model)

        return builder.build()


@pytest.mark.odmantic
@mongodb_test
class TestOdmanticSync(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def db_client(self, database_url):
        client = MongoClient(database_url)
        yield client
        client.close()

    @pytest.fixture(scope="session")
    def db_engine(self, db_client):
        return SyncEngine(db_client, database="test")

    @pytest.fixture(scope="session")
    def app(self, builder, db_engine, db_model):
        @builder.both.default
        async def route():
            return paginate(db_engine, db_model)

        return builder.build()
