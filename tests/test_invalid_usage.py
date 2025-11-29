import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_pagination import LimitOffsetParams, Page, add_pagination
from fastapi_pagination.paginator import paginate


def test_params_not_set():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route():
        return paginate([])

    with pytest.raises(RuntimeError, match=r"Use params, add_pagination or pagination_ctx"):
        client.get("/")


def test_default_page_with_limit_offset():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def route(params: LimitOffsetParams = Depends()) -> Page:
        return paginate([], params)

    add_pagination(app)
    with pytest.raises(TypeError, match=r"Page should be used with Params"):
        client.get("/")
