from contextlib import closing
from functools import partial
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy import bindparam
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_pagination import Page, Params, set_page
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


class TestSQLModelBindParams:
    @pytest.fixture(scope="session")
    def bound_query(self, sm_user):
        return select(sm_user).where(sm_user.name == bindparam("target_name"))

    @pytest.fixture(scope="session")
    def target_name(self, entities):
        return entities[0].name

    @pytest.fixture(scope="session")
    def expected_total(self, entities, target_name):
        return sum(1 for entry in entities if entry.name == target_name)

    @pytest.fixture(scope="session")
    def async_sa_engine(self, database_url):
        async_url = database_url.replace("postgresql", "postgresql+asyncpg", 1).replace("sqlite", "sqlite+aiosqlite", 1)

        return create_async_engine(async_url)

    def test_bind_params_paginate(self, sm_session, bound_query, target_name, expected_total):
        with closing(sm_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                bound_query,
                params=Params(page=1, size=10),
                bind_params={"target_name": target_name},
                execute_options={"logging_token": "bind-params-test"},
            )

        assert page.total == expected_total
        assert all(item.name == target_name for item in page.items)

    @pytest.mark.asyncio(scope="session")
    async def test_bind_params_apaginate(self, async_sa_engine, bound_query, target_name, expected_total):
        with set_page(Page[Any]):
            async with AsyncSession(async_sa_engine) as session:
                page = await apaginate(
                    session,
                    bound_query,
                    params=Params(page=1, size=10),
                    bind_params={"target_name": target_name},
                    execute_options={"logging_token": "bind-params-test"},
                )

        assert page.total == expected_total
        assert all(item.name == target_name for item in page.items)
