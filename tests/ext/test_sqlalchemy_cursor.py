from typing import Iterator, List

from _pytest.python_api import raises
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

    @app.get("/first-85", response_model=CursorPage[UserOut])
    def route_first(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).where(sa_user.id <= 85).order_by(sa_user.id, sa_user.name))

    @app.get("/last-85", response_model=CursorPage[UserOut])
    def route_last(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).where(sa_user.id > 15).order_by(sa_user.id, sa_user.name))

    @app.get("/no-order", response_model=CursorPage[UserOut])
    def route_on_order(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user))

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


@sqlalchemy20
@mark.asyncio
async def test_cursor_refetch(app, client, entities, postgres_url):
    entities = sorted(parse_obj_as(List[UserOut], entities), key=(lambda it: (it.id, it.name)))
    first_85_entities = entities[:85]
    last_85_entities = entities[15:]

    items = []
    page_size = 10
    cursor = None

    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/first-85", params={**params, "size": page_size})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items.extend(parse_obj_as(List[UserOut], data["items"]))

        current = data["current_page"]

        if data["next_page"] is None:
            break

        cursor = data["next_page"]

    assert items == first_85_entities

    items = items[:80]

    cursor = current

    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/", params={**params, "size": page_size})
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

        resp = await client.get("/last-85", params={**params, "size": page_size})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items = parse_obj_as(List[UserOut], data["items"]) + items

        current = data["current_page_backwards"]

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == last_85_entities

    items = items[5:]

    cursor = current

    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/", params={**params, "size": page_size})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items = parse_obj_as(List[UserOut], data["items"]) + items

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == entities


@sqlalchemy20
@mark.asyncio
async def test_no_order(app, client, entities):
    with raises(
        ValueError,
        match="^Cursor pagination requires ordering$",
    ):
        await client.get("/no-order")
