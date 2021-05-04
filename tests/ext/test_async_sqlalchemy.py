from typing import AsyncIterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.async_sqlalchemy import paginate

from ..base import BasePaginationTestCase, SafeTestClient, UserOut
from ..utils import faker


@fixture(scope="session")
def database_url(database_url) -> str:
    database_url = database_url.replace("postgresql", "postgresql+asyncpg", 1)
    database_url = database_url.replace("sqlite", "sqlite+aiosqlite", 1)

    return database_url


@fixture(scope="session")
def engine(database_url):
    return create_async_engine(database_url)


@fixture(scope="session")
def Session(engine):
    return sessionmaker(engine, class_=AsyncSession)


@fixture(scope="session")
def Base(engine):
    return declarative_base()


@fixture(scope="session")
def User(Base):
    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String, nullable=False)

    return User


@fixture(scope="session")
def app(Base, User, Session, engine):
    app = FastAPI()

    @app.on_event("startup")
    async def on_startup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with Session() as session:
            session.add_all([User(name=faker.name()) for _ in range(100)])
            await session.commit()

    async def get_db() -> AsyncIterator[Session]:
        async with Session() as session:
            yield session

    @app.get("/default", response_model=Page[UserOut])
    @app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
    async def route(db: Session = Depends(get_db)):
        return await paginate(db, select(User))

    add_pagination(app)
    return app


class TestAsyncSQLAlchemy(BasePaginationTestCase):
    @fixture(scope="session")
    def client(self, app):
        with SafeTestClient(app) as c:
            yield c

    @fixture(scope="session")
    async def entities(self, Session, User):
        async with Session() as session:
            result = await session.execute(select(User))
            return [*result.scalars()]
