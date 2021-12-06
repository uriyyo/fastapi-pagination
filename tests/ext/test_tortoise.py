from random import choice
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

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase
from ..utils import faker


class Order(Model):
    id = IntField(pk=True)
    name = TextField(null=False)
    user = ForeignKeyField(f"models.User", related_name="orders")

    class Meta:
        table = "orders"


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)

    orders: ReverseRelation[Order]

    class Meta:
        table = "users"


@fixture(scope="session")
def database_url(database_url):
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgres://")
    if database_url.startswith("sqlite"):
        return "sqlite://:memory:"

    return database_url


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


class BaseTortoiseTestCase(BasePaginationTestCase):
    @fixture(scope="session")
    def model_cls(self):
        return self.model

    @fixture(scope="session")
    async def app(self, database_url, query, model_cls, pagination_params):
        app = FastAPI()

        EXECUTOR_CACHE.clear()
        register_tortoise(
            app,
            modules={"models": [__name__]},
            db_url=database_url,
            generate_schemas=True,
        )

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        async def route():
            return await paginate(query(), **pagination_params())

        add_pagination(app)
        return app


class TestTortoise(BaseTortoiseTestCase):
    @fixture(scope="session")
    def pagination_params(self):
        return lambda: {"prefetch_related": False}

    @fixture(scope="session")
    async def entities(self, query, client):
        await User.all().delete()
        await User.bulk_create(User(name=faker.name()) for _ in range(100))

        return await User.all()


class OrderOut(PydanticModel):
    name: str


class UserWithRelationOut(PydanticModel):
    name: str
    orders: List[OrderOut]


class TestTortoiseWithRelatedObjects(BaseTortoiseTestCase):
    model = UserWithRelationOut

    @fixture(
        scope="session",
        params=[lambda: True, lambda: ["orders"], lambda: [Prefetch("orders", Order.all())]],
        ids=["bool", "list", "prefetch"],
    )
    def pagination_params(self, request):
        return lambda: {"prefetch_related": request.param()}

    @fixture(scope="session")
    async def entities(self, query, client):
        await User.all().delete()
        await User.bulk_create(User(name=faker.name()) for _ in range(100))

        users = await User.all()
        await Order.bulk_create(Order(name=faker.name(), user=choice(users)) for _ in range(300))

        return await User.all().prefetch_related("orders")
