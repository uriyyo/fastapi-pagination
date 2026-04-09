import pytest
from peewee import Model, TextField

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.peewee import apaginate, create_count_query, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import maybe_async


@pytest.fixture(scope="class")
def peewee_db(is_async_db, sqlite_file):
    """Create Peewee database instance."""
    if is_async_db:
        from playhouse.pwasyncio import AsyncSqliteDatabase

        db = AsyncSqliteDatabase(sqlite_file)
    else:
        from peewee import SqliteDatabase

        db = SqliteDatabase(sqlite_file)

    yield db

    if is_async_db:
        import asyncio

        from playhouse.pwasyncio import greenlet_spawn

        asyncio.run(greenlet_spawn(db.close))
        asyncio.run(db.close_pool())
    else:
        db.close()


@pytest.fixture(scope="class")
def peewee_user(peewee_db):
    """Create User model."""
    from peewee import IntegerField

    class User(Model):
        id = IntegerField(primary_key=True)
        name = TextField()

        class Meta:
            database = peewee_db
            table_name = "users"

    return User


@pytest.fixture(scope="class")
def peewee_order(peewee_db, peewee_user):
    """Create Order model."""
    from peewee import ForeignKeyField, IntegerField

    class Order(Model):
        id = IntegerField(primary_key=True)
        user = ForeignKeyField(peewee_user, backref="orders", column_name="user_id")
        name = TextField()

        class Meta:
            database = peewee_db
            table_name = "orders"

    return Order


class _PeeweePaginateFunc:
    """Helper class for peewee pagination tests."""

    add_pydantic_v1_suites = True

    @pytest.fixture(scope="session")
    def paginate_func(self, is_async_db):
        if is_async_db:
            return apaginate

        return paginate


@async_sync_testsuite
class TestPeeweeDefault(_PeeweePaginateFunc, BasePaginationTestSuite):
    @pytest.fixture(
        scope="class",
        params=[True, False],
        ids=["model", "query"],
    )
    def query(self, request, peewee_user):
        if request.param:
            return peewee_user

        return peewee_user.select().order_by(peewee_user.id)

    @pytest.fixture(scope="class")
    def app(self, builder, query, peewee_user, peewee_order, paginate_func, peewee_db):
        builder = builder.new()

        @builder.both.default
        async def route_default():
            return await maybe_async(paginate_func(query))

        @builder.both.non_scalar
        async def route_non_scalar():
            q = peewee_user.select(peewee_user.id, peewee_user.name).order_by(peewee_user.id)
            return await maybe_async(paginate_func(q))

        return builder.build()


@async_sync_testsuite
class TestPeeweeRelationship(_PeeweePaginateFunc, BasePaginationTestSuite):
    @pytest.fixture(scope="class")
    def app(self, builder, peewee_user, peewee_order, paginate_func):
        builder = builder.new()

        @builder.both.relationship
        async def route():
            q = peewee_user.select().join(peewee_order).order_by(peewee_user.id).distinct()
            return await maybe_async(paginate_func(q, unique=False, prefetch=(peewee_order.select(),)))

        return builder.build()


class TestPeeweeUnwrap:
    def test_scalar_not_unwrapped(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            with set_page(Page[UserOut]):
                page = paginate(peewee_user.select(), params=Params(page=1, size=10))

        assert page.dict()["items"] == [{"id": entry.id, "name": entry.name} for entry in entities[:10]]

    def test_non_scalar_not_unwrapped(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            with set_page(Page[UserOut]):
                page = paginate(
                    peewee_user.select(peewee_user.id, peewee_user.name),
                    params=Params(page=1, size=10),
                )

        assert page.dict()["items"] == [{"id": entry.id, "name": entry.name} for entry in entities[:10]]

    @pytest.mark.parametrize(
        ("query", "validate"),
        [
            (
                lambda peewee_user: peewee_user.select(),
                lambda peewee_user, item: isinstance(item, peewee_user),
            ),
            (
                lambda peewee_user: peewee_user.select(peewee_user.id, peewee_user.name),
                lambda peewee_user, item: isinstance(item, peewee_user),
            ),
        ],
    )
    def test_unwrap_raw_results(self, peewee_db, peewee_user, query, validate):
        q = query(peewee_user)

        with peewee_db.atomic():
            page = paginate(q, params=Params(page=1, size=1))

        assert page.items
        assert validate(peewee_user, page.items[0])

    def test_paginate_with_model_class(self, peewee_db, peewee_user):
        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            page = paginate(peewee_user, params=Params(page=1, size=1))

        assert page.items

    def test_unique_false(self, peewee_db, peewee_user):
        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            page = paginate(
                peewee_user.select(),
                params=Params(page=1, size=10),
                unique=False,
            )

        assert page.items


class TestPeeweeAsyncAvailability:
    def test_apaginate_raises_without_async_support(self, peewee_user):
        from fastapi_pagination.ext.peewee import PEEWEE_ASYNC_AVAILABLE, apaginate

        if PEEWEE_ASYNC_AVAILABLE:
            pytest.skip("Async is available, cannot test missing async scenario")

        import asyncio

        with pytest.raises(TypeError, match=r"apaginate requires peewee>=4\.0\.0"):
            asyncio.run(apaginate(peewee_user.select()))

    def test_paginate_works_without_async_support(self, peewee_db, peewee_user):
        from fastapi_pagination import Page, Params, set_page
        from fastapi_pagination.ext.peewee import PEEWEE_ASYNC_AVAILABLE, paginate

        if PEEWEE_ASYNC_AVAILABLE:
            pytest.skip("Async is available, cannot test missing async scenario")

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        with set_page(Page):
            page = paginate(peewee_user.select(), params=Params(page=1, size=10))

        assert page.items == []


class TestPeeweeRawSQL:
    def test_paginate_raw_sql(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        with set_page(Page[UserOut]):
            page = paginate(
                "SELECT * FROM users ORDER BY id",
                params=Params(page=1, size=10),
                db=peewee_db,
            )

        assert len(page.items) == 10
        for i, item in enumerate(page.items):
            assert item.id == entities[i].id
            assert item.name == entities[i].name

    def test_paginate_raw_sql_missing_db(self, peewee_db, peewee_user):
        with pytest.raises(ValueError, match="Database is required for raw SQL"):
            paginate("SELECT * FROM users", params=Params(page=1, size=10))

    def test_paginate_raw_sql_with_limit_offset(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        with set_page(Page[UserOut]):
            page = paginate(
                "SELECT * FROM users ORDER BY id",
                params=Params(page=1, size=5),
                db=peewee_db,
            )

        assert len(page.items) == 5
        for i, item in enumerate(page.items):
            assert item.id == entities[i].id
            assert item.name == entities[i].name

    def test_paginate_raw_sql_count(self, peewee_db, peewee_user):
        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        with set_page(Page):
            page = paginate(
                "SELECT * FROM users",
                params=Params(page=1, size=10),
                db=peewee_db,
            )

        assert page.total == 100


class TestPeeweeCreateCountQuery:
    def test_create_count_query_with_model_select(self, peewee_db, peewee_user):
        from peewee import Select

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        query = peewee_user.select()
        count_query = create_count_query(query, use_subquery=True)

        assert isinstance(count_query, Select)

        count_query_no_subquery = create_count_query(query, use_subquery=False)
        assert isinstance(count_query_no_subquery, Select)

    def test_create_count_query_with_limit_offset(self, peewee_db, peewee_user):
        from peewee import Select

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        query = peewee_user.select().limit(10).offset(5)
        count_query = create_count_query(query, use_subquery=True)

        assert isinstance(count_query, Select)

    def test_create_count_query_with_raw_query(self, peewee_db, peewee_user):
        from peewee import RawQuery

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        raw_query = RawQuery(peewee_db, "SELECT * FROM users")
        count_query = create_count_query(raw_query, use_subquery=True)

        assert count_query is not None

        count_query_no_subquery = create_count_query(raw_query, use_subquery=False)
        assert count_query_no_subquery is not None

    def test_create_count_query_with_raw_sql_string(self, peewee_db, peewee_user):
        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        raw_sql = "SELECT * FROM users"
        count_query = create_count_query(raw_sql, use_subquery=True)

        assert count_query == "SELECT count(*) FROM (SELECT * FROM users) AS __count_query__"
