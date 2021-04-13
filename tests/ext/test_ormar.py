import databases
import sqlalchemy
from fastapi import FastAPI
from ormar import Integer, Model, ModelMeta, String
from pytest import fixture

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.ormar import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, SafeTestClient, UserOut
from ..utils import faker


@fixture(scope="session")
def db(database_url):
    return databases.Database(database_url)


@fixture(scope="session")
def meta(database_url):
    return sqlalchemy.MetaData()


@fixture(scope="session")
def User(meta, db):
    class User(Model):
        class Meta(ModelMeta):
            database = db
            metadata = meta

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
    else:
        return User.objects


@fixture(scope="session")
def app(db, meta, User, query):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup() -> None:
        engine = sqlalchemy.create_engine(str(db.url))
        meta.drop_all(engine)
        meta.create_all(engine)
        await db.connect()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await db.disconnect()

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(query)

    add_pagination(app)
    return app


class TestOrmar(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, User, query, client):
        await User.objects.delete(each=True)
        for _ in range(100):
            await User.objects.create(name=faker.name())
        return await User.objects.all()
