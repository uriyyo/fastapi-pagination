from typing import Generic, TypeVar

from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import (
    LimitOffsetPage,
    Page,
    Params,
    add_pagination,
    paginate,
    set_page,
)

from .base import BasePaginationTestCase


class TestPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def app(self, model_cls, entities):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        async def route():
            return paginate(entities)

        return add_pagination(app)


T = TypeVar("T")


class CustomPage(Page[T], Generic[T]):
    new_field: int


def test_paginator_additional_data():
    with set_page(CustomPage):
        page = paginate([], Params(), additional_data={"new_field": 10})

    assert page == CustomPage(items=[], total=0, page=1, pages=0, size=50, new_field=10)
