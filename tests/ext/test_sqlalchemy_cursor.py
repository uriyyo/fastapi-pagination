from collections.abc import Iterator
from typing import TypeVar

import pytest
from fastapi import Depends, FastAPI, status
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.customization import CustomizedPage, UseQuotedCursor
from fastapi_pagination.ext.sqlalchemy import paginate
from tests.schemas import UserOut
from tests.utils import parse_obj_as

from .utils import sqlalchemy20


@pytest.fixture(scope="session", params=[True, False], ids=["quoted", "unquoted"])
def quoted_cursor(request) -> bool:
    return request.param


@pytest.fixture(scope="session")
def app(sa_user, sa_order, sa_session, quoted_cursor):
    app = FastAPI()

    _T = TypeVar("_T")
    _CursorPage = CustomizedPage[
        CursorPage[_T],
        UseQuotedCursor(quoted_cursor),
    ]

    def get_db() -> Iterator[Session]:
        with sa_session() as db:
            yield db

    @app.get("/", response_model=_CursorPage[UserOut])
    def route(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).order_by(sa_user.id, sa_user.name))

    @app.get("/first-85", response_model=_CursorPage[UserOut])
    def route_first(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).where(sa_user.id <= 85).order_by(sa_user.id, sa_user.name))

    @app.get("/last-85", response_model=_CursorPage[UserOut])
    def route_last(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user).where(sa_user.id > 15).order_by(sa_user.id, sa_user.name))

    @app.get("/no-order", response_model=_CursorPage[UserOut])
    def route_on_order(db: Session = Depends(get_db)):
        return paginate(db, select(sa_user))

    return add_pagination(app)


@sqlalchemy20
@pytest.mark.asyncio(loop_scope="session")
async def test_cursor(app, client, entities):
    entities = sorted(parse_obj_as(list[UserOut], entities), key=(lambda it: (it.id, it.name)))

    items = []

    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get("/", params={**params, "size": 10})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items.extend(parse_obj_as(list[UserOut], data["items"]))

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

        items = parse_obj_as(list[UserOut], data["items"]) + items

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == entities


@sqlalchemy20
@pytest.mark.asyncio(loop_scope="session")
async def test_cursor_refetch(app, client, entities, postgres_url):  # noqa: PLR0915
    entities = sorted(parse_obj_as(list[UserOut], entities), key=(lambda it: (it.id, it.name)))
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

        items.extend(parse_obj_as(list[UserOut], data["items"]))

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

        items.extend(parse_obj_as(list[UserOut], data["items"]))

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

        items = parse_obj_as(list[UserOut], data["items"]) + items

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

        items = parse_obj_as(list[UserOut], data["items"]) + items

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == entities


@sqlalchemy20
@pytest.mark.asyncio(loop_scope="session")
async def test_no_order(app, client, entities):
    with pytest.raises(
        ValueError,
        match="^Cursor pagination requires ordering$",
    ):
        await client.get("/no-order")
