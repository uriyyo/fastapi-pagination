from collections.abc import Iterator

import pytest
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fastapi_pagination.ext.sqlalchemy import paginate
from tests.base import BasePaginationTestSuite

from .utils import sqlalchemy20


@sqlalchemy20
class TestSQLAlchemyFuture(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_order, sa_session):
        def get_db() -> Iterator[Session]:
            with sa_session() as db:
                yield db

        @builder.both.default
        def route_1(db: Session = Depends(get_db)):
            return paginate(db, select(sa_user))

        @builder.both.relationship
        def route_2(db: Session = Depends(get_db)):
            return paginate(db, select(sa_user).options(selectinload(sa_user.orders)))

        @builder.both.non_scalar
        def route_3(db: Session = Depends(get_db)):
            return paginate(db, select(sa_user.id, sa_user.name))

        return builder.build()
