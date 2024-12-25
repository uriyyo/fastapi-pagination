from functools import partial

import pytest
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi_pagination.ext.sqlmodel import paginate
from tests.base import BasePaginationTestSuite, only_cases


@pytest.fixture(scope="session")
def session(sa_engine):
    return partial(AsyncSession, sa_engine)


class TestSQLModelDefault(BasePaginationTestSuite):
    is_async = True

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
    def app(self, query, session, builder):
        builder = builder.new()

        @builder.both.default
        async def route():
            async with session() as db:
                return await paginate(db, query)

        return builder.build()


@only_cases("relationship")
class TestSQLModelRelationship(BasePaginationTestSuite):
    is_async = True

    @pytest.fixture(scope="session")
    def app(self, session, sm_user, builder):
        @builder.both.relationship
        async def route():
            async with session() as db:
                return await paginate(db, select(sm_user).options(selectinload(sm_user.orders)))

        return builder.build()
