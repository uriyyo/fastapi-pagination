from typing import Any, Dict

from fastapi import FastAPI, Query
from pytest import fixture

from fastapi_pagination import add_pagination
from fastapi_pagination.iterables import LimitOffsetPage, Page, paginate

from .base import BasePaginationTestCase, SafeTestClient, UserOut
from .utils import faker

app = FastAPI()

entities = [UserOut(name=faker.name()) for _ in range(100)]


@app.get("/default", response_model=Page[UserOut])
@app.get("/limit-offset", response_model=LimitOffsetPage[UserOut])
async def route(skip_len: bool = Query(False)):
    kwargs = {} if skip_len else {"total": len(entities)}

    return paginate((entity for entity in entities), **kwargs)


add_pagination(app)


class TestIterablesPagination(BasePaginationTestCase):
    page = Page
    limit_offset_page = LimitOffsetPage

    _should_normalize_expected = False

    def _normalize_expected(self, result):
        if self._should_normalize_expected:
            result.total = None

        return result

    @fixture(
        params=[True, False],
        ids=["with-len", "without-len"],
    )
    def additional_params(self, request) -> Dict[str, Any]:
        self._should_normalize_expected = request.param
        return {"skip_len": True} if request.param else {}

    @fixture(scope="session")
    def entities(self):
        return entities

    @fixture(scope="session")
    def client(self):
        with SafeTestClient(app) as c:
            yield c
