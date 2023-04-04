from typing import Iterator, List

from fastapi import Depends, FastAPI, status
from pydantic import parse_obj_as
from pytest import fixture, mark
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage

from ..schemas import UserOut
from .utils import sqlalchemy20

try:
    from fastapi_pagination.ext.sqlalchemy_future import paginate
except ImportError:
    paginate = None


@fixture(scope="session")
def app(sa_user, sa_order, sa_session):
    app = FastAPI()

    def get_db() -> Iterator[Session]:
        with sa_session() as db:
            yield db

    @app.get("/", response_model=CursorPage[UserOut])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).order_by(sa_user.id, sa_user.name))

    return add_pagination(app)


@sqlalchemy20
@mark.asyncio
async def test_cursor(app, client, entities):
    entities = sorted(parse_obj_as(List[UserOut], entities), key=(lambda it: (it.id, it.name)))

    items = []

    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/", params={**params, "size": 10})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items.extend(parse_obj_as(List[UserOut], data["items"]))

        if data["next_page"] is None:
            break

        cursor = data["next_page"]

    assert items == entities

    items = []

    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/", params={**params, "size": 10})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items = parse_obj_as(List[UserOut], data["items"]) + items

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == entities
