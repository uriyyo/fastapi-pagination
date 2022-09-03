from functools import partial
from itertools import count

from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination, paginate

from .base import BasePaginationTestCase, UserOut
from .utils import faker

id_seq = partial(next, iter(count(1)))

entities = [UserOut(id=id_seq(), name=faker.name()) for _ in range(100)]


class TestPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def entities(self):
        return entities

    @fixture(scope="session")
    def app(self, model_cls):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        async def route():
            return paginate(entities)

        add_pagination(app)
        return app
