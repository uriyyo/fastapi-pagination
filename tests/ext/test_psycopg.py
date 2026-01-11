from contextlib import asynccontextmanager

import pytest
from psycopg import AsyncConnection, Connection
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier

from fastapi_pagination.ext.psycopg import apaginate, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async


@pytest.fixture(scope="session")
def db_type():
    return "postgres"


@pytest.fixture(scope="session")
def database_url(postgres_url):
    return postgres_url


@async_sync_testsuite
class TestPsycopg(BasePaginationTestSuite):
    @pytest.fixture(scope="session", params=["raw", "sql-stmt"])
    def query_factory(self, request):
        def _factory():
            if request.param == "raw":
                return "SELECT id, name FROM users"

            return SQL("SELECT id, name FROM {}").format(Identifier("users"))

        return _factory

    @pytest.fixture(scope="session", params=["connection", "cursor"])
    def conn_ctx(self, database_url, is_async_db, request):
        use_cursor = request.param == "cursor"

        @asynccontextmanager
        async def async_conn_ctx():
            if is_async_db:
                async with await AsyncConnection.connect(database_url, row_factory=dict_row) as conn:
                    if use_cursor:
                        async with conn.cursor() as cursor:
                            yield cursor
                    else:
                        yield conn
            else:
                with Connection.connect(database_url, row_factory=dict_row) as conn:
                    if use_cursor:
                        with conn.cursor() as cursor:
                            yield cursor
                    else:
                        yield conn

        return async_conn_ctx

    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        return apaginate if is_async_db else paginate

    @pytest.fixture(scope="session")
    def app(self, builder, conn_ctx, paginate_func, query_factory):
        builder = builder.new()

        @builder.both.default
        async def route():
            async with conn_ctx() as conn:
                return await maybe_async(paginate_func(conn, query_factory()))

        return builder.build()
