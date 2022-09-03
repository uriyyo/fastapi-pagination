from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination, paginate

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
