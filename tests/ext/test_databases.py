import sqlalchemy
from databases import Database
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.databases import paginate

from ..base import BasePaginationTestCase
from ..utils import faker

metadata = sqlalchemy.MetaData()
User = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
)


@fixture(scope="session")
def db(database_url):
    return Database(database_url)


@fixture(scope="session")
def app(db, model_cls):
    app = FastAPI()

    app.add_event_handler("startup", db.connect)
    app.add_event_handler("shutdown", db.disconnect)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db, User.select())

    return add_pagination(app)


class TestDatabases(BasePaginationTestCase):
    @fixture(scope="class")
    async def entities(self, db):
        await db.execute_many(User.insert(), [{"name": faker.name()} for _ in range(100)])

        return [{**user} async for user in db.iterate(User.select())]
