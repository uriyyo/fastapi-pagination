from asyncpg import create_pool
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.asyncpg import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, SafeTestClient, UserOut


@fixture(scope="session")
def database_url(postgres_url) -> str:
    return postgres_url


@fixture(scope="session")
def pool(database_url):
    return create_pool(database_url)


@fixture(scope="session")
def app(pool):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        await pool
        await pool.acquire()

        async with pool.acquire() as conn:
            await conn.fetch("DROP TABLE IF EXISTS users CASCADE;")
            await conn.fetch("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL);")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await pool.terminate()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        async with pool.acquire() as conn:
            return await paginate(conn, "SELECT id, name FROM users")

    add_pagination(app)
    return app


class TestAsyncpg(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, pool):
        async with pool.acquire() as conn:
            return [{**user} for user in await conn.fetch("SELECT id, name FROM users;")]
