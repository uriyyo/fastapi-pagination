import sys
from contextlib import suppress

import pytest
from pony.orm import Database, Required, Set, db_session, select
from sqlalchemy.engine.url import make_url

from fastapi_pagination.ext.pony import paginate
from fastapi_pagination.pydantic import IS_PYDANTIC_V2
from tests.base import BasePaginationTestSuite


@pytest.fixture(scope="session")
def pony_db(db_type, database_url, sqlite_file):
    db = Database()

    if db_type == "sqlite":
        db.bind("sqlite", sqlite_file)
    else:
        url = make_url(database_url)
        db.bind(
            "postgres",
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port,
            database=url.database,
        )

    return db


@pytest.fixture(scope="session")
def pony_user(pony_db):
    class User(pony_db.Entity):
        _table_ = "users"

        name = Required(str)
        orders = Set("Order")

    return User


@pytest.fixture(scope="session")
def pony_order(pony_db, pony_user):
    class Order(pony_db.Entity):
        _table_ = "orders"

        name = Required(str)
        user_id = Required("User")

    return Order


if IS_PYDANTIC_V2:
    from pydantic import field_validator

    _field_validator = field_validator("orders", mode="before")
else:
    from pydantic import validator

    _field_validator = validator("orders", pre=True, allow_reuse=True)


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="skip pony tests for python 3.11",
)
class TestPony(BasePaginationTestSuite):
    @pytest.fixture(scope="session")
    def app(self, builder, pony_db, pony_user, pony_order):
        with suppress(Exception):
            pony_db.generate_mapping(create_tables=False)

        class PonyModelWithRel(builder.classes.model_with_rel):
            @_field_validator
            def pony_set_to_list(cls, values):
                if not isinstance(values, list):
                    return sorted([v.to_dict() for v in values], key=lambda x: x["id"])

                return values

        builder = builder.classes.update(model_with_rel=PonyModelWithRel)

        @builder.both.default.relationship
        def route():
            with db_session:
                return paginate(select(p for p in pony_user))

        return builder.build()
