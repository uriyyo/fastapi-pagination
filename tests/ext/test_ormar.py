import databases
import sqlalchemy
from fastapi import FastAPI
from ormar import Integer, Model, OrmarConfig, String
from pytest import fixture, mark
from sqlalchemy.engine.create import create_engine

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.ormar import paginate
from tests.base import BasePaginationTestCase


@fixture(scope="session")
def db(database_url):
    return databases.Database(database_url)


@fixture(scope="session")
def meta(database_url):
    return sqlalchemy.MetaData()


@fixture(scope="session")
def engine(database_url):
    return create_engine(database_url)


@fixture(scope="session")
def user_cls(meta, db, engine):
    class User(Model):
        ormar_config = OrmarConfig(
            metadata=meta,
            database=db,
            engine=engine,
        )

        id: int = Integer(primary_key=True)
        name: str = String(max_length=100)

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, user_cls):
    if request.param:
        return user_cls

    return user_cls.objects


@fixture(scope="session")
def app(db, meta, user_cls, query, model_cls):
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
