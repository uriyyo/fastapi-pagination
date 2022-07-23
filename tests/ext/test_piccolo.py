import os
from itertools import count
from pathlib import Path
from typing import cast

from fastapi import FastAPI
from piccolo.columns import Integer, Text
from piccolo.conf.apps import AppConfig, AppRegistry
from piccolo.engine import SQLiteEngine, engine_finder
from piccolo.table import Table
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.piccolo import paginate

from ..base import BasePaginationTestCase
from ..utils import faker

_counter = count().__next__

os.environ["PICCOLO_CONF"] = __name__


class User(Table, tablename="users"):
    id = Integer(default=_counter, primary_key=True)
    name = Text(required=False, null=True)


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return User
    else:
        return User.select()


DB = SQLiteEngine()
APP_REGISTRY = AppRegistry()

APP_CONFIG = AppConfig(
    app_name="example",
    migrations_folder_path=None,
    table_classes=[User],
)


@fixture(scope="session")
def database_url():
    return "piccolo.sqlite"


@async_fixture(scope="session")
async def engine(database_url):
    engine: SQLiteEngine = cast(SQLiteEngine, engine_finder())

    p = Path(engine.path)
    if p.exists():
        os.remove(p)

    await engine.prep_database()
    await User.create_table().run()


@fixture(scope="session")
def app(query, engine, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(query)

    return add_pagination(app)


class TestPiccolo(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, query, client):
        await User.insert(*(User(name=faker.name()) for _ in range(100))).run()

        return await User.select()
