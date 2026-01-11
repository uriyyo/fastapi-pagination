import pytest
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
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


@pytest.mark.usefixtures("db_client")
@mongodb_test
class TestBeanieAggregateTransformer(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def entities(self, entities):
        entities = sorted(entities, key=lambda x: x.name)
        return entities[:20]

    @pytest.fixture(scope="session")
    def app(self, builder, be_user):
        @builder.both.default
        async def route():
            return await apaginate(
                be_user.aggregate([]),
                aggregation_pipeline_transformer=lambda pipeline: [
                    {"$sort": {"name": 1}},
                    {"$limit": 20},
                    *pipeline,
                ],
            )

        return builder.build()


class _UserProjection(BaseModel):
    name: str


@pytest.mark.usefixtures("db_client")
@mongodb_test
class TestBeanieAggregate(BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["with-projection", "without-projection"],
    )
    def aggr_projection(self, request):
        if request.param:
            return _UserProjection

        return None

    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["with-match", "without-match"],
    )
    def match_stage(self, request):
        if not request.param:
            return None

        return {"$match": {"name": {"$exists": True}}}

    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["with-sort", "without-sort"],
    )
    def sort_stage(self, request):
        if not request.param:
            return None

        return {"$sort": {"name": 1}}

    @pytest.fixture(scope="session")
    def aggr_query(self, be_user, match_stage, sort_stage, aggr_projection):
        pipeline = []
        if match_stage:
            pipeline.append(match_stage)
        if sort_stage:
            pipeline.append(sort_stage)

        return be_user.aggregate(pipeline, projection_model=aggr_projection)

    @pytest.fixture(scope="session")
    def entities(self, entities, sort_stage):
        if sort_stage:
            return sorted(entities, key=lambda x: x.name)

        return entities

    @pytest.fixture(scope="session")
    def app(self, builder, be_user, aggr_query):
        builder = builder.new()

        class Model(builder.classes.model):
            name: str

        builder = builder.classes.update(model=Model)

        @builder.both.default
        async def route():
            return await apaginate(aggr_query)

        return builder.build()
