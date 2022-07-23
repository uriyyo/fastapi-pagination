from contextlib import AsyncExitStack

from asyncpg import create_pool
from fastapi import FastAPI
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.asyncpg import paginate

from ..base import BasePaginationTestCase
from ..utils import faker


@fixture(scope="session")
def database_url(postgres_url) -> str:
    return postgres_url


@fixture(scope="session")
def pool(database_url):
    return create_pool(database_url)


@fixture(scope="session")
def app(pool, model_cls):
    app = FastAPI()
    stack = AsyncExitStack()

    @app.on_event("startup")
    async def on_startup() -> None:
        await stack.enter_async_context(pool)

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await stack.aclose()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        async with pool.acquire() as conn:
            return await paginate(conn, "SELECT id, name FROM users")

    return add_pagination(app)


class TestAsyncpg(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, pool):
        async with pool.acquire() as conn:
            await conn.executemany(f"INSERT INTO users(name) VALUES ($1);", [(faker.name(),) for _ in range(100)])

            return [{**user} for user in await conn.fetch("SELECT id, name FROM users;")]
