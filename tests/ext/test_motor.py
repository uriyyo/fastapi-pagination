import pytest
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate
from tests.base import BasePaginationTestCase

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def entities(entities):
    return sorted(entities, key=lambda entity: entity.name)


@pytest.fixture(scope="session")
def app(db_client, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db_client.test.users, sort=[("name", 1)])

    return add_pagination(app)


@mongodb_test
class TestMotor(BasePaginationTestCase):
    pass
