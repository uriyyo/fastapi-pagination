from contextlib import closing
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from fastapi_pagination import Page, Params, set_page, set_params
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields, UseQuotedCursor
from fastapi_pagination.ext.sqlalchemy import apaginate, paginate
from tests.base import BasePaginationTestSuite, SuiteBuilder, async_sync_testsuite, sync_testsuite
from tests.ext.utils import is_sqlalchemy20
from tests.schemas import UserOut, UserWithoutIDOut
from tests.utils import maybe_async


class _SQLAlchemyPaginateFuncMixin:
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

        @builder.cursor.relationship
        async def route_relationship(db: Any = Depends(sa_session_ctx)):
            return await maybe_async(
                paginate_func(db, select(sa_user).options(selectinload(sa_user.orders)).order_by(sa_user.id)),
            )

        return builder.build()

    @pytest.mark.asyncio(scope="session")
    async def test_no_order(self, sa_session, sa_user, paginate_func):
        with (
            pytest.raises(ValueError, match=r"^Cursor pagination requires ordering$"),
            set_page(CursorPage[UserOut]),
            set_params(CursorPage.__params_type__()),
        ):
            await maybe_async(paginate_func(sa_session(), select(sa_user)))


@async_sync_testsuite
class TestCompoundSelectSQLAlchemyCursor(_SQLAlchemyPaginateFuncMixin, BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_session_ctx, paginate_func):
        builder = builder.new()

        @builder.cursor.default
        async def route(db: Any = Depends(sa_session_ctx)):
            stmt = select(sa_user).union_all(select(sa_user)).order_by("id")
            return await maybe_async(paginate_func(db, stmt, unique=False))

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


class TestSQLAlchemyInlineCount:
    def test_inline_count_select_model(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[UserOut]):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert page.total == len(entities)
        assert len(page.items) == 10
        assert all(isinstance(item, UserOut) for item in page.items)

    def test_inline_count_total_matches_full_count(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert page.total == len(entities)

    def test_inline_count_with_filter(self, sa_session, sa_user, entities):
        target_name = entities[0].name

        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user).where(sa_user.name == target_name),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert page.total == sum(1 for e in entities if e.name == target_name)

    def test_inline_count_items_are_model_instances(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=1, size=5),
                inline_count=func.count().over(),
            )

        assert len(page.items) == 5
        assert all(isinstance(item, sa_user) for item in page.items)

    def test_inline_count_non_scalar_query(self, sa_session, sa_user, entities):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user.id, sa_user.name),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert page.total == len(entities)
        assert all(item.id is not None and item.name is not None for item in page.items)

    def test_inline_count_distinct_total_is_correct(self, sa_session, sa_user, sa_order, entities):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user).join(sa_order).distinct(),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        expected_total = len({e.id for e in entities})
        assert page.total == expected_total

    def test_inline_count_distinct_items_are_model_instances(self, sa_session, sa_user, sa_order, entities):
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user).join(sa_order).distinct(),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert all(isinstance(item, sa_user) for item in page.items)

    def test_inline_count_out_of_range_page_total_is_correct(self, sa_session, sa_user, entities):
        """Out-of-range offset must still report the correct total, not 0."""
        with closing(sa_session()) as session, set_page(Page[Any]):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=9999, size=10),
                inline_count=func.count().over(),
            )

        assert page.items == []
        assert page.total == len(entities)

    def test_inline_count_include_total_false_skips_count(self, sa_session, sa_user, entities):
        """When include_total=False the total must be None and no count is computed."""
        from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal

        NoTotalPage = CustomizedPage[Page[Any], UseIncludeTotal(False)]
        no_total_params = NoTotalPage.__params_type__()

        with closing(sa_session()) as session, set_page(NoTotalPage), set_params(no_total_params):
            page = paginate(
                session,
                select(sa_user),
                inline_count=func.count().over(),
            )

        assert page.total is None
        assert len(page.items) > 0

    @pytest.mark.asyncio(scope="session")
    async def test_inline_count_apaginate(self, sa_user, sa_engine, entities):
        """The async apaginate path must work with inline_count."""
        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

        if not isinstance(sa_engine, AsyncEngine):
            pytest.skip("async engine required for this test")

        async with AsyncSession(sa_engine) as session, set_page(Page[Any]):
            page = await apaginate(
                session,
                select(sa_user),
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
            )

        assert page.total == len(entities)
        assert len(page.items) == 10
        assert all(isinstance(item, sa_user) for item in page.items)

    def test_inline_count_distinct_preserves_order(self, sa_session, sa_user, sa_order, entities):
        """ORDER BY must be preserved when DISTINCT wraps the query in a subquery."""
        with closing(sa_session()) as session, set_page(Page[Any]):
            page_asc = paginate(
                session,
                select(sa_user).join(sa_order).distinct().order_by(sa_user.id.asc()),
                params=Params(page=1, size=100),
                inline_count=func.count().over(),
            )

        ids = [item.id for item in page_asc.items]
        assert ids == sorted(ids), "Items must be returned in ascending id order"

    def test_inline_count_legacy_query_new_style_raises(self, sa_session, sa_user):
        """paginate(conn, legacy_Query, inline_count=...) must raise TypeError."""
        with closing(sa_session()) as session:
            legacy_query = session.query(sa_user)
            with pytest.raises(TypeError, match="inline_count is not supported"):
                paginate(session, legacy_query, inline_count=func.count().over())

    def test_inline_additional_data_callable_basic(self, sa_session, sa_user, entities):
        """Callable additional_data extracts aggregated values from raw rows."""

        CustomPage = CustomizedPage[Page[Any], UseAdditionalFields(user_count_sum=(int, ...))]

        stmt = select(
            sa_user,
            func.count(sa_user.id).over().label("_inline_total"),
        ).order_by(sa_user.id)

        def extract(rows):
            return {"user_count_sum": rows[0]._mapping["_inline_total"] if rows else 0}

        with closing(sa_session()) as session, set_page(CustomPage):
            page = paginate(
                session,
                stmt,
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
                additional_data=extract,
            )

        assert page.user_count_sum == page.total

    def test_inline_additional_data_callable_empty_page(self, sa_session, sa_user):
        """Callable receives an empty list when query returns no rows."""

        CustomPage = CustomizedPage[Page[Any], UseAdditionalFields(fallback=(str, ...))]

        stmt = select(sa_user).where(sa_user.id == -999)

        def extract(rows):
            return {"fallback": "empty" if not rows else "found"}

        with closing(sa_session()) as session, set_page(CustomPage):
            page = paginate(
                session,
                stmt,
                params=Params(page=1, size=10),
                inline_count=func.count().over(),
                additional_data=extract,
            )

        assert page.fallback == "empty"
        assert page.total == 0

    def test_callable_additional_data_without_inline_count(self, sa_session, sa_user, entities):
        """Callable additional_data works without inline_count, receiving unwrapped items."""
        CustomPage = CustomizedPage[Page[Any], UseAdditionalFields(page_item_count=(int, ...))]

        with closing(sa_session()) as session, set_page(CustomPage):
            page = paginate(
                session,
                select(sa_user),
                params=Params(page=1, size=10),
                additional_data=lambda items: {"page_item_count": len(items)},
            )

        assert page.page_item_count == len(page.items)
