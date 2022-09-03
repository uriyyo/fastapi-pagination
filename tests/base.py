from typing import Any, ClassVar, Dict, List, Type

from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from pytest import fixture, mark
from pytest_asyncio import fixture as async_fixture

from fastapi_pagination import set_page
from fastapi_pagination.default import Page, Params
from fastapi_pagination.limit_offset import LimitOffsetPage, LimitOffsetParams
from fastapi_pagination.paginator import paginate

from .schemas import UserOut, UserWithOrderOut
from .utils import normalize

_default_params = [
    *[Params(page=i) for i in range(1, 10)],
    *[Params(size=i) for i in range(1, 100, 10)],
    *[Params(page=i, size=j) for i in range(1, 10) for j in range(1, 50, 10)],
]
_limit_offset_params = [
    *[LimitOffsetParams(offset=i) for i in range(1, 10)],
    *[LimitOffsetParams(limit=i) for i in range(1, 100, 10)],
    *[LimitOffsetParams(offset=i, limit=j) for i in range(10) for j in range(1, 50, 10)],
]


@mark.usefixtures("db_type")
class BasePaginationTestCase:
    pagination_types: ClassVar[List[str]] = ["default"]

    page: ClassVar[Type[Page]] = Page
    limit_offset_page: ClassVar[Type[LimitOffsetPage]] = LimitOffsetPage

    def __init_subclass__(cls, **kwargs):
        if cls.pagination_types is not BasePaginationTestCase.pagination_types:
            mark.parametrize("pagination_type", cls.pagination_types, scope="session")(cls)

    @fixture(scope="session")
    def pagination_type(self):
        return "default"

    @fixture
    def path(self, cls_name, pagination_type):
        base = "default" if cls_name == "page" else "limit-offset"

        if pagination_type == "default":
            prefix = "/"
        elif pagination_type == "non-scalar":
            prefix = f"/non-scalar/"
        elif pagination_type == "relationship":
            prefix = f"/relationship/"
        else:
            raise ValueError(f"Unknown suite type {pagination_type}")

        return prefix + base

    @fixture(scope="session")
    def additional_params(self) -> Dict[str, Any]:
        return {}

    @fixture(scope="session")
    def model_cls(self, pagination_type):
        return UserOut

    @fixture(scope="session")
    def model_with_rel_cls(self):
        return UserWithOrderOut

    @fixture(scope="session")
    def result_model_cls(self, model_cls, model_with_rel_cls, pagination_type):
        if pagination_type == "relationship":
            return model_with_rel_cls

        return model_cls

    @mark.parametrize(
        "params,cls_name",
        [
            *[(p, "page") for p in _default_params],
            *[(p, "limit_offset_page") for p in _limit_offset_params],
        ],
    )
    @mark.asyncio
    async def test_pagination(
        self,
        client,
        params,
        entities,
        cls_name,
        additional_params,
        result_model_cls,
        path,
    ):
        response = await client.get(path, params={**params.dict(), **additional_params})
        response.raise_for_status()

        cls = getattr(self, cls_name)

        with set_page(cls):
            expected = self._normalize_expected(paginate(entities, params))

        a, b = normalize(cls[result_model_cls], expected, response.json())
        assert a == b

    def _normalize_expected(self, result):
        return result

    @async_fixture(scope="session")
    async def client(self, app):
        async with LifespanManager(app), AsyncClient(app=app, base_url="http://testserver") as c:
            yield c


__all__ = [
    "BasePaginationTestCase",
]
