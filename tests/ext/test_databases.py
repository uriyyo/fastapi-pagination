import sqlalchemy
from databases import Database
from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.databases import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker


@fixture(scope="session")
def metadata(database_url):
    return sqlalchemy.MetaData()


@fixture(scope="session")
def db(database_url):
    return Database(database_url)


@fixture(scope="session")
def User(metadata):
    return sqlalchemy.Table(
        "users",
        metadata,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
        sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    )


@fixture(scope="session")
def app(db, metadata, User):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        await db.connect()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await db.disconnect()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(db, User.select())

    add_pagination(app)
    return app


class TestDatabases(BasePaginationTestCase):
    @fixture(scope="class")
    async def entities(self, db, User):
        await db.execute_many(User.insert(), [{"name": faker.name()} for _ in range(100)])
        return [{**user} async for user in db.iterate(User.select())]
