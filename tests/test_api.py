from typing import Any

from fastapi import Depends, FastAPI, Response
from fastapi.routing import APIRouter
from fastapi.testclient import TestClient

from fastapi_pagination import Page, add_pagination, paginate, response


def test_set_response():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/",
        response_model=Page[int],
    )
    async def route(res: Response):
        assert res is response()
        return paginate([])

    add_pagination(app)
    client.get("/")


def test_add_pagination():
    app = FastAPI()

    @app.get("/first")
    async def route():
        pass

    @app.get(
        "/second",
        response_model=Page[int],
    )
    async def route():
        pass

    *_, r1, r2 = app.routes

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 0

    add_pagination(app)

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 4

    add_pagination(app)

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 4


def test_add_pagination_include_router():
    router1 = APIRouter()

    @router1.get(
        "/first",
        response_model=Page[int],
    )
    async def route():
        pass

    (r1,) = router1.routes
    assert len(r1.dependencies) == 0

    add_pagination(router1)

    assert len(r1.dependencies) == 4

    router2 = APIRouter()

    @router2.get(
        "/second",
        response_model=Page[int],
    )
    async def route():
        pass

    (r2,) = router2.routes
    assert len(r2.dependencies) == 0

    app = FastAPI()
    app.include_router(router1)
    app.include_router(router2)

    *_, r1, r2 = app.routes

    assert len(r1.dependencies) == 4
    assert len(r2.dependencies) == 0

    add_pagination(app)

    assert len(r1.dependencies) == 4
    assert len(r2.dependencies) == 4


def test_add_pagination_additional_dependencies():
    app = FastAPI()

    async def dep():
        pass

    @app.get(
        "/",
        response_model=Page[int],
        dependencies=[Depends(dep)],
    )
    async def route(_: Any = Depends(dep)):
        pass

    *_, r = app.routes
    assert len(r.dependencies) == 1
    assert len(r.dependant.dependencies) == 2

    add_pagination(app)

    assert len(r.dependencies) == 5
    assert len(r.dependant.dependencies) == 6
