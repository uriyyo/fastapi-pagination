from . import patch  # noqa: F401  # isort: skip  # DO NOT REMOVE THIS LINE.
from asyncio import new_event_loop
from itertools import count
from pathlib import Path
from random import randint
from typing import Any

import aiosqlite
import asyncpg
import pytest
from asgi_lifespan import LifespanManager
from cassandra.cluster import Cluster
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pytest_asyncio import fixture as async_fixture
from typing_extensions import TypeAlias

from .schemas import UserWithOrderOut
from .utils import faker

RawData: TypeAlias = list[dict[str, Any]]


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
    parser.addoption(
        "--cassandra-dsn",
        type=str,
        required=True,
    )


@pytest.fixture(scope="session")
def _mongodb_url(request) -> str:
    return request.config.getoption("--mongodb-dsn")


@pytest.fixture(scope="session")
def mongodb_url(_mongodb_url, request) -> str:
    request.getfixturevalue("_setup_mongodb")
    return _mongodb_url


@pytest.fixture(scope="session")
def _postgres_url(request) -> str:
    return request.config.getoption("--postgres-dsn")


@pytest.fixture(scope="session")
def postgres_url(_postgres_url, request) -> str:
    request.getfixturevalue("_setup_postgres")
    return _postgres_url


@pytest.fixture(scope="session")
def _cassandra_address(request) -> str:
    return request.config.getoption("--cassandra-dsn")


@pytest.fixture(scope="session")
def cassandra_address(_cassandra_address, request) -> str:
    request.getfixturevalue("_setup_cassandra")
    return _cassandra_address


@pytest.fixture(scope="session")
def _sqlite_file() -> str:
    return str(Path("./test_db.sqlite").resolve().absolute())


@pytest.fixture(scope="session")
def sqlite_file(_sqlite_file, request) -> str:
    request.getfixturevalue("_setup_sqlite")
    return _sqlite_file


@pytest.fixture(scope="session")
def sqlite_url(sqlite_file) -> str:
    return f"sqlite:///{sqlite_file}"


@pytest.fixture(scope="session")
def raw_data() -> RawData:
    user_ids = count(1)
    order_ids = count(1)

    def generate_one() -> dict[str, Any]:
        """Generate a single user with unique user id"""
        id_ = next(user_ids)

        return {
            "id": id_,
            "name": faker.unique.name(),
            "orders": [
                {
                    "id": next(order_ids),
                    "user_id": id_,
                    "name": faker.unique.name(),
                }
                for _ in range(randint(1, 10))  # noqa: S311
            ],
        }

    return [generate_one() for _ in range(100)]


@pytest.fixture(scope="session")
def entities(raw_data: RawData) -> list[UserWithOrderOut]:
    return [UserWithOrderOut(**data) for data in raw_data]


@pytest.fixture(scope="session")
def cassandra_session(_cassandra_address: str):
    with Cluster([_cassandra_address]).connect() as session:
        ddl = "DROP KEYSPACE IF EXISTS  ks"
        session.execute(ddl)

        ddl = (
            "CREATE KEYSPACE IF NOT EXISTS ks WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}"
        )
        session.execute(ddl)

        yield session


@async_fixture(scope="session", autouse=True)
async def _setup_postgres(_postgres_url: str, raw_data: RawData):
    async with asyncpg.create_pool(_postgres_url) as pool:
        await pool.fetch("DROP TABLE IF EXISTS users CASCADE;")
        await pool.fetch("DROP TABLE IF EXISTS orders CASCADE;")
        await pool.fetch(
            """
        CREATE TABLE IF NOT EXISTS "users" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" TEXT NOT NULL
        );
        """,
        )
        await pool.fetch(
            """
        CREATE TABLE IF NOT EXISTS "orders" (
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" TEXT NOT NULL,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
        );
        """,
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
async def _setup_sqlite(_sqlite_file: str, raw_data: RawData):
    async with aiosqlite.connect(_sqlite_file) as pool:
        await pool.execute("DROP TABLE IF EXISTS orders;")
        await pool.execute("DROP TABLE IF EXISTS users;")
        await pool.execute(
            """
        CREATE TABLE IF NOT EXISTS "users" (
            "id" INTEGER PRIMARY KEY NOT NULL,
            "name" TEXT NOT NULL
        );
        """,
        )
        await pool.execute(
            """
        CREATE TABLE IF NOT EXISTS "orders" (
            "id" INTEGER PRIMARY KEY NOT NULL,
            "name" TEXT NOT NULL,
            "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
        );
        """,
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
async def _setup_mongodb(_mongodb_url: str, raw_data: RawData):
    motor = AsyncIOMotorClient(_mongodb_url)

    await motor.test.users.delete_many({})
    await motor.test.users.insert_many(raw_data)

    motor.close()


@pytest.fixture(scope="session")
def is_async_db() -> bool:
    return False


@pytest.fixture(
    scope="session",
    params=["postgres", "sqlite"],
)
def db_type(request) -> str:
    return request.param


@pytest.fixture(scope="session")
def database_url(db_type: str, is_async_db: bool, request) -> str:
    if db_type == "postgres":  # noqa: SIM108
        url = request.getfixturevalue("postgres_url")
    elif db_type == "sqlite":
        url = request.getfixturevalue("sqlite_url")
    else:
        raise ValueError(f"Unknown database type: {db_type}")

    if is_async_db:
        url = url.replace("postgresql", "postgresql+asyncpg", 1)
        url = url.replace("sqlite", "sqlite+aiosqlite", 1)

    return url


@pytest.fixture(scope="session")
def event_loop():
    return new_event_loop()


def pytest_collection_modifyitems(items: list[pytest.Function]):
    items.sort(key=lambda it: (it.path, it.nodeid))


@async_fixture(scope="class")
async def client(app: FastAPI):
    async with (
        LifespanManager(app),
        AsyncClient(
            transport=ASGITransport(app),
            base_url="http://testserver",
            timeout=60,
        ) as c,
    ):
        yield c
