from collections.abc import Iterator
from contextlib import closing
from typing import Any

import pytest
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.sqlalchemy import paginate
from tests.base import BasePaginationTestSuite
from tests.schemas import UserOut, UserWithoutIDOut

from .utils import is_sqlalchemy20, sqlalchemy20


@pytest.fixture(
    scope="session",
    params=[True, False],
    ids=["subquery_count", "no_subquery_count"],
)
def use_subquery_count(request):
    if request.param and not is_sqlalchemy20:
        pytest.skip("subquery_count is not supported for SQLAlchemy<2.0")

    return request.param


@sqlalchemy20
class TestSQLAlchemy(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, sa_user, sa_session, use_subquery_count):
        def get_db() -> Iterator[Session]:
            with closing(sa_session()) as db:
                yield db

        @builder.both.default
        def route(db: Session = Depends(get_db)):
            return paginate(db, select(sa_user), subquery_count=use_subquery_count)

        return builder.build()

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
