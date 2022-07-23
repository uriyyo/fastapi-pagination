from fastapi import FastAPI
from gino_starlette import Gino
from orm import Integer, String
from pytest import fixture
from pytest_asyncio import fixture as async_fixture
from sqlalchemy import Column, Integer, String

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.gino import paginate

from ..base import BasePaginationTestCase
from ..utils import faker


@fixture(scope="session")
def database_url(postgres_url) -> str:
    return postgres_url


@fixture(scope="session")
def db(database_url):
    return Gino(dsn=database_url)


@fixture(scope="session")
def User(db):
    class User(db.Model):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User
    else:
        return User.query


@fixture(scope="session")
def app(db, User, query, model_cls):
    app = FastAPI()
    db.init_app(app)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(query)

    return add_pagination(app)


class TestGino(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, User, query):
        await User.insert().gino.all(*[{"name": faker.name()} for _ in range(100)])

        return await User.query.gino.all()
