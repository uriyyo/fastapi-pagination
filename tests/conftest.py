from asyncio import new_event_loop

from asyncpg import create_pool
from pytest import fixture


def pytest_addoption(parser):
    parser.addoption(
        "--postgres-dsn",
        type=str,
        required=True,
    )
    parser.addoption(
        "--mongodb-dsn",
        type=str,
        required=True,
    )


@fixture(scope="session")
def postgres_url(request) -> str:
    return request.config.getoption("--postgres-dsn")


@fixture(scope="session", autouse=True)
async def _setup_postgres(postgres_url):
    async with create_pool(postgres_url) as pool:
        await pool.fetch("DROP TABLE IF EXISTS users CASCADE;")
        await pool.fetch("DROP TABLE IF EXISTS orders CASCADE;")
        await pool.fetch(
            """
        CREATE TABLE IF NOT EXISTS "users" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" TEXT NOT NULL
        );
        """
        )
        await pool.fetch(
            """
        CREATE TABLE IF NOT EXISTS "orders" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" TEXT NOT NULL,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
        );
        """
        )


@fixture(scope="class")
async def _clear_database(database_url, postgres_url):
    if not database_url.startswith("postgres"):
        return

    async with create_pool(postgres_url) as pool:
        await pool.fetch("TRUNCATE TABLE users CASCADE;")


@fixture(scope="session")
def mongodb_url(request) -> str:
    return request.config.getoption("--mongodb-dsn")


@fixture(scope="session")
def sqlite_url() -> str:
    return "sqlite:///.db"


@fixture(
    scope="session",
    params=["postgres_url", "sqlite_url"],
)
def database_url(request) -> str:
    return request.getfixturevalue(request.param)


@fixture(scope="session")
def event_loop():
    return new_event_loop()
