from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from fastapi_pagination import Page, add_pagination, paginate, response


def test_set_response():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/", response_model=Page[int])
    async def route(res: Response):
        assert res is response()
        return paginate([])

    add_pagination(app)
    client.get("/")
