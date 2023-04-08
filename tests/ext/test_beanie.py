from beanie import Document, init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.beanie import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def database_url(mongodb_url) -> str:
    return mongodb_url


@fixture(scope="session")
def be_user():
    class User(Document):
        id_: int = Field(alias="id")
        name: str

        class Settings:
            name = "users"

    return User


@async_fixture(scope="session")
async def db_client(database_url, be_user):
    client = AsyncIOMotorClient(database_url)
    await init_beanie(database=client.test, document_models=[be_user])
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

    class Model(model_cls):
        id: int = Field(alias="id_")

        class Config:
            allow_population_by_field_name = True

    @app.get("/default", response_model=Page[Model], response_model_by_alias=False)
    @app.get("/limit-offset", response_model=LimitOffsetPage[Model], response_model_by_alias=False)
    async def route():
        return await paginate(query)

    return add_pagination(app)


class TestBeanie(BasePaginationTestCase):
    pass
