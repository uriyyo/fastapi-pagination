from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pytest import fixture, mark

from fastapi_pagination import LimitOffsetPage, Page, add_pagination

from ..base import BasePaginationTestCase
from .utils import mongodb_test

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
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@fixture(scope="session")
def db_engine(db_client):
    return AIOEngine(db_client, database="test")


@fixture(scope="session")
def db_model(db_engine):
    class User(Model):
        name: str

        model_config = {
            "collection": "users",
        }

    return User


@fixture(scope="session")
def app(db_engine, db_model, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db_engine, db_model)

    return add_pagination(app)


@mark.odmantic
@mongodb_test
class TestOdmantic(BasePaginationTestCase):
    @fixture(scope="session")
    def model_cls(self):
        class Model(BaseModel):
            name: str

        return Model
