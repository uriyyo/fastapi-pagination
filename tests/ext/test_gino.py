from fastapi import FastAPI
from gino_starlette import Gino
from orm import Integer, String
from pytest import fixture
from sqlalchemy import Column, Integer, String

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.gino import paginate

from ..base import BasePaginationTestCase, UserOut
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
def app(db, User, query):
    app = FastAPI()
    db.init_app(app)

    @app.on_event("startup")
    async def on_startup() -> None:
        await db.gino.drop_all()
        await db.gino.create_all()
        await User.delete.gino.status()

        for _ in range(100):
            await User.create(name=faker.name())

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(query)

    add_pagination(app)
    return app


class TestGino(BasePaginationTestCase):
    @fixture(scope="session")
    async def entities(self, User, query):
        return await User.query.gino.all()
