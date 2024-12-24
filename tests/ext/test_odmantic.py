from collections.abc import Awaitable

import pytest
from fastapi import FastAPI
from motor import MotorClient
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine, Model, SyncEngine

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.odmantic import paginate
from tests.base import BasePaginationTestCase

from .utils import mongodb_test


@pytest.fixture(scope="session")
def db_model():
    class User(Model):
        name: str

        model_config = {
            "collection": "users",
        }

    return User


@pytest.fixture(scope="session")
def app(db_engine, db_model, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        res = paginate(db_engine, db_model)

        if isinstance(res, Awaitable):
            res = await res

        return res

    return add_pagination(app)


@pytest.mark.odmantic
@mongodb_test
class TestOdmanticAsync(BasePaginationTestCase):
    @pytest.fixture(scope="session")
    def db_client(self, database_url):
        client = AsyncIOMotorClient(database_url)
        yield client
        client.close()

    @pytest.fixture(scope="session")
    def db_engine(self, db_client):
        return AIOEngine(db_client, database="test")


@pytest.mark.odmantic
@mongodb_test
class TestOdmanticSync(BasePaginationTestCase):
    @pytest.fixture(scope="session")
    def db_client(self, database_url):
        client = MotorClient(database_url)
        yield client
        client.close()

    @pytest.fixture(scope="session")
    def db_engine(self, db_client):
        return SyncEngine(db_client, database="test")
