from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pytest import raises

from fastapi_pagination import add_pagination, paginate, resolve_params
from fastapi_pagination.cursor import CursorPage, CursorParams


def test_unsupported_params():
    with raises(ValueError, match="^'cursor' params not supported$"):
        paginate([1, 2, 3], CursorParams())


def test_invalid_cursor():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/route",
        response_model=CursorPage[int],
    )
    def route():
        params = resolve_params()
        params.to_raw_params()

        return CursorPage(items=[])

    add_pagination(app)

    response = client.get("/route", params={"cursor": "invalid"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid cursor value"}
