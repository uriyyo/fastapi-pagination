from typing import List

from beanie import Document, init_beanie
from beanie.odm.queries.find import FindMany
from fastapi import FastAPI, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field, parse_obj_as
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.beanie import paginate

from ..base import BasePaginationTestCase
from ..schemas import UserOut
from .utils import mongodb_test


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

    @app.get("/", response_model=CursorPage[Model], response_model_by_alias=False)
    async def cursor():
        return await paginate(query)

    return add_pagination(app)


@mongodb_test
class TestBeanie(BasePaginationTestCase):
    @mark.asyncio
    async def test_cursor(self, app, client, entities, query):
        entities = sorted(parse_obj_as(List[UserOut], entities), key=(lambda it: (it.id, it.name)))

        items = []
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}

            resp = await client.get("/", params={**params, "size": 10})
            assert resp.status_code == status.HTTP_200_OK
            data = resp.json()

            items.extend(parse_obj_as(List[UserOut], data["items"]))

            if data["next_page"] is None:
                break

            _cursor = cursor

            cursor = data["next_page"]

        assert items == entities

        # backwards paging doesn't work out of the box for FindMany queries
        if isinstance(query, FindMany):
            return

        items = []
        cursor = _cursor

        while True:
            params = {"cursor": cursor} if cursor else {}

            resp = await client.get("/", params={**params, "size": 10})
            assert resp.status_code == status.HTTP_200_OK
            data = resp.json()

            items = parse_obj_as(List[UserOut], data["items"]) + items

            if data["previous_page"] is None:
                break

            cursor = data["previous_page"]

        assert items == entities
