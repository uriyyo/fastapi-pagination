from fastapi import FastAPI
from pytest import fixture

from fastapi_pagination import LimitOffsetPage, Page, add_pagination, paginate

from .base import BasePaginationTestCase, SafeTestClient, UserOut
from .utils import faker

app = FastAPI()

entities = [UserOut(name=faker.name()) for _ in range(100)]


@app.get("/default", response_model=Page[UserOut])
@app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
async def route():
    return paginate(entities)


add_pagination(app)


class TestPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def entities(self):
        return entities

    @fixture(scope="session")
    def client(self):
        with SafeTestClient(app) as c:
            yield c
