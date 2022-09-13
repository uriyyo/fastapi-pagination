from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import raises

from fastapi_pagination import LimitOffsetParams, add_pagination
from fastapi_pagination.paginator import paginate


def test_params_not_set():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route():
        return paginate([])

    with raises(RuntimeError, match="Use params or add_pagination"):
        client.get("/")


def test_default_page_with_limit_offset():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route(params: LimitOffsetParams = Depends()):
        return paginate([], params)

    add_pagination(app)
    with raises(ValueError, match="Page should be used with Params"):
        client.get("/")
