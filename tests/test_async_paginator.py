from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import (
    LimitOffsetPage,
    Page,
    add_pagination,
)
from fastapi_pagination.async_paginator import paginate

from .base import BasePaginationTestCase
from .utils import OptionalLimitOffsetPage, OptionalPage


class TestAsyncPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def app(self, model_cls, entities):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        @app.get("/optional/default", response_model=OptionalPage[model_cls])
        @app.get("/optional/limit-offset", response_model=OptionalLimitOffsetPage[model_cls])
        async def route():
            return await paginate(entities)

        return add_pagination(app)
