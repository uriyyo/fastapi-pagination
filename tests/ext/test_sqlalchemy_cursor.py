from typing import TypeVar

import pytest
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import set_page, set_params
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.customization import CustomizedPage, UseQuotedCursor
from fastapi_pagination.ext.sqlalchemy import paginate
from tests.base import BasePaginationTestSuite, SuiteBuilder
from tests.schemas import UserOut


class TestSQLAlchemyCursor(BasePaginationTestSuite):
    @pytest.fixture(
        scope="session",
        params=[True, False],
        ids=["quoted", "unquoted"],
    )
    def quoted_cursor(self, request) -> bool:
        return request.param

    @pytest.fixture(scope="session")
    def builder(self, quoted_cursor) -> SuiteBuilder:
        _T = TypeVar("_T")
        _CursorPage = CustomizedPage[
            CursorPage[_T],
            UseQuotedCursor(quoted_cursor),
        ]

        return SuiteBuilder.with_classes(cursor=_CursorPage)

    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_order, sa_session, sm_session_ctx):
        @builder.cursor.default
        def route(db: Session = Depends(sm_session_ctx)):
            return paginate(db, select(sa_user).order_by(sa_user.id))

        return builder.build()

    def test_no_order(self, sa_session, sa_user):
        with (
            pytest.raises(ValueError, match=r"^Cursor pagination requires ordering$"),
            set_page(CursorPage[UserOut]),
            set_params(CursorPage.__params_type__()),
        ):
            paginate(sa_session(), select(sa_user))
