import sqlalchemy
from databases import Database
from fastapi import FastAPI
from orm import Integer, Model, String
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.orm import paginate

from ..base import BasePaginationTestCase


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
def app(db, metadata, User, model_cls):
    app = FastAPI()

    app.add_event_handler("startup", db.connect)
    app.add_event_handler("shutdown", db.disconnect)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(User.objects)

    return add_pagination(app)


class TestORM(BasePaginationTestCase):
    pass
