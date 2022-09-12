from . import patch  # noqa  # isort: skip  # DO NOT REMOVE THIS LINE.
from asyncio import new_event_loop
from itertools import count
from pathlib import Path
from random import randint

import aiosqlite
import asyncpg
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from .schemas import UserWithOrderOut
from .utils import faker


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
def raw_data():
    user_ids = count(1)
    order_ids = count(1)

    def generate_one():
        id_ = next(user_ids)

        return {
            "id": id_,
            "name": faker.name(),
            "orders": [
                {
                    "id": next(order_ids),
                    "user_id": id_,
                    "name": faker.name(),
                }
                for _ in range(randint(1, 10))
            ],
        }

    return [generate_one() for _ in range(100)]


@fixture(scope="session")
def entities(raw_data):
    return [UserWithOrderOut(**data) for data in raw_data]


@async_fixture(scope="session", autouse=True)
async def _setup_postgres(postgres_url, raw_data):
    async with asyncpg.create_pool(postgres_url) as pool:
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

        await pool.executemany(
            """
            INSERT INTO "users" (id, name) VALUES ($1, $2)
            """,
            [(user["id"], user["name"]) for user in raw_data],
        )
        await pool.executemany(
            """
            INSERT INTO "orders" (id, user_id, name) VALUES ($1, $2, $3)
            """,
            [(order["id"], order["user_id"], order["name"]) for user in raw_data for order in user["orders"]],
        )

        await pool.fetch("COMMIT")


@async_fixture(scope="session", autouse=True)
async def _setup_sqlite(sqlite_file, raw_data):
    async with aiosqlite.connect(sqlite_file) as pool:
        await pool.execute("DROP TABLE IF EXISTS orders;")
        await pool.execute("DROP TABLE IF EXISTS users;")
        await pool.execute(
            """
        CREATE TABLE IF NOT EXISTS "users" (
            "id" INTEGER PRIMARY KEY NOT NULL,
            "name" TEXT NOT NULL
        );
        """
        )
        await pool.execute(
            """
        CREATE TABLE IF NOT EXISTS "orders" (
            "id" INTEGER PRIMARY KEY NOT NULL,
            "name" TEXT NOT NULL,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
        );
        """
        )

        await pool.executemany(
            """
            INSERT INTO "users" (id, name) VALUES (?, ?)
            """,
            [(user["id"], user["name"]) for user in raw_data],
        )
        await pool.executemany(
            """
            INSERT INTO "orders" (id, user_id, name) VALUES (?, ?, ?)
            """,
            [(order["id"], order["user_id"], order["name"]) for user in raw_data for order in user["orders"]],
        )

        await pool.commit()


@async_fixture(scope="session", autouse=True)
async def _setup_mongodb(mongodb_url, raw_data):
    client = AsyncIOMotorClient(mongodb_url)

    await client.test.users.delete_many({})
    await client.test.users.insert_many(raw_data)

    client.close()


@fixture(scope="session")
def mongodb_url(request) -> str:
    return request.config.getoption("--mongodb-dsn")


@fixture(scope="session")
def postgres_url(request) -> str:
    return request.config.getoption("--postgres-dsn")


@fixture(scope="session")
def sqlite_file() -> str:
    return str(Path("./test_db.sqlite").resolve().absolute())


@fixture(scope="session")
def sqlite_url(sqlite_file) -> str:
    return f"sqlite:///{sqlite_file}"


@fixture(scope="session")
def is_async_db() -> bool:
    return False


@fixture(
    scope="session",
    params=["postgres", "sqlite"],
)
def db_type(request) -> str:
    return request.param


@fixture(scope="session")
def database_url(db_type, postgres_url, sqlite_url, is_async_db) -> str:
    if db_type == "postgres":
        url = postgres_url
    else:
        url = sqlite_url

    if is_async_db:
        url = url.replace("postgresql", "postgresql+asyncpg", 1)
        url = url.replace("sqlite", "sqlite+aiosqlite", 1)

    return url


@fixture(scope="session")
def event_loop():
    return new_event_loop()


def pytest_collection_modifyitems(items):
    items.sort(key=lambda it: (it.path, it.name))


@async_fixture(scope="class")
async def client(app):
    async with LifespanManager(app), AsyncClient(app=app, base_url="http://testserver") as c:
        yield c
