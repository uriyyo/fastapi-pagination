from typing import AsyncIterator

from fastapi import Depends, FastAPI
from pytest import fixture
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.async_sqlalchemy import paginate

from ..base import BasePaginationTestCase

try:
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    AsyncSession = None


@fixture(scope="session")
def is_async_db():
    return True


@fixture(scope="session")
def app(sa_session, sa_user, model_cls, model_with_rel_cls):
    app = FastAPI()

    async def get_db() -> AsyncIterator[AsyncSession]:
        async with sa_session() as session:
            yield session

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route(db: AsyncSession = Depends(get_db)):
        return await paginate(db, select(sa_user))

    @app.get("/non-scalar/default", response_model=Page[model_cls])
    @app.get("/non-scalar/limit-offset", response_model=LimitOffsetPage[model_cls])
    async def route(db: AsyncSession = Depends(get_db)):
        return await paginate(db, select(sa_user.id, sa_user.name))

    @app.get("/relationship/default", response_model=Page[model_with_rel_cls])
    @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_with_rel_cls])
    async def route(db: AsyncSession = Depends(get_db)):
        return await paginate(db, select(sa_user).options(selectinload(sa_user.orders)))

    return add_pagination(app)


class TestAsyncSQLAlchemy(BasePaginationTestCase):
    pagination_types = ["default", "non-scalar", "relationship"]
