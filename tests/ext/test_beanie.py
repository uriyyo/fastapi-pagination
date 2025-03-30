import pytest
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination.ext.beanie import apaginate
from tests.base import BasePaginationTestSuite

from .utils import mongodb_test


@pytest.fixture(scope="session")
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


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, be_user):
    if request.param:
        return be_user

    return be_user.find()


@pytest.mark.usefixtures("db_client")
@mongodb_test
class TestBeanie(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, query):
        class Model(builder.classes.model):
            id: int = Field(alias="id_")

            class Config:
                allow_population_by_field_name = True

        builder = builder.classes.update(model=Model)

        @builder.cursor.default.with_kwargs(response_model_by_alias=False)
        async def cursor_route():
            return await apaginate(query)

        @builder.both.default.with_kwargs(response_model_by_alias=False)
        async def route():
            return await apaginate(query)

        return builder.build()
