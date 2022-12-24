from typing import List

from fastapi import FastAPI
from pytest import fixture
from tortoise import Model
from tortoise.backends.base.executor import EXECUTOR_CACHE
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import PydanticModel
from tortoise.fields import (
    ForeignKeyField,
    IntField,
    ReverseRelation,
    TextField,
)
from tortoise.query_utils import Prefetch

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate

from ..base import BasePaginationTestCase


class Order(Model):
    id = IntField(pk=True)
    name = TextField(null=False)
    user = ForeignKeyField("models.User", related_name="orders")

    class Meta:
        table = "orders"


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)

    orders: ReverseRelation[Order]

    class Meta:
        table = "users"


class OrderOut(PydanticModel):
    id: int
    name: str


class UserWithRelationOut(PydanticModel):
    id: int
    name: str
    orders: List[OrderOut]


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return lambda: User
    else:
        return lambda: User.all()


@fixture(scope="session")
def database_url(database_url, sqlite_file):
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgres://")
    if database_url.startswith("sqlite"):
        database_url = f"sqlite://{sqlite_file}"

    return database_url


@fixture(scope="session")
def app(database_url, query):
    app = FastAPI()

    EXECUTOR_CACHE.clear()
    register_tortoise(
        app,
        modules={"models": [__name__]},
        db_url=database_url,
    )

    return app


class TestTortoiseDefault(BasePaginationTestCase):
    pagination_types = ["default"]

    @fixture(scope="session")
    def app(self, query, app, model_cls):
        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        async def route():
            return await paginate(query(), prefetch_related=False)

        return add_pagination(app)


class TestTortoiseRelationship(BasePaginationTestCase):
    pagination_types = ["relationship"]

    @fixture(scope="session")
    def model_with_rel_cls(self):
        return UserWithRelationOut

    @fixture(scope="session")
    def app(self, app, query, model_with_rel_cls, pagination_params):
        @app.get("/relationship/default", response_model=Page[model_with_rel_cls])
        @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_with_rel_cls])
        async def route():
            return await paginate(query(), **pagination_params())

        return add_pagination(app)

    @fixture(
        scope="session",
        params=[
            lambda: True,
            lambda: ["orders"],
            lambda: [Prefetch("orders", Order.all())],
        ],
        ids=["bool", "list", "prefetch"],
    )
    def pagination_params(self, request):
        return lambda: {"prefetch_related": request.param()}
