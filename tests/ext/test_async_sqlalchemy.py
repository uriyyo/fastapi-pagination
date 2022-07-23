from typing import AsyncIterator

import pytest_asyncio
from fastapi import Depends, FastAPI
from pytest import fixture, mark
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.async_sqlalchemy import paginate

from ..base import BasePaginationTestCase
from ..utils import faker

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)


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
def app(Session, engine, model_cls):
    app = FastAPI()

    async def get_db() -> AsyncIterator[Session]:
        async with Session() as session:
            yield session

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route(db: Session = Depends(get_db)):
        return await paginate(db, select(User))

    return add_pagination(app)


@mark.future_sqlalchemy
class TestAsyncSQLAlchemy(BasePaginationTestCase):
    @pytest_asyncio.fixture(scope="class")
    async def entities(self, Session):
        async with Session() as session:
            session.add_all([User(name=faker.name()) for _ in range(100)])
            await session.commit()

            result = await session.execute(select(User))
            return [*result.scalars()]
