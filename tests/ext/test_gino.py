from fastapi import Depends, FastAPI
from gino_starlette import Gino
from orm import Integer, String
from pytest import fixture
from sqlalchemy import Column, Integer, String

from fastapi_pagination import (
    LimitOffsetPage,
    LimitOffsetPaginationParams,
    Page,
    PaginationParams,
)
from fastapi_pagination.ext.gino import paginate

from ..base import (
    BasePaginationTestCase,
    SafeTestClient,
    UserOut,
    limit_offset_params,
    page_params,
)
from ..utils import faker


@fixture(scope="session")
def database_url(postgres_url) -> str:
    return postgres_url


@fixture(scope="session")
def db(database_url):
    return Gino(dsn=database_url)


@fixture(scope="session")
def User(db):
    class User(db.Model):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

    return User


@fixture(scope="session")
def app(db, User):
    app = FastAPI()
    db.init_app(app)

    @app.on_event("startup")
    async def on_startup() -> None:
        await db.gino.drop_all()
        await db.gino.create_all()

        for _ in range(100):
            await User.create(name=faker.name())

    @app.get("/implicit", response_model=Page[UserOut], dependencies=[Depends(page_params)])
    async def route():
        return await paginate(User.query)

    @app.get("/explicit", response_model=Page[UserOut])
    async def route(params: PaginationParams = Depends()):
        return await paginate(User.query, params)

    @app.get(
        "/implicit-limit-offset",
        response_model=LimitOffsetPage[UserOut],
        dependencies=[Depends(limit_offset_params)],
    )
    async def route():
        return await paginate(User.query)

    @app.get("/explicit-limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route(params: LimitOffsetPaginationParams = Depends()):
        return await paginate(User.query, params)

    return app


class TestGino(BasePaginationTestCase):
    @fixture(scope="session")
    async def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, User):
        return await User.query.gino.all()
