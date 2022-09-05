from contextlib import suppress

from fastapi import FastAPI
from pony.orm import Database, Required, Set, db_session, select
from pydantic import validator
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.ext.pony import paginate

from ..base import BasePaginationTestCase


@fixture(scope="session")
def pony_db(db_type, database_url, sqlite_file):
    db = Database()

    if db_type == "sqlite":
        db.bind("sqlite", sqlite_file)
    else:
        db.bind(db_type, database_url)

    return db


@fixture(scope="session")
def pony_user(pony_db):
    class User(pony_db.Entity):
        _table_ = "users"

        name = Required(str)
        orders = Set("Order")

    return User


@fixture(scope="session")
def pony_order(pony_db, pony_user):
    class Order(pony_db.Entity):
        _table_ = "orders"

        name = Required(str)
        user_id = Required("User")

    return Order


@fixture(scope="session")
def app(pony_db, pony_user, pony_order, model_cls, model_with_rel_cls):
    app = FastAPI()

    with suppress(Exception):
        pony_db.generate_mapping(create_tables=False)

    class model_pony_with_rel_cls(model_with_rel_cls):
        @validator("orders", pre=True, allow_reuse=True)
        def pony_set_to_list(cls, values):
            if not isinstance(values, list):
                return sorted([v.to_dict() for v in values], key=lambda x: x["id"])

            return values

    @app.get("/default", response_model=Page[model_cls])
    @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
    @app.get("/relationship/default", response_model=Page[model_pony_with_rel_cls])
    @app.get("/relationship/limit-offset", response_model=LimitOffsetPage[model_pony_with_rel_cls])
    def route():
        with db_session:
            return paginate(select(p for p in pony_user))

    return add_pagination(app)


class TestPony(BasePaginationTestCase):
    pagination_types = ["default", "relationship"]
