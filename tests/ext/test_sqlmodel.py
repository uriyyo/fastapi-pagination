from functools import partial

import pytest
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fastapi_pagination.ext.sqlmodel import paginate
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def session(sa_engine):
    return partial(Session, sa_engine)


class TestSQLModelDefault(BasePaginationTestSuite):
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
    def app(self, builder, query, session):
        @builder.both.default
        def route():
            with session() as db:
                return paginate(db, query)

        return builder.build()


class TestSQLModelRelationship(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, session, sm_user):
        @builder.both.relationship
        def route():
            with session() as db:
                return paginate(db, select(sm_user).options(selectinload(sm_user.orders)))

        return builder.build()
