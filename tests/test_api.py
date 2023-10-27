from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Generic, Sequence, TypeVar

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.routing import APIRouter
from fastapi.testclient import TestClient
from pydantic import Field
from pytest import fixture

try:
    from pydantic.generics import GenericModel
except ImportError:  # pragma: no cover
    from pydantic import BaseModel as GenericModel

from pytest import raises

from fastapi_pagination import (
    Page,
    Params,
    add_pagination,
    paginate,
    request,
    response,
)
from fastapi_pagination.api import apply_items_transformer, create_page, pagination_ctx, pagination_items
from fastapi_pagination.bases import AbstractPage


def test_set_response_request():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/",
        response_model=Page[int],
    )
    async def route(req: Request, res: Response):
        assert res is response()
        assert req is request()

        return paginate([])

    add_pagination(app)
    client.get("/")


def test_get_empty_response_request():
    with raises(RuntimeError, match=r"^response context var must be set$"):
        response()

    with raises(RuntimeError, match=r"^request context var must be set$"):
        request()


def test_add_pagination():
    app = FastAPI()

    @app.get("/first")
    async def route_1():
        pass

    @app.get(
        "/second",
        response_model=Page[int],
    )
    async def route_2():
        pass

    *_, r1, r2 = app.routes

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 0

    add_pagination(app)

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 1

    add_pagination(app)

    assert len(r1.dependencies) == 0
    assert len(r2.dependencies) == 1


def test_add_pagination_include_router():
    router1 = APIRouter()

    @router1.get(
        "/first",
        response_model=Page[int],
    )
    async def route_1():
        pass

    (r1,) = router1.routes
    assert len(r1.dependencies) == 0

    add_pagination(router1)

    assert len(r1.dependencies) == 1

    router2 = APIRouter()

    @router2.get(
        "/second",
        response_model=Page[int],
    )
    async def route_2():
        pass

    (r2,) = router2.routes
    assert len(r2.dependencies) == 0

    app = FastAPI()
    app.include_router(router1)
    app.include_router(router2)

    *_, r1, r2 = app.routes

    assert len(r1.dependencies) == 1
    assert len(r2.dependencies) == 0

    add_pagination(app)

    assert len(r1.dependencies) == 1
    assert len(r2.dependencies) == 1


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

    assert len(r.dependencies) == 2
    assert len(r.dependant.dependencies) == 3


def test_pagination_items_outside_create_page():
    with raises(
        RuntimeError,
        match=r"^pagination_items must be called inside create_page$",
    ):
        pagination_items()


def test_create_page_duplicate_params():
    with raises(TypeError):
        create_page([], 1, Params(), total=0)

    with raises(TypeError):
        create_page([], 1, Params(), params=None)


T = TypeVar("T")


def test_pagination_items():
    app = FastAPI()
    client = TestClient(app)

    class InnerModel(GenericModel, Generic[T]):
        items: Sequence[T] = Field(default_factory=pagination_items)

    class CustomPage(AbstractPage[T], Generic[T]):
        inner: InnerModel[T]

        __params_type__ = Params

        @classmethod
        def create(cls, items, total, params):
            return cls.parse_obj({"inner": {}})

    @app.get(
        "/",
        response_model=CustomPage[int],
    )
    async def route():
        return paginate([1, 2, 3])

    add_pagination(app)

    rsp = client.get("/")
    assert rsp.json() == {"inner": {"items": [1, 2, 3]}}


def test_items_transformer():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/explicit",
        response_model=Page[int],
    )
    async def route1():
        return paginate([1, 2, 3], transformer=lambda items: [i * 2 for i in items])

    @app.get(
        "/implicit",
        response_model=Page[int],
        dependencies=[
            Depends(pagination_ctx(transformer=lambda items: [i * 2 for i in items])),
        ],
    )
    async def route2():
        return paginate([1, 2, 3])

    add_pagination(app)

    rsp = client.get("/explicit")
    assert rsp.json() == {"items": [2, 4, 6], "total": 3, "page": 1, "pages": 1, "size": 50}

    rsp = client.get("/implicit")
    assert rsp.json() == {"items": [2, 4, 6], "total": 3, "page": 1, "pages": 1, "size": 50}


def test_apply_items_transformer_sync_with_async_transformer():
    async def async_transformer(items):
        return [i * 2 for i in items]

    with raises(
        ValueError,
        match=r"^apply_items_transformer called with async_=False but transformer is async$",
    ):
        apply_items_transformer([], async_transformer, async_=False)


def test_no_exception_on_validation_error():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/",
        response_model=Page[int],
    )
    async def route():
        return paginate([])

    add_pagination(app)

    rsp = client.get("/", params={"page": -1})
    assert rsp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLifespan:
    @fixture(scope="class")
    def app(self):
        @asynccontextmanager
        async def lifespan(_: Any) -> AsyncIterator[None]:
            app.state.called = True
            yield

        app = FastAPI(lifespan=lifespan)

        @app.get(
            "/",
            response_model=Page[int],
        )
        async def route():
            return paginate([])

        add_pagination(app)
        app.state.called = False

        return app

    async def test_lifespan_wrap(self, app, client):
        rsp = await client.get("/")
        assert rsp.status_code == status.HTTP_200_OK

        assert app.state.called, "original lifespan not called"
