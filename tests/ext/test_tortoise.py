import pytest
from fastapi import FastAPI
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

from fastapi_pagination.ext.tortoise import apaginate
from tests.base import BasePaginationTestSuite


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
    orders: list[OrderOut]


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return lambda: User

    return lambda: User.all()


@pytest.fixture(scope="session")
def database_url(database_url, sqlite_file):
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgres://")
    if database_url.startswith("sqlite"):
        database_url = f"sqlite://{sqlite_file}"

    return database_url


@pytest.fixture(scope="session")
def app(database_url, query):
    app = FastAPI()

    EXECUTOR_CACHE.clear()
    register_tortoise(
        app,
        modules={"models": [__name__]},
        db_url=database_url,
    )

    return app


class TestTortoiseDefault(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, app, builder, query):
        builder.app = app

        @builder.both.default
        async def route():
            return await apaginate(query(), prefetch_related=False)

        return builder.build()


class TestTortoiseRelationship(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, app, builder, query, pagination_params):
        builder.app = app
        builder = builder.classes.update(model_with_rel=UserWithRelationOut)

        @builder.both.relationship
        async def route():
            return await apaginate(query(), **pagination_params())

        return builder.build()

    @pytest.fixture(
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
