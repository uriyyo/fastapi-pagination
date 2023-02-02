from contextlib import suppress
from typing import Any, Dict

from fastapi import FastAPI, Query
from pytest import fixture

from fastapi_pagination import add_pagination
from fastapi_pagination.iterables import LimitOffsetPage, Page, paginate

from .base import BasePaginationTestCase


class TestIterablesPagination(BasePaginationTestCase):
    page = Page
    limit_offset_page = LimitOffsetPage

    _should_normalize_expected = False

    def _normalize_expected(self, result):
        if self._should_normalize_expected:
            result.total = None

            with suppress(ValueError):
                result.pages = None

        return result

    @fixture(
        params=[True, False],
        ids=["with-len", "without-len"],
    )
    def additional_params(self, request) -> Dict[str, Any]:
        self._should_normalize_expected = request.param
        return {"skip_len": True} if request.param else {}

    @fixture(scope="session")
    def app(self, model_cls, entities):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        async def route(skip_len: bool = Query(False)):
            kwargs = {} if skip_len else {"total": len(entities)}

            return paginate((entity for entity in entities), **kwargs)

        return add_pagination(app)
