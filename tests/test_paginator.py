from fastapi import Depends, FastAPI
from pytest import fixture

from fastapi_pagination import (
    LimitOffsetPage,
    LimitOffsetPaginationParams,
    Page,
    PaginationParams,
)
from fastapi_pagination.paginator import paginate

from .base import (
    BasePaginationTestCase,
    SafeTestClient,
    UserOut,
    limit_offset_params,
    page_params,
)
from .utils import faker

app = FastAPI()

entities = [UserOut(name=faker.name()) for _ in range(100)]


@app.get("/implicit", response_model=Page[UserOut], dependencies=[Depends(page_params)])
def route():
    return paginate(entities)


@app.get("/explicit", response_model=Page[UserOut])
def route(params: PaginationParams = Depends()):
    return paginate(entities, params)


@app.get(
    "/implicit-limit-offset",
    response_model=LimitOffsetPage[UserOut],
    dependencies=[Depends(limit_offset_params)],
)
def route():
    return paginate(entities)


@app.get("/explicit-limit-offset", response_model=LimitOffsetPage[UserOut])
def route(params: LimitOffsetPaginationParams = Depends()):
    return paginate(entities, params)


class TestPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def entities(self):
        return entities

    @fixture(scope="session")
    def client(self):
        with SafeTestClient(app) as c:
            yield c
