from fastapi import FastAPI
from flaky import flaky
from motor.motor_asyncio import AsyncIOMotorClient
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.motor import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def db_client(database_url):
    client = AsyncIOMotorClient(database_url)
    yield client
    client.close()


@fixture(scope="session")
def entities(entities):
    return sorted(entities, key=lambda entity: entity.name)


@fixture(scope="session")
def app(db_client, model_cls):
    app = FastAPI()

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route():
        return await paginate(db_client.test.users, sort=["name", 1])

    return add_pagination(app)


@flaky(max_runs=5)
class TestMotor(BasePaginationTestCase):
    pass
