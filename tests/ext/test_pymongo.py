import pytest
from fastapi import FastAPI
from pymongo import MongoClient

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@pytest.fixture(scope="session")
def db_client(database_url):
    with MongoClient(database_url) as client:
        yield client


@pytest.fixture(scope="session")
def app(db_client, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return paginate(db_client.test.users)

    return add_pagination(app)


@mongodb_test
class TestPymongo(BasePaginationTestSuite):
    pass
