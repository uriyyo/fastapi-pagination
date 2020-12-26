from asyncio import create_task
from typing import Generic, TypeVar

from fastapi import Depends, FastAPI, Response
from fastapi.testclient import TestClient
from pytest import mark

from fastapi_pagination import PaginationParams, paginate
from fastapi_pagination.api import (
    create_page,
    response,
    use_as_page,
    using_response,
)
from fastapi_pagination.page import BasePage


def test_set_response():
    app = FastAPI()
    client = TestClient(app)

    @app.get("/", dependencies=[Depends(using_response)])
    async def route(res: Response):
        assert res is response()
        return {}

    client.get("/")

    @app.get("/no-response")
    async def route(res: Response):
        assert response() is None
        return {}

    client.get("/no-response")


@mark.asyncio
async def test_use_as_page():
    async def _use_as_page():
        T = TypeVar("T")

        @use_as_page
        class CustomPage(BasePage[T], Generic[T]):
            @classmethod
            def create(cls, items, total, params):
                return cls(
                    items=items,
                    total=total,
                )

        page = paginate([1, 2, 3], PaginationParams(0, 50))
        assert isinstance(page, CustomPage)
        assert page.items == [1, 2, 3]
        assert page.total == 3

    await create_task(_use_as_page())
