from databases import Database, __version__
from fastapi import FastAPI
from orm import Integer, Model, ModelRegistry, String
from pytest import fixture, mark

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.orm import paginate

from ..base import BasePaginationTestCase

if tuple(map(int, __version__.split("."))) >= (0, 9, 0):
    raise ImportError("This test is only for databases<0.9.0")


@fixture(scope="session")
def db(database_url):
    return Database(database_url)


@fixture(scope="session")
def user(db):
    models = ModelRegistry(database=db)

    class User(Model):
        tablename = "users"
        registry = models
        fields = {
            "id": Integer(primary_key=True),
            "name": String(max_length=100),
        }

    return User


@fixture(scope="session")
def app(db, user, model_cls):
    app = FastAPI()

    app.add_event_handler("startup", db.connect)
    app.add_event_handler("shutdown", db.disconnect)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(user.objects)

    return add_pagination(app)


@mark.orm
class TestORM(BasePaginationTestCase):
    pass
