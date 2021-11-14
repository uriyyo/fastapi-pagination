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

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.piccolo import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker

_counter = count().__next__

os.environ["PICCOLO_CONF"] = __name__


class _User(Table):
    id = Integer(default=_counter, primary_key=True)
    name = Text(required=False, null=True)


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return _User
    else:
        return _User.select()


DB = SQLiteEngine()
APP_REGISTRY = AppRegistry()

APP_CONFIG = AppConfig(
    app_name="example",
    migrations_folder_path=None,
    table_classes=[_User],
)


@fixture(scope="session")
def database_url():
    return "piccolo.sqlite"


@fixture(scope="session")
async def _engine(database_url):
    engine: SQLiteEngine = cast(SQLiteEngine, engine_finder())

    p = Path(engine.path)
    if p.exists():
        os.remove(p)

    await engine.prep_database()
    await _User.create_table().run()


@fixture(scope="session")
def app(query, _engine):
    app = FastAPI()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(query)

    add_pagination(app)
    return app


class TestPiccolo(BasePaginationTestCase):
    @fixture(scope="session")
    async def entities(self, query, client):
        await _User.delete(force=True)
        for _ in range(100):
            await _User(name=faker.name()).save()

        return await _User.select()
