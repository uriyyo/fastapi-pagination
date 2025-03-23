from typing import Any

import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastapi_pagination import add_pagination, paginate, pagination_ctx
from fastapi_pagination.customization import CustomizedPage
from fastapi_pagination.links import LimitOffsetPage, Page, UseHeaderLinks, UseLimitOffsetHeaderLinks

app = FastAPI()
client = TestClient(app)

PageDefaultLinks = CustomizedPage[
    Page,
    UseHeaderLinks(),
]

PageLimitOffsetHeaderLinks = CustomizedPage[
    LimitOffsetPage,
    UseLimitOffsetHeaderLinks(),
]


@app.get("/default", response_model=Page[int])
@app.get("/limit-offset", response_model=LimitOffsetPage[int])
@app.get("/default-header-links", response_model=PageDefaultLinks[int])
@app.get("/limit-offset-header-links", response_model=PageLimitOffsetHeaderLinks[int])
async def route_1():
    return paginate([*range(200)])


@app.get("/default-empty", response_model=Page[int])
@app.get("/default-header-links-empty", response_model=PageDefaultLinks[int])
async def route_2():
    return paginate([])


class MySchemaPage(BaseModel):
    page: Page[Any]


class MySchemaLimitOffset(BaseModel):
    page: LimitOffsetPage[Any]


@app.get(
    "/revalidate/default",
    dependencies=[Depends(pagination_ctx(Page[int]))],
    response_model=MySchemaPage,
)
@app.get(
    "/revalidate/limit-offset",
    dependencies=[Depends(pagination_ctx(LimitOffsetPage[int]))],
    response_model=MySchemaLimitOffset,
)
async def route_3():
    page = paginate([*range(10)])
    return {"page": page}


add_pagination(app)


@pytest.mark.parametrize(
    ("self", "prev", "next", "first", "last"),
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
def test_links(self, prev, next, first, last):  # noqa: A002
    response = client.get(self)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["links"] == {
        "self": self,
        "prev": prev,
        "next": next,
        "first": first,
        "last": last,
    }


@pytest.mark.parametrize(
    ("self", "prev", "next", "first", "last"),
    [
        (
            "/default-header-links",
            None,
            "/default-header-links?page=2",
            "/default-header-links?page=1",
            "/default-header-links?page=4",
        ),
        (
            "/default-header-links?page=2",
            "/default-header-links?page=1",
            "/default-header-links?page=3",
            "/default-header-links?page=1",
            "/default-header-links?page=4",
        ),
        (
            "/default-header-links?page=4",
            "/default-header-links?page=3",
            None,
            "/default-header-links?page=1",
            "/default-header-links?page=4",
        ),
        (
            "/default-header-links-empty",
            None,
            None,
            "/default-header-links-empty?page=1",
            "/default-header-links-empty?page=1",
        ),
        (
            "/limit-offset-header-links",
            None,
            "/limit-offset-header-links?offset=50",
            "/limit-offset-header-links?offset=0",
            "/limit-offset-header-links?offset=150",
        ),
        (
            "/limit-offset-header-links?offset=100",
            "/limit-offset-header-links?offset=50",
            "/limit-offset-header-links?offset=150",
            "/limit-offset-header-links?offset=0",
            "/limit-offset-header-links?offset=150",
        ),
        (
            "/limit-offset-header-links?offset=150",
            "/limit-offset-header-links?offset=100",
            None,
            "/limit-offset-header-links?offset=0",
            "/limit-offset-header-links?offset=150",
        ),
        (
            "/limit-offset-header-links?limit=30&offset=50",
            "/limit-offset-header-links?limit=30&offset=20",
            "/limit-offset-header-links?limit=30&offset=80",
            "/limit-offset-header-links?limit=30&offset=0",
            "/limit-offset-header-links?limit=30&offset=170",
        ),
    ],
    ids=[
        "default-header-links-first",
        "default-header-links-middle",
        "default-header-links-last",
        "default-header-links-empty",
        "limit-offset-header-links-first",
        "limit-offset-header-links-middle",
        "limit-offset-header-links-last",
        "limit-offset-header-links-custom-offset",
    ],
)
def test_header_links(self, prev, next, first, last):  # noqa: A002
    parts = []
    if first:
        parts.append(f'<{first}>; rel="first"')
    if last:
        parts.append(f'<{last}>; rel="last"')
    if next:
        parts.append(f'<{next}>; rel="next"')
    if prev:
        parts.append(f'<{prev}>; rel="prev"')

    response = client.get(self)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("link") is not None
    assert response.headers.get("link") == ", ".join(parts)


def test_revalidation_default():
    response = client.get("/revalidate/default")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "page": {
            "items": [*range(10)],
            "total": 10,
            "page": 1,
            "size": 50,
            "pages": 1,
            "links": {
                "first": "/revalidate/default?page=1",
                "last": "/revalidate/default?page=1",
                "self": "/revalidate/default",
                "next": None,
                "prev": None,
            },
        },
    }


def test_revalidation_limit_offset():
    response = client.get("/revalidate/limit-offset")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "page": {
            "items": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "total": 10,
            "limit": 50,
            "offset": 0,
            "links": {
                "first": "/revalidate/limit-offset?offset=0",
                "last": "/revalidate/limit-offset?offset=0",
                "self": "/revalidate/limit-offset",
                "next": None,
                "prev": None,
            },
        },
    }
