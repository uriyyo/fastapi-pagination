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
    @pytest.fixture(scope="session", params=["args", "kwargs"])
    def query_params(self, request):
        if request.param == "args":
            return (1,)

        return {"arg": 1}

    @pytest.fixture(scope="session", params=["raw", "sql-stmt"])
    def query_factory(self, request, query_params):
        def _factory():
            arg_format = "%s" if isinstance(query_params, tuple) else "%(arg)s"

            if request.param == "raw":
                return f"SELECT id, name FROM users WHERE 1 = {arg_format}"  # noqa: S608

            return SQL(f"SELECT id, name FROM {{}} WHERE 1 = {arg_format}").format(Identifier("users"))  # type: ignore[arg-type]  # noqa: S608

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
    def app(self, builder, conn_ctx, paginate_func, query_factory, query_params):
        builder = builder.new()

        @builder.both.default
        async def route():
            async with conn_ctx() as conn:
                return await maybe_async(paginate_func(conn, query_factory(), query_params=query_params))

        return builder.build()
