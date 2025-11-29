from contextlib import closing
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from fastapi_pagination import Page, Params, set_page, set_params
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.customization import CustomizedPage, UseQuotedCursor
from fastapi_pagination.ext.sqlalchemy import apaginate, paginate
from tests.base import BasePaginationTestSuite, SuiteBuilder, async_sync_testsuite, sync_testsuite
from tests.ext.utils import is_sqlalchemy20
from tests.schemas import UserOut, UserWithoutIDOut
from tests.utils import maybe_async


class _SQLAlchemyPaginateFuncMixin:
    add_pydantic_v1_suites = True

    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        if is_async_db:
            return apaginate

        return paginate


@async_sync_testsuite
class TestSQLAlchemyBaseSuite(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["subquery_count", "no_subquery_count"],
    )
    def use_subquery_count(self, request):
        if request.param and not is_sqlalchemy20:
            pytest.skip("subquery_count is not supported for SQLAlchemy<2.0")

        return request.param

    @pytest.fixture(scope="session")
    def app(self, sa_session, sa_user, sa_session_ctx, paginate_func, builder, use_subquery_count):
        builder = builder.new()
        kwargs = {"subquery_count": use_subquery_count}

        @builder.both.default
        async def route_default(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(
                paginate_func(db, select(sa_user), **kwargs),
            )

        @builder.both.non_scalar
        async def route_non_scalar(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(
                paginate_func(db, select(sa_user.id, sa_user.name), **kwargs),
            )

        @builder.both.relationship
        async def route_relationship(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(
                paginate_func(db, select(sa_user).options(selectinload(sa_user.orders)), **kwargs),
            )

        return builder.build()


class TestSQLAlchemyUnwrap:
    def test_scalar_not_unwrapped(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[UserWithoutIDOut]):
            page = paginate(session, select(sa_user.name), params=Params(page=1, size=10))

        assert page.dict()["items"] == [{"name": entry.name} for entry in entities[:10]]

    def test_non_scalar_not_unwrapped(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[UserOut]):
            page = paginate(session, select(sa_user.id, sa_user.name), params=Params(page=1, size=10))

        assert page.dict()["items"] == [{"id": entry.id, "name": entry.name} for entry in entities[:10]]

    @pytest.mark.parametrize(
        ("query", "validate"),
        [
            (
                lambda sa_user: select(sa_user),
                lambda sa_user, item: isinstance(item, sa_user),
            ),
            (
                lambda sa_user: select(sa_user.id),
                lambda sa_user, item: len(item) == 1,
            ),
            (
                lambda sa_user: select(sa_user.id, sa_user.name),
                lambda sa_user, item: len(item) == 2,
            ),
            (
                lambda sa_user: select(sa_user).from_statement(select(sa_user)),
                lambda sa_user, item: isinstance(item, sa_user),
            ),
            (
                lambda sa_user: select(sa_user.id).union_all(select(sa_user.id)),
                lambda sa_user, item: len(item) == 1,
            ),
        ],
    )
    def test_unwrap_raw_results(self, sa_session, sa_user, query, validate):
        q = query(sa_user)

        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(session, q, params=Params(page=1, size=1))

        assert page.items
        assert validate(sa_user, page.items[0])

    @pytest.mark.parametrize(
        ("unwrap_mode", "validate"),
        [
            (None, lambda item, sa_user: isinstance(item, sa_user)),
            ("auto", lambda item, sa_user: isinstance(item, sa_user)),
            ("legacy", lambda item, sa_user: isinstance(item, sa_user)),
            ("unwrap", lambda item, sa_user: isinstance(item, sa_user)),
            ("no-unwrap", lambda item, sa_user: len(item) == 1 and isinstance(item[0], sa_user)),
        ],
    )
    def test_unwrap_mode_select_scalar_model(self, sa_session, sa_user, unwrap_mode, validate):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=1, size=1),
                unwrap_mode=unwrap_mode,
            )

        assert validate(page.items[0], sa_user)

    @pytest.mark.parametrize(
        ("unwrap_mode", "validate"),
        [
            (None, lambda item, sa_user: len(item) == 1),
            ("auto", lambda item, sa_user: len(item) == 1),
            ("legacy", lambda item, sa_user: isinstance(item, str)),
            ("unwrap", lambda item, sa_user: isinstance(item, str)),
            ("no-unwrap", lambda item, sa_user: len(item) == 1),
        ],
    )
    def test_unwrap_mode_select_scalar_column(self, sa_session, sa_user, unwrap_mode, validate):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user.name),
                params=Params(page=1, size=1),
                unwrap_mode=unwrap_mode,
            )

        assert validate(page.items[0], sa_user)

    @pytest.mark.parametrize(
        ("unwrap_mode", "validate"),
        [
            (None, lambda item, sa_user: len(item) == 2),
            ("auto", lambda item, sa_user: len(item) == 2),
            ("legacy", lambda item, sa_user: len(item) == 2),
            ("unwrap", lambda item, sa_user: isinstance(item, sa_user)),
            ("no-unwrap", lambda item, sa_user: len(item) == 2),
        ],
    )
    def test_unwrap_mode_select_non_scalar(self, sa_session, sa_user, unwrap_mode, validate):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user, sa_user.name),
                params=Params(page=1, size=1),
                unwrap_mode=unwrap_mode,
            )

        assert validate(page.items[0], sa_user)


@sync_testsuite
class TestSQLAlchemyOldStyle(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, sa_session, sa_user, sa_session_ctx, paginate_func, builder):
        builder = builder.new()

        @builder.both.default
        async def route(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(paginate_func(db.query(sa_user)))

        return builder.build()


@async_sync_testsuite
class TestSQLAlchemyCursor(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["quoted", "unquoted"],
    )
    def quoted_cursor(self, request) -> bool:
        return request.param

    @pytest.fixture(scope="session")
    def builder(self, quoted_cursor) -> SuiteBuilder:
        return SuiteBuilder.with_classes(
            cursor=CustomizedPage[CursorPage, UseQuotedCursor(quoted_cursor)],
        )

    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_order, sa_session, sa_session_ctx, paginate_func):
        builder = builder.new()

        @builder.cursor.default
        async def route(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(paginate_func(db, select(sa_user).order_by(sa_user.id)))

        return builder.build()

    @pytest.mark.asyncio(scope="session")
    async def test_no_order(self, sa_session, sa_user):
        with (
            pytest.raises(ValueError, match=r"^Cursor pagination requires ordering$"),
            set_page(CursorPage[UserOut]),
            set_params(CursorPage.__params_type__()),
        ):
            await maybe_async(paginate(sa_session(), select(sa_user)))


@async_sync_testsuite
class TestCompoundSelectSQLAlchemyCursor(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_session_ctx, paginate_func):
        builder = builder.new()

        @builder.cursor.default
        async def route(db: Any = Depends(sa_session_ctx)):
            stmt = select(sa_user).union_all(select(sa_user)).order_by("id")
            return await maybe_async(paginate_func(db, stmt))

        return builder.build()

    @pytest.fixture(scope="session")
    def entities(self, entities):
        return entities + entities


@async_sync_testsuite
class TestSQLAlchemyFromStatement(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, paginate_func, sa_user, sa_session_ctx):
        builder = builder.new()

        @builder.both.default.optional
        async def route(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(
                paginate_func(db, select(sa_user).from_statement(text("SELECT * FROM users"))),
            )

        return builder.build()


@async_sync_testsuite
class TestSQLAlchemyRaw(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_session_ctx, paginate_func):
        builder = builder.new()

        @builder.both.default.optional
        async def route(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(paginate_func(db, text("SELECT * FROM users")))

        return builder.build()
