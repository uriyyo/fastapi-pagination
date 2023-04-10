from fastapi import FastAPI
from pytest import fixture, mark
from sqlalchemy import Column, Integer, String

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase

pytestmark = mark.gino


@fixture(scope="session")
def db_type():
    return "postgres"


@fixture(scope="session")
def db(database_url):
    from gino_starlette import Gino

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

    return User.query


@fixture(scope="session")
def app(db, User, query, model_cls):
    from fastapi_pagination.ext.gino import paginate

    app = FastAPI()
    db.init_app(app)

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(query)

    return add_pagination(app)


class TestGino(BasePaginationTestCase):
    pass
