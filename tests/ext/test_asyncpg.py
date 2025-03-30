import pytest
from asyncpg import create_pool

from fastapi_pagination.ext.asyncpg import apaginate
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def db_type():
    return "postgres"


@pytest.fixture(scope="session")
def database_url(postgres_url):
    return postgres_url


@pytest.fixture(scope="session")
def pool(database_url):
    return create_pool(database_url)


class TestAsyncpg(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, pool, builder):
        @builder.lifespan
        async def lifespan():
            async with pool:
                yield

        @builder.both.default
        async def route():
            async with pool.acquire() as conn:
                return await apaginate(conn, "SELECT id, name FROM users")

        return builder.build()
