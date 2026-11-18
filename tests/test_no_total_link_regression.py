import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_pagination import add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseIncludeTotal
from fastapi_pagination.links import Page, UseHeaderLinks

NoTotalPage = CustomizedPage[Page[int], UseIncludeTotal(False)]
NoTotalHeaderPage = CustomizedPage[Page[int], UseIncludeTotal(False), UseHeaderLinks()]
app = FastAPI()


@app.get("/items", response_model=NoTotalPage)
@app.get("/headers", response_model=NoTotalHeaderPage)
def items():
    return paginate(list(range(95)))


@app.get("/exact", response_model=NoTotalPage)
@app.get("/exact-headers", response_model=NoTotalHeaderPage)
def exact_items():
    return paginate(list(range(100)))


add_pagination(app)


def test_full_page_with_unknown_total_has_next_but_no_last():
    response = TestClient(app).get("/items?size=10")
    assert response.status_code == 200
    links = response.json()["links"]
    assert links["next"] == "/items?size=10&page=2"


def test_unknown_total_has_no_last_link():
    response = TestClient(app).get("/items?size=10")
    links = response.json()["links"]
    assert links["last"] is None


@pytest.mark.parametrize(("page", "next_page"), [(1, 2), (2, 3), (10, None), (11, None)])
def test_body_and_header_links(page, next_page):
    params = {"size": 10, "page": page}
    body = TestClient(app).get("/items", params=params)
    assert body.status_code == 200
    links = body.json()["links"]
    assert links["last"] is None
    assert links["next"] == (f"/items?size=10&page={next_page}" if next_page else None)
    assert links["prev"] == (f"/items?size=10&page={page - 1}" if page > 1 else None)
    response = TestClient(app).get("/headers", params=params)
    assert response.status_code == 200
    header = response.headers["link"]
    assert 'rel="last"' not in header
    assert ('rel="next"' in header) == (next_page is not None)


def test_full_final_page_without_total_links_to_one_empty_page():
    client = TestClient(app)
    response = client.get("/exact?size=10&page=10")
    assert response.status_code == 200
    next_link = response.json()["links"]["next"]
    assert next_link == "/exact?size=10&page=11"

    empty = client.get(next_link)
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["links"]["next"] is None

    header = client.get("/exact-headers?size=10&page=10").headers["link"]
    assert '</exact-headers?size=10&page=11>; rel="next"' in header
    empty_header = client.get("/exact-headers?size=10&page=11").headers["link"]
    assert 'rel="next"' not in empty_header
