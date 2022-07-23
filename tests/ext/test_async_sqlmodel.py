from functools import partial
from typing import Iterator

from fastapi import Depends, FastAPI
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel, insert, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.async_sqlmodel import paginate

from ..base import BasePaginationTestCase
from ..utils import faker


@fixture(scope="session")
def database_url(database_url) -> str:
    database_url = database_url.replace("postgresql", "postgresql+asyncpg", 1)
    database_url = database_url.replace("sqlite", "sqlite+aiosqlite", 1)

    return database_url


@fixture(scope="session")
def engine(database_url):
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    return create_async_engine(database_url, connect_args=connect_args)


@fixture(scope="session")
def SessionLocal(engine):
    return partial(AsyncSession, engine)


@fixture(scope="session")
def User():
    class User(SQLModel, table=True):
        __tablename__ = "users"

        id: int = Field(primary_key=True)
        name: str

    return User


@fixture(
    scope="session",
    params=[True, False],
    ids=["model", "query"],
)
def query(request, User):
    if request.param:
        return User
    else:
        return select(User)


@fixture(scope="session")
def app(query, engine, User, SessionLocal, model_cls):
    app = FastAPI()

    async def get_db() -> Iterator[AsyncSession]:
        db = SessionLocal()

        async with db.begin():
            yield db

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route(db: AsyncSession = Depends(get_db)):
        return await paginate(db, query)

    return add_pagination(app)


@mark.future_sqlalchemy
class TestSQLModel(BasePaginationTestCase):
    @async_fixture(scope="class")
    async def entities(self, engine, User):
        async with engine.begin() as conn:
            await conn.execute(insert(User).values([{"name": faker.name()} for _ in range(100)]))
            return (await conn.execute(select(User))).unique().all()
