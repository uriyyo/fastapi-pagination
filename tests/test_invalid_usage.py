from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pytest import raises

from fastapi_pagination.limit_offset import PaginationParams
from fastapi_pagination.paginator import paginate


def test_params_not_set():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route():
        return paginate([])

    with raises(RuntimeError, match="Use explicit params or pagination dependency"):
        client.get("/")


def test_default_page_with_limit_offset():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route(params: PaginationParams = Depends()):
        return paginate([], params)

    with raises(ValueError, match="Page should be used with PaginationParams"):
        client.get("/")
