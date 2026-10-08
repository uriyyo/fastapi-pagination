import asyncio
import warnings
from asyncio import current_task
from contextlib import closing
from functools import partial
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy import bindparam
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine
from sqlalchemy.orm import scoped_session, selectinload, sessionmaker
from sqlmodel import Field, Relationship, Session, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields
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


class TestSQLModelNoDeprecationWarnings:
    @pytest.fixture(scope="session")
    def async_sa_engine(self, database_url):
        async_url = database_url.replace("postgresql", "postgresql+asyncpg", 1).replace("sqlite", "sqlite+aiosqlite", 1)

        return create_async_engine(async_url)

    @pytest.fixture(params=["limit-offset", "cursor"])
    def page_cls_and_params(self, request):
        if request.param == "cursor":
            return CursorPage[Any], CursorParams(size=10)

        return Page[Any], Params(page=1, size=10)

    @staticmethod
    def _assert_no_deprecation_warnings(records: list[warnings.WarningMessage]) -> None:
        deprecations = [r for r in records if issubclass(r.category, DeprecationWarning)]
        assert not deprecations, [str(r.message) for r in deprecations]

    @pytest.mark.parametrize("scoped", [False, True])
    def test_paginate(self, sa_engine, sm_user, page_cls_and_params, scoped):
        page_cls, params = page_cls_and_params
        factory = scoped_session(sessionmaker(sa_engine, class_=Session)) if scoped else partial(Session, sa_engine)
        session = factory()

        with warnings.catch_warnings(record=True) as records, set_page(page_cls):
            warnings.simplefilter("always")
            page = paginate(factory if scoped else session, select(sm_user).order_by(sm_user.id), params)

        session.close()

        assert page.items
        self._assert_no_deprecation_warnings(records)

    @pytest.mark.asyncio(scope="session")
    @pytest.mark.parametrize("scoped", [False, True])
    async def test_apaginate(self, async_sa_engine, sm_user, page_cls_and_params, scoped):
        page_cls, params = page_cls_and_params
        factory = (
            async_scoped_session(async_sessionmaker(async_sa_engine, class_=AsyncSession), scopefunc=current_task)
            if scoped
            else partial(AsyncSession, async_sa_engine)
        )
        session = factory()

        with warnings.catch_warnings(record=True) as records, set_page(page_cls):
            warnings.simplefilter("always")
            page = await apaginate(factory if scoped else session, select(sm_user).order_by(sm_user.id), params)

        await session.close()

        assert page.items
        self._assert_no_deprecation_warnings(records)


class TestSQLModelAsyncHooks:
    @pytest.fixture(scope="session")
    def async_sa_engine(self, database_url):
        async_url = database_url.replace("postgresql", "postgresql+asyncpg", 1).replace("sqlite", "sqlite+aiosqlite", 1)

        return create_async_engine(async_url)

    @pytest.mark.asyncio(scope="session")
    @pytest.mark.parametrize("use_connection", [False, True])
    async def test_async_transformer_and_additional_data(self, async_sa_engine, sm_user, entities, use_connection):
        async def transformer(items):
            await asyncio.sleep(0)
            return [("transformed", item) for item in items]

        async def additional_data(items):
            await asyncio.sleep(0)
            return {"extra": len(items)}

        with set_page(CustomizedPage[Page[Any], UseAdditionalFields(extra=int)]):
            if use_connection:
                async with async_sa_engine.connect() as conn:
                    page = await apaginate(
                        conn,
                        select(sm_user).order_by(sm_user.id),
                        Params(page=1, size=10),
                        transformer=transformer,
                        additional_data=additional_data,
                    )
            else:
                async with AsyncSession(async_sa_engine) as session:
                    page = await apaginate(
                        session,
                        select(sm_user).order_by(sm_user.id),
                        Params(page=1, size=10),
                        transformer=transformer,
                        additional_data=additional_data,
                    )

        assert len(page.items) == 10
        assert all(marker == "transformed" for marker, _ in page.items)
        assert page.total == len(entities)
        assert page.extra == 10
