from typing import Any, ClassVar, Dict, Type

from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from pydantic import BaseModel
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture

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
    *[Params(page=i) for i in range(1, 10)],
    *[Params(size=i) for i in range(1, 100, 10)],
    *[Params(page=i, size=j) for i in range(1, 10) for j in range(1, 50, 10)],
]
_limit_offset_params = [
    *[LimitOffsetParams(offset=i) for i in range(10)],
    *[LimitOffsetParams(limit=i) for i in range(1, 100, 10)],
    *[LimitOffsetParams(offset=i, limit=j) for i in range(10) for j in range(1, 50, 10)],
]


class BasePaginationTestCase:
    page: ClassVar[Type[Page]] = Page
    limit_offset_page: ClassVar[Type[LimitOffsetPage]] = LimitOffsetPage

    @fixture(scope="session")
    def additional_params(self) -> Dict[str, Any]:
        return {}

    @fixture(scope="session")
    def model_cls(self):
        return UserOut

    @mark.parametrize(
        "params,cls_name,path",
        [
            *[(p, "page", "/default") for p in _default_params],
            *[(p, "limit_offset_page", "/limit-offset") for p in _limit_offset_params],
        ],
    )
    @mark.asyncio
    async def test_pagination(
        self,
        clear_database,
        client,
        params,
        entities,
        cls_name,
        path,
        additional_params,
        model_cls,
    ):
        response = await client.get(path, params={**params.dict(), **additional_params})

        cls = getattr(self, cls_name)
        set_page(cls)

        expected = self._normalize_expected(paginate(entities, params))

        a, b = normalize(
            cls[model_cls],
            self._normalize_model(expected),
            self._normalize_model(response.json()),
        )
        assert a == b

    def _normalize_expected(self, result):
        return result

    def _normalize_model(self, obj):
        return obj

    @async_fixture(scope="session")
    async def client(self, app):
        async with LifespanManager(app), AsyncClient(app=app, base_url="http://testserver") as c:
            yield c


__all__ = ["BasePaginationTestCase", "UserOut"]
