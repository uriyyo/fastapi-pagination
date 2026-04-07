import pytest
from fastapi import Depends
from peewee import Model, TextField

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.peewee import apaginate, paginate
from tests.base import BasePaginationTestSuite, async_sync_testsuite
from tests.utils import create_ctx, maybe_async


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
def peewee_db_ctx(peewee_db, is_async_db):
    """Create database context manager."""
    return create_ctx(peewee_db.atomic, is_async_db)


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
    def app(self, builder, query, peewee_user, peewee_order, peewee_db_ctx, paginate_func):
        builder = builder.new()

        @builder.both.default
        async def route_default(db=Depends(peewee_db_ctx)):
            return await maybe_async(paginate_func(db, query))

        @builder.both.non_scalar
        async def route_non_scalar(db=Depends(peewee_db_ctx)):
            # Non-scalar means selecting specific columns instead of full model
            query = peewee_user.select(peewee_user.id, peewee_user.name).order_by(peewee_user.id)
            return await maybe_async(paginate_func(db, query))

        return builder.build()


@async_sync_testsuite
class TestPeeweeRelationship(_PeeweePaginateFunc, BasePaginationTestSuite):
    @pytest.fixture(scope="class")
    def app(self, builder, peewee_user, peewee_order, peewee_db_ctx, paginate_func):
        builder = builder.new()

        @builder.both.relationship
        async def route(db=Depends(peewee_db_ctx)):
            # Use join to get related records and hydrate orders via prefetch after pagination.
            query = peewee_user.select().join(peewee_order).order_by(peewee_user.id).distinct()
            return await maybe_async(paginate_func(db, query, unique=False, prefetch=(peewee_order.select(),)))

        return builder.build()


class TestPeeweeUnwrap:
    def test_scalar_not_unwrapped(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            with set_page(Page[UserOut]):
                page = paginate(peewee_db, peewee_user.select(), params=Params(page=1, size=10))

        assert page.dict()["items"] == [{"id": entry.id, "name": entry.name} for entry in entities[:10]]

    def test_non_scalar_not_unwrapped(self, peewee_db, peewee_user, entities):
        from tests.schemas import UserOut

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)
            with set_page(Page[UserOut]):
                page = paginate(
                    peewee_db,
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
                # Peewee column selection still returns Model instances
                lambda peewee_user, item: isinstance(item, peewee_user),
            ),
        ],
    )
    def test_unwrap_raw_results(self, peewee_db, peewee_user, query, validate):
        q = query(peewee_user)

        with peewee_db.atomic():
            page = paginate(peewee_db, q, params=Params(page=1, size=1))

        assert page.items
        assert validate(peewee_user, page.items[0])


class TestPeeweeAsyncAvailability:
    def test_apaginate_raises_without_async_support(self, peewee_db, peewee_user):
        from fastapi_pagination.ext.peewee import PEEWEE_ASYNC_AVAILABLE, apaginate

        if PEEWEE_ASYNC_AVAILABLE:
            pytest.skip("Async is available, cannot test missing async scenario")

        import asyncio

        with pytest.raises(TypeError, match=r"apaginate requires peewee>=4\.0\.0"):
            asyncio.run(apaginate(peewee_db, peewee_user.select()))

    def test_paginate_works_without_async_support(self, peewee_db, peewee_user):
        from fastapi_pagination import Page, Params, set_page
        from fastapi_pagination.ext.peewee import PEEWEE_ASYNC_AVAILABLE, paginate

        if PEEWEE_ASYNC_AVAILABLE:
            pytest.skip("Async is available, cannot test missing async scenario")

        with peewee_db.atomic():
            peewee_db.create_tables([peewee_user], safe=True)

        with set_page(Page):
            page = paginate(peewee_db, peewee_user.select(), params=Params(page=1, size=10))

        assert page.items == []
