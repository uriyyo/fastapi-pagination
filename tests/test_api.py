from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated, Any, Generic, TypeVar

import pytest
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.routing import APIRouter
from fastapi.testclient import TestClient
from pydantic import Field

from fastapi_pagination.cursor import CursorPage, CursorParams
from fastapi_pagination.errors import UninitializedConfigurationError

try:
    from pydantic.generics import GenericModel
except ImportError:  # pragma: no cover
    from pydantic import BaseModel as GenericModel

from fastapi_pagination import (
    LimitOffsetPage,
    LimitOffsetParams,
    Page,
    Params,
    add_pagination,
    paginate,
    request,
    response,
)
from fastapi_pagination.api import (
    apply_items_transformer,
    create_page,
    pagination_ctx,
    pagination_items,
    resolve_page,
    set_page,
)
from fastapi_pagination.bases import AbstractPage, AbstractParams, BaseRawParams, RawParams


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
    with pytest.raises(RuntimeError, match=r"^response context var must be set$"):
        response()

    with pytest.raises(RuntimeError, match=r"^request context var must be set$"):
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


def test_page_resolve_from_params_val() -> None:
    assert resolve_page(Params()) is Page
    assert resolve_page(LimitOffsetParams()) is LimitOffsetPage
    assert resolve_page(CursorParams()) is CursorPage


def test_page_resolve_set_page() -> None:
    class CustomPage(AbstractPage[int]):
        pass

    with set_page(CustomPage):
        assert resolve_page(Params()) is CustomPage
        assert resolve_page(LimitOffsetParams()) is CustomPage
        assert resolve_page(CursorParams()) is CustomPage


def test_resolve_page_no_page_set() -> None:
    with pytest.raises(UninitializedConfigurationError):
        resolve_page()

    class _UnconnectedParams(AbstractParams):
        def to_raw_params(self) -> BaseRawParams:
            return RawParams()

    with pytest.raises(UninitializedConfigurationError):
        resolve_page(_UnconnectedParams())


def test_pagination_items_outside_create_page():
    with pytest.raises(
        RuntimeError,
        match=r"^pagination_items must be called inside create_page$",
    ):
        pagination_items()


def test_create_page_duplicate_params():
    with pytest.raises(TypeError):
        create_page([], 1, Params(), total=0)

    with pytest.raises(TypeError):
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

    with pytest.raises(
        ValueError,
        match=r"^apply_items_transformer called with async_=False but transformer is async$",
    ):
        apply_items_transformer([], async_transformer, async_=False)


@pytest.mark.asyncio(loop_scope="session")
async def test_async_items_transformer():
    async def async_transformer(items):
        return [i * 2 for i in items]

    assert await apply_items_transformer([1, 2, 3], async_transformer, async_=True) == [2, 4, 6]


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


def test_unwrap_annotated():
    app = FastAPI()
    client = TestClient(app)

    @app.get(
        "/",
        response_model=Annotated[Page[int], "my-metadata"],
    )
    async def route():
        return paginate([])

    add_pagination(app)

    rsp = client.get("/")
    assert rsp.status_code == status.HTTP_200_OK


class TestLifespan:
    @pytest.fixture(scope="class")
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

    @pytest.mark.asyncio(loop_scope="session")
    async def test_lifespan_wrap(self, app, client):
        rsp = await client.get("/")
        assert rsp.status_code == status.HTTP_200_OK

        assert app.state.called, "original lifespan not called"


class TestPatchOpenAPI:
    @pytest.fixture(scope="class")
    def app(self):
        app = FastAPI()
        app.openapi()["info"]["title"] = "Custom Title"

        @app.get(
            "/",
            response_model=Page[int],
        )
        async def route():
            return paginate([])

        add_pagination(app)

        return app

    @pytest.mark.asyncio(loop_scope="session")
    async def test_patch_openapi(self, app, client):
        rsp = await client.get("/openapi.json")
        assert rsp.status_code == status.HTTP_200_OK

        data = rsp.json()
        assert data["info"]["title"] == "Custom Title"
