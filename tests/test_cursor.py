import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastapi_pagination import Params, add_pagination, paginate, resolve_params
from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.flow import flow, run_sync_flow
from fastapi_pagination.flows import generic_flow


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


def test_cursor_does_not_mutate_additional_data():
    @flow
    def cursor_flow(raw_params):
        return [1, 2, 3], {"next_": "n"}
        yield

    additional_data = {"x": 1}

    kwargs = run_sync_flow(
        generic_flow(
            cursor_flow=cursor_flow,
            total_flow=lambda: (yield 3),
            params=CursorParams(),
            additional_data=additional_data,
            create_page_factory=lambda items, **kwargs: kwargs,
        )
    )

    assert kwargs["next_"] == "n"
    assert additional_data == {"x": 1}
