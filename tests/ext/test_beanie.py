from typing import Any

import pytest
from beanie import Document, init_beanie
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import Page, set_page, set_params
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal
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
    client = AsyncMongoClient(database_url)
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

    @pytest.mark.asyncio(scope="session")
    async def test_cursor_links(self, be_user, entities):
        total = len(entities)

        page = await apaginate(be_user, CursorParams(size=total))
        assert len(page.items) == total
        assert page.next_page is None
        assert page.previous_page is None

        first = await apaginate(be_user, CursorParams(size=total - 1))
        assert first.next_page is not None
        assert first.previous_page is None

        last = await apaginate(be_user, CursorParams(size=total - 1, cursor=first.next_page))
        assert len(last.items) == 1
        assert last.next_page is None
        assert last.previous_page is not None

        back = await apaginate(be_user, CursorParams(size=total - 1, cursor=last.previous_page))
        assert len(back.items) == total - 1
        assert back.next_page is not None
        assert back.previous_page is None

    @pytest.mark.asyncio(scope="session")
    async def test_cursor_links_middle_page(self, be_user, entities):
        first = await apaginate(be_user, CursorParams(size=1))
        middle = await apaginate(be_user, CursorParams(size=1, cursor=first.next_page))
        assert middle.next_page is not None
        assert middle.previous_page is not None

        third = await apaginate(be_user, CursorParams(size=1, cursor=middle.next_page))
        back = await apaginate(be_user, CursorParams(size=1, cursor=third.previous_page))
        assert back.items == middle.items
        assert back.next_page is not None
        assert back.previous_page is not None


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


@pytest.mark.usefixtures("db_client")
@mongodb_test
class TestBeanieAggregateCursor:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_cursor_pages(self, be_user, entities):
        params = CursorParams(size=4)
        page = await apaginate(be_user.aggregate([{"$match": {}}]), params)

        assert len(page.items) == 4
        assert page.previous_page is not None

        seen = list(page.items)
        while page.next_page:
            page = await apaginate(
                be_user.aggregate([{"$match": {}}]),
                CursorParams(size=4, cursor=page.next_page),
            )
            seen.extend(page.items)

        assert len(seen) == len(entities)
        assert len({item["_id"] for item in seen}) == len(entities)

        prev_page = await apaginate(
            be_user.aggregate([{"$match": {}}]),
            CursorParams(size=4, cursor=page.previous_page),
        )
        last = len(page.items)
        assert [item["_id"] for item in prev_page.items] == [item["_id"] for item in seen[-(last + 4) : -last]]

        # prev_ then next_ must round-trip to the page we came from
        back = await apaginate(
            be_user.aggregate([{"$match": {}}]),
            CursorParams(size=4, cursor=prev_page.next_page),
        )
        assert [item["_id"] for item in back.items] == [item["_id"] for item in seen[-last:]][:4]


@pytest.mark.usefixtures("db_client")
@mongodb_test
class TestBeanieAggregateIncludeTotal:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_include_total_false(self, be_user, entities):
        NoTotalPage = CustomizedPage[Page[Any], UseIncludeTotal(False)]

        with set_page(NoTotalPage), set_params(NoTotalPage.__params_type__(page=1, size=10)):
            page = await apaginate(be_user.aggregate([{"$sort": {"id": 1}}]))

        assert page.total is None
        assert [item["id"] for item in page.items] == [entity.id for entity in entities[:10]]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_include_total_false_with_filter_end(self, be_user, entities):
        NoTotalPage = CustomizedPage[Page[Any], UseIncludeTotal(False)]

        with set_page(NoTotalPage), set_params(NoTotalPage.__params_type__(page=1, size=10)):
            page = await apaginate(
                be_user.aggregate([{"$sort": {"id": 1}}, {"$addFields": {"flag": True}}]),
                aggregation_filter_end="auto",
            )

        assert page.total is None
        assert all(item["flag"] for item in page.items)
        assert len(page.items) == 10
