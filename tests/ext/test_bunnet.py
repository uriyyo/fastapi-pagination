from bunnet import Document, init_bunnet
from fastapi import FastAPI
from pymongo import MongoClient
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.bunnet import paginate

from ..base import BasePaginationTestCase
from .utils import mongodb_test


@fixture(scope="session")
def be_user():
    class User(Document):
        name: str

        class Settings:
            name = "users"

    return User


@async_fixture(scope="session")
def db_client(database_url, be_user):
    client = MongoClient(database_url)
    init_bunnet(database=client.test, document_models=[be_user])
    yield
    client.close()


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, be_user):
    if request.param:
        return be_user

    return be_user.find()


@fixture(scope="session")
def app(db_client, query, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    def route():
        return paginate(query)

    return add_pagination(app)


@mongodb_test
class TestBunnet(BasePaginationTestCase):
    pass
