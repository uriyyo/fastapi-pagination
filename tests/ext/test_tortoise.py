from fastapi import Depends, FastAPI
from pytest import fixture
from tortoise import Model
from tortoise.backends.base.executor import EXECUTOR_CACHE
from tortoise.contrib.fastapi import register_tortoise
from tortoise.fields import IntField, TextField

from fastapi_pagination import (
    LimitOffsetPage,
    LimitOffsetPaginationParams,
    Page,
    PaginationParams,
)
from fastapi_pagination.ext.tortoise import paginate

from ..base import (
    BasePaginationTestCase,
    SafeTestClient,
    UserOut,
    limit_offset_params,
    page_params,
)
from ..utils import faker


@fixture(scope="session")
def sqlite_url() -> str:
    return "sqlite://:memory:"


class User(Model):
    id = IntField(pk=True)
    name = TextField(null=False)

    class Meta:
        table = "users"


@fixture(scope="session", params=["model", "query"])
def query_type(request):
    return request.param


@fixture(scope="session", params=["model", "query"])
def app(query_type, database_url):
    app = FastAPI()

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgres://")

    EXECUTOR_CACHE.clear()
    register_tortoise(
        app,
        modules={"models": [__name__]},
        db_url=database_url,
        generate_schemas=True,
    )

    def query():
        if query_type == "model":
            return User

        return User.all()

    @app.get("/implicit", response_model=Page[UserOut], dependencies=[Depends(page_params)])
    async def route():
        return await paginate(query())

    @app.get("/explicit", response_model=Page[UserOut])
    async def route(params: PaginationParams = Depends()):
        return await paginate(query(), params)

    @app.get(
        "/implicit-limit-offset",
        response_model=LimitOffsetPage[UserOut],
        dependencies=[Depends(limit_offset_params)],
    )
    async def route():
        return await paginate(query())

    @app.get("/explicit-limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route(params: LimitOffsetPaginationParams = Depends()):
        return await paginate(query(), params)

    return app


class TestTortoise(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, client):
        for _ in range(100):
            await User.create(name=faker.name())

        return await User.all()
