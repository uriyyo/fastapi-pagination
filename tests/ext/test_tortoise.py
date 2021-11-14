from fastapi import FastAPI
from pytest import fixture
from tortoise import Model
from tortoise.backends.base.executor import EXECUTOR_CACHE
from tortoise.contrib.fastapi import register_tortoise
from tortoise.fields import IntField, TextField

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from fastapi_pagination.limit_offset import Page as LimitOffsetPage

from ..base import BasePaginationTestCase, UserOut
from ..utils import faker


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)

    class Meta:
        table = "users"


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request):
    if request.param:
        return User
    else:
        return User.all()


@fixture(scope="session")
def app(query, database_url):
    app = FastAPI()

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgres://")
    if database_url.startswith("sqlite"):
        database_url = "sqlite://:memory:"

    EXECUTOR_CACHE.clear()
    register_tortoise(
        app,
        modules={"models": [__name__]},
        db_url=database_url,
        generate_schemas=True,
    )

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route():
        return await paginate(query)

    add_pagination(app)
    return app


class TestTortoise(BasePaginationTestCase):
    @fixture(scope="session")
    async def entities(self, query, client):
        await User.all().delete()
        for _ in range(100):
            await User.create(name=faker.name())

        return await User.all()
