from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pytest import mark

from fastapi_pagination import add_pagination, paginate
from fastapi_pagination.links import LimitOffsetPage, Page

app = FastAPI()
client = TestClient(app)


@app.get("/default", response_model=Page[int])
@app.get("/limit-offset", response_model=LimitOffsetPage[int])
async def route():
    return paginate([*range(200)])


@app.get("/default-empty", response_model=Page[int])
async def route():
    return paginate([])


add_pagination(app)


@mark.parametrize(
    "self,prev,next,first,last",
    [
        (
            "/default",
            None,
            "/default?page=2",
            "/default?page=1",
            "/default?page=4",
        ),
        (
            "/default?page=2",
            "/default?page=1",
            "/default?page=3",
            "/default?page=1",
            "/default?page=4",
        ),
        (
            "/default?page=4",
            "/default?page=3",
            None,
            "/default?page=1",
            "/default?page=4",
        ),
        (
            "/default-empty",
            None,
            None,
            "/default-empty?page=1",
            "/default-empty?page=1",
        ),
        (
            "/limit-offset",
            None,
            "/limit-offset?offset=50",
            "/limit-offset?offset=0",
            "/limit-offset?offset=150",
        ),
        (
            "/limit-offset?offset=100",
            "/limit-offset?offset=50",
            "/limit-offset?offset=150",
            "/limit-offset?offset=0",
            "/limit-offset?offset=150",
        ),
        (
            "/limit-offset?offset=150",
            "/limit-offset?offset=100",
            None,
            "/limit-offset?offset=0",
            "/limit-offset?offset=150",
        ),
        (
            "/limit-offset?limit=30&offset=50",
            "/limit-offset?limit=30&offset=20",
            "/limit-offset?limit=30&offset=80",
            "/limit-offset?limit=30&offset=0",
            "/limit-offset?limit=30&offset=170",
        ),
    ],
    ids=[
        "default-first",
        "default-middle",
        "default-last",
        "default-empty",
        "limit-offset-first",
        "limit-offset-middle",
        "limit-offset-last",
        "limit-offset-custom-offset",
    ],
)
def test_links(self, prev, next, first, last):
    response = client.get(self)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["links"] == {
        "self": self,
        "prev": prev,
        "next": next,
        "first": first,
        "last": last,
    }
