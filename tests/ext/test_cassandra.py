from typing import List

from cassandra.cqlengine import columns, connection, management, models
from fastapi import FastAPI, status
from pydantic import parse_obj_as
from pytest import fixture, mark

from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage as BaseCursorPage

from ..schemas import UserOut

try:
    from fastapi_pagination.ext.cassandra import paginate
except ImportError:
    paginate = None

CursorPage = BaseCursorPage.with_custom_options(str_cursor=False)


class User(models.Model):
    __keyspace__ = "ks"

    group = columns.Text(partition_key=True)
    id = columns.Integer(primary_key=True)
    name = columns.Text()


@fixture(scope="session")
def app(cassandra_session, raw_data):

    connection.register_connection("cluster1", session=cassandra_session, default=True)
    management.sync_table(model=User, keyspaces=("ks",))

    users = [User(group="GC", id=user.get("id"), name=user.get("name")) for user in raw_data]
    for user in users:
        user.save()

    app = FastAPI()

    @app.get("/", response_model=CursorPage[UserOut])
    def route():
        return paginate(User.objects().order_by("id").allow_filtering(), query_filter=dict(group="GC"))

    return add_pagination(app)


@mark.asyncio
async def test_cursor(app, client, entities):
    entities = sorted(parse_obj_as(List[UserOut], entities), key=(lambda it: (it.id, it.name)))

    items = []

    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get(f"/", params={**params, "size": 10})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items.extend(parse_obj_as(List[UserOut], data["items"]))

        if data["next_page"] is None:
            break

        cursor = data["next_page"]

    assert items == entities

    """
    backwards paging doesn't work out of the box
    it's on the client to save those pages states

    items = []

    while True:
        params = {"cursor": cursor} if cursor else {}

        resp = await client.get(f"/", params={**params, "size": 10})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        items = parse_obj_as(List[UserOut], data["items"]) + items

        if data["previous_page"] is None:
            break

        cursor = data["previous_page"]

    assert items == entities
    """
