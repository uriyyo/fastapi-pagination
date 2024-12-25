from collections.abc import Iterator
from contextlib import closing

import pytest
from fastapi import Depends
from sqlalchemy import select, text
from sqlalchemy.orm.session import Session

from fastapi_pagination.ext.sqlalchemy import paginate
from tests.base import BasePaginationTestSuite, add_cases


@add_cases("optional")
class TestSQLAlchemyFromStatement(BasePaginationTestSuite):
    is_async = False

    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_session):
        def get_db() -> Iterator[Session]:
            with closing(sa_session()) as db:
                yield db

        @builder.both.default.optional
        def route(db: Session = Depends(get_db)):
            return paginate(db, select(sa_user).from_statement(text("SELECT * FROM users")))

        return builder.build()
