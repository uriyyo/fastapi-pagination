import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from fastapi_pagination.ext.motor import apaginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def entities(entities):
    return sorted(entities, key=lambda entity: entity.name)


@mongodb_test
class TestMotor(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, db_client):
        @builder.both.default
        async def route():
            return await apaginate(db_client.test.users, sort=[("name", 1)])

        return builder.build()
