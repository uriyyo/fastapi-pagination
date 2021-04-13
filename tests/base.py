from typing import Type

from fastapi.testclient import TestClient
from pydantic import BaseModel
from pytest import mark

from fastapi_pagination import set_page
from fastapi_pagination.default import Page, Params
from fastapi_pagination.limit_offset import LimitOffsetPage, LimitOffsetParams
from fastapi_pagination.paginator import paginate

from .utils import normalize


class UserOut(BaseModel):
    name: str

    class Config:
        orm_mode = True


_default_params = [
    *[Params(page=i) for i in range(10)],
    *[Params(size=i) for i in range(1, 100, 10)],
    *[Params(page=i, size=j) for i in range(10) for j in range(1, 50, 10)],
]
_limit_offset_params = [
    *[LimitOffsetParams(offset=i) for i in range(10)],
    *[LimitOffsetParams(limit=i) for i in range(1, 100, 10)],
    *[LimitOffsetParams(offset=i, limit=j) for i in range(10) for j in range(1, 50, 10)],
]


class BasePaginationTestCase:
    model: Type[BaseModel] = UserOut

    @mark.parametrize(
        "params,cls,path",
        [
            *[(p, Page, "/default") for p in _default_params],
            *[(p, LimitOffsetPage, "/limit-offset") for p in _limit_offset_params],
        ],
    )
    def test_pagination(self, client, params, entities, cls, path):
        response = client.get(path, params=params.dict())

        set_page(cls)
        expected = paginate(entities, params)

        a, b = normalize(
            cls[self.model],
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


__all__ = ["BasePaginationTestCase", "UserOut", "SafeTestClient"]
