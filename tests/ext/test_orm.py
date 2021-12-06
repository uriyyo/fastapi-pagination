import sqlalchemy
from databases import Database
from fastapi import FastAPI
from orm import Integer, Model, String
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.orm import paginate

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker


@fixture(scope="session")
def db(database_url):
    return Database(database_url)


@fixture(scope="session")
def metadata(database_url):
    return sqlalchemy.MetaData()


@fixture(scope="session")
def User(metadata, db):
    class User(Model):
        __tablename__ = "users"
        __database__ = db
        __metadata__ = metadata

        id = Integer(primary_key=True)
        name = String(max_length=100)

    return User


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
        return await paginate(User.objects)

    add_pagination(app)
    return app


class TestORM(BasePaginationTestCase):
    @fixture(scope="class")
    async def entities(self, User):
        for _ in range(100):
            await User.objects.create(name=faker.name())

        return await User.objects.all()
