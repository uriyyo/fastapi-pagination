import databases
import sqlalchemy
from fastapi import FastAPI
from ormar import Integer, Model, String
from pytest import fixture, mark

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.ormar import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def db(database_url):
    return databases.Database(database_url)


@fixture(scope="session")
def meta(database_url):
    return sqlalchemy.MetaData()


@fixture(scope="session")
def User(meta, db):
    class User(Model):
        ormar_config = {
            "metadata": meta,
            "database": db,
        }

        id = Integer(primary_key=True)
        name = String(max_length=100)

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User

    return User.objects


@fixture(scope="session")
def app(db, meta, User, query, model_cls):
    app = FastAPI()

    app.add_event_handler("startup", db.connect)
    app.add_event_handler("shutdown", db.disconnect)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(query)

    return add_pagination(app)


@mark.ormar
class TestOrmar(BasePaginationTestCase):
    pass
