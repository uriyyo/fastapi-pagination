import os
from itertools import count
from pathlib import Path
from typing import cast

import pytest
from piccolo.columns import Integer, Text
from piccolo.conf.apps import AppConfig, AppRegistry
from piccolo.engine import SQLiteEngine, engine_finder
from piccolo.table import Table
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.piccolo import apaginate
from tests.base import BasePaginationTestSuite
from tests.utils import faker

_counter = count().__next__

os.environ["PICCOLO_CONF"] = __name__


class User(Table, tablename="users"):
    id = Integer(default=_counter, primary_key=True)
    name = Text(required=False, null=True)


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return User

    return User.select().order_by(User.id)


DB = SQLiteEngine()
APP_REGISTRY = AppRegistry()

APP_CONFIG = AppConfig(
    app_name="example",
    migrations_folder_path=None,
    table_classes=[User],
)


@pytest.fixture(scope="session")
def database_url():
    return "piccolo.sqlite"


@async_fixture(scope="session")
async def engine(database_url):
    engine: SQLiteEngine = cast(SQLiteEngine, engine_finder())

    p = Path(engine.path)
    if p.exists():
        p.unlink()

    await engine.prep_database()
    await User.create_table().run()


class TestPiccolo(BasePaginationTestSuite):
    @async_fixture(scope="class")
    async def entities(self, query, client):
        await User.insert(*(User(name=faker.name()) for _ in range(100))).run()

        return await User.select()

    @pytest.fixture(scope="session")
    def app(self, builder, query, engine):
        @builder.both.default
        async def route():
            return await apaginate(query)

        return builder.build()
