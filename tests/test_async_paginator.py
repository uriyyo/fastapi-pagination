import pytest
from fastapi import FastAPI

from fastapi_pagination import (
    LimitOffsetPage,
    Page,
    add_pagination,
)
from fastapi_pagination.async_paginator import paginate

from .base import BasePaginationTestCase
from .utils import OptionalLimitOffsetPage, OptionalPage


async def _len_func(seq):
    return len(seq)


class TestAsyncPaginationParams(BasePaginationTestCase):
    @pytest.fixture(scope="session", params=[len, _len_func], ids=["sync", "async"])
    def len_function(self, request):
        return request.param

    @pytest.fixture(scope="session")
    def app(self, model_cls, entities, len_function):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        @app.get("/optional/default", response_model=OptionalPage[model_cls])
        @app.get("/optional/limit-offset", response_model=OptionalLimitOffsetPage[model_cls])
        async def route():
            return await paginate(entities, length_function=len_function)

        return add_pagination(app)
