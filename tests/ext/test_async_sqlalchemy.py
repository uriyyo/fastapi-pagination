from collections.abc import AsyncIterator

import pytest
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_pagination.ext.sqlalchemy import paginate
from tests.base import BasePaginationTestSuite, add_cases

from .utils import sqlalchemy20


@sqlalchemy20
@add_cases("non-scalar", "relationship")
class TestAsyncSQLAlchemy(BasePaginationTestSuite):
    is_async = True

    @pytest.fixture(scope="session")
    def app(self, sa_session, sa_user, builder):
        async def get_db() -> AsyncIterator[AsyncSession]:
            async with sa_session() as session:
                yield session

        @builder.both.default
        async def route_1(db: AsyncSession = Depends(get_db)):
            return await paginate(db, select(sa_user))

        @builder.both.non_scalar
        async def route_2(db: AsyncSession = Depends(get_db)):
            return await paginate(db, select(sa_user.id, sa_user.name))

        @builder.both.relationship
        async def route_3(db: AsyncSession = Depends(get_db)):
            return await paginate(db, select(sa_user).options(selectinload(sa_user.orders)))

        return builder.build()
