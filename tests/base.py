from dataclasses import asdict
from typing import Type

from fastapi.testclient import TestClient
from pydantic import BaseModel
from pytest import fixture, mark

from fastapi_pagination import Page, PaginationParams, using_page, using_params
from fastapi_pagination.limit_offset import Page as LimitOffsetPage
from fastapi_pagination.limit_offset import (
    PaginationParams as LimitOffsetPaginationParams,
)
from fastapi_pagination.paginator import paginate

from .utils import normalize

page_params = using_params(PaginationParams)
limit_offset_params = using_params(LimitOffsetPaginationParams)


class UserOut(BaseModel):
    name: str

    class Config:
        orm_mode = True


class BasePaginationTestCase:
    model: Type[BaseModel] = UserOut

    path_implicit: str = "/implicit"
    path_explicit: str = "/explicit"

    path_implicit_limit_offset: str = "/implicit-limit-offset"
    path_explicit_limit_offset: str = "/explicit-limit-offset"

    @fixture
    def _limit_offset_page(self):
        with using_page(LimitOffsetPage):
            yield

    @mark.parametrize("path_type", ["implicit", "explicit"])
    @mark.parametrize(
        "params",
        [
            *[PaginationParams(page=i) for i in range(10)],
            *[PaginationParams(size=i) for i in range(1, 100, 10)],
            *[PaginationParams(page=i, size=j) for i in range(10) for j in range(1, 50, 10)],
        ],
        ids=lambda p: f"page-{p.page},size-{p.size}",
    )
    def test_params(self, client, params, entities, path_type):
        response = client.get(getattr(self, f"path_{path_type}"), params=asdict(params))

        expected = paginate(entities, params)

        a, b = normalize(
            Page[self.model],
            self._normalize_model(expected),
            self._normalize_model(response.json()),
        )
        assert a == b

    @mark.parametrize("path_type", ["implicit", "explicit"])
    @mark.parametrize(
        "params",
        [
            *[LimitOffsetPaginationParams(offset=i) for i in range(10)],
            *[LimitOffsetPaginationParams(limit=i) for i in range(1, 100, 10)],
            *[LimitOffsetPaginationParams(offset=i, limit=j) for i in range(10) for j in range(1, 50, 10)],
        ],
        ids=lambda p: f"limit-{p.limit},offset-{p.offset}",
    )
    def test_params_limit_offset(self, client, _limit_offset_page, params, entities, path_type):
        response = client.get(getattr(self, f"path_{path_type}_limit_offset"), params=asdict(params))

        expected = paginate(entities, params)

        a, b = normalize(
            LimitOffsetPage[self.model],
            self._normalize_model(expected),
            self._normalize_model(response.json()),
        )
        assert a == b

    def _normalize_model(self, obj):
        return obj


class SafeTestClient(TestClient):
    def __exit__(self, *args):
        try:
            super().__exit__(*args)
        except BaseException:
            pass


__all__ = ["BasePaginationTestCase", "UserOut", "limit_offset_params", "page_params", "SafeTestClient"]
