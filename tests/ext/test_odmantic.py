from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture, mark

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase

try:
    from odmantic import AIOEngine, Model

    from fastapi_pagination.ext.odmantic import paginate

    has_odmantic = True
except ImportError:
    Model = None
    AIOEngine = None

    has_odmantic = False


pytestmark = mark.skipif(
    not has_odmantic,
    reason="Odmantic is not installed",
)


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@fixture(scope="session")
def db_model():
    class User(Model):
        name: str

    return User


@fixture(scope="session")
def db_engine(db_client):
    return AIOEngine(db_client)


@fixture(scope="session")
def app(db_client, db_engine, db_model, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db_engine, db_model)

    return add_pagination(app)


class TestOdmantic(BasePaginationTestCase):
    pass
