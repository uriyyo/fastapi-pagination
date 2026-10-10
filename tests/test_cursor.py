import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastapi_pagination import Params, add_pagination, paginate, resolve_params
from fastapi_pagination.cursor import CursorPage, CursorParams


def test_unsupported_params():
    with pytest.raises(ValueError, match=r"^'cursor' params not supported$"):
        paginate([1, 2, 3], CursorParams())


def test_cursor_page_invalid_params_type():
    with pytest.raises(TypeError, match=r"^CursorPage should be used with CursorParams$"):
        CursorPage[int].create(
            items=[1, 2, 3],
            total=3,
            params=Params(),
        )


@pytest.mark.parametrize(
    "cursor",
    ["invalid", "null"],
)
def test_invalid_cursor(cursor):
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/route",
        response_model=CursorPage[int],
    )
    def route():
        params = resolve_params()
        params.to_raw_params()

        return CursorPage(items=[], total=0)

    add_pagination(app)

    response = client.get("/route", params={"cursor": cursor})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid cursor value"}


@pytest.mark.parametrize(
    ("size", "status_code"),
    [
        (0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, status.HTTP_200_OK),
    ],
)
def test_cursor_params_size_min(size, status_code):
    app = FastAPI()
    client = TestClient(app)

    @app.get("/route", response_model=CursorPage[int])
    def route():
        return CursorPage(items=[], total=0)

    add_pagination(app)

    assert client.get("/route", params={"size": size}).status_code == status_code
