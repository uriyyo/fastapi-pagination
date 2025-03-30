from functools import partial
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_pagination.ext.sqlmodel import apaginate, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import create_ctx, maybe_async


@pytest.fixture(scope="session")
def sm_session(sa_engine, is_async_db):
    return partial(AsyncSession if is_async_db else Session, sa_engine)


@pytest.fixture(scope="session")
def sm_session_ctx(sm_session, is_async_db):
    return create_ctx(sm_session, is_async_db)


@pytest.fixture(scope="session")
def sm_user(sm_order):
    class User(SQLModel, table=True):
        __tablename__ = "users"

        id: int = Field(primary_key=True)
        name: str

        orders: list[sm_order] = Relationship()

    return User


@pytest.fixture(scope="session")
def sm_order():
    class Order(SQLModel, table=True):
        __tablename__ = "orders"

        id: int = Field(primary_key=True)
        user_id: int = Field(foreign_key="users.id")
        name: str

    return Order


class _SQLModelPaginateFunc:
    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        if is_async_db:
            return apaginate

        return paginate


@async_sync_testsuite
class TestSQLModelDefault(_SQLModelPaginateFunc, BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["model", "query"],
    )
    def query(self, request, sm_user):
        if request.param:
            return sm_user

        return select(sm_user)

    @pytest.fixture(scope="session")
    def app(self, builder, query, sm_session_ctx, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route(db: Any = Depends(sm_session_ctx)):
            return await maybe_async(paginate_func(db, query))

        return builder.build()


@async_sync_testsuite
class TestSQLModelRelationship(_SQLModelPaginateFunc, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sm_session_ctx, sm_user, paginate_func):
        builder = builder.new()

        @builder.both.relationship
        async def route(db: Any = Depends(sm_session_ctx)):
            return await maybe_async(paginate_func(db, select(sm_user).options(selectinload(sm_user.orders))))

        return builder.build()
