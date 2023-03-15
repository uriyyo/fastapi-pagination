from typing import Any, ClassVar, Dict, List, Type

from pytest import fixture, mark

from fastapi_pagination import set_page
from fastapi_pagination.default import Page, Params
from fastapi_pagination.limit_offset import LimitOffsetPage, LimitOffsetParams
from fastapi_pagination.paginator import paginate

from .schemas import UserOut, UserWithOrderOut
from .utils import normalize, OptionalPage, OptionalLimitOffsetPage

_default_params = [
    Params(page=1),
    Params(page=2),
    Params(page=3),
    Params(size=100),
    Params(page=1, size=10),
    Params(page=9, size=10),
    Params(page=10, size=10),
    Params(page=2, size=25),
    Params(size=31),
]
_limit_offset_params = [
    LimitOffsetParams(limit=50),
    LimitOffsetParams(limit=50, offset=50),
    LimitOffsetParams(limit=50, offset=100),
    LimitOffsetParams(limit=100),
    LimitOffsetParams(limit=10),
    LimitOffsetParams(limit=10, offset=80),
    LimitOffsetParams(limit=10, offset=90),
    LimitOffsetParams(limit=25, offset=25),
    LimitOffsetParams(limit=31),
]
_params_desc = [
    "first",
    "second",
    "third-empty",
    "full-page",
    "first-10-items",
    "last-10-items",
    "after-last-10-items-empty",
    "second-25-items",
    "31-items",
]


@mark.usefixtures("db_type")
class BasePaginationTestCase:
    pagination_types: ClassVar[List[str]] = ["default"]

    page: ClassVar[Type[Page]] = Page
    limit_offset_page: ClassVar[Type[LimitOffsetPage]] = LimitOffsetPage

    optional_page: ClassVar[Type[Page]] = OptionalPage
    optional_limit_offset_page: ClassVar[Type[LimitOffsetPage]] = OptionalLimitOffsetPage

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
            prefix = "/non-scalar/"
        elif pagination_type == "relationship":
            prefix = "/relationship/"
        elif pagination_type == "optional":
            prefix = "/optional/"
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

    async def run_pagination_test(
        self,
        client,
        path,
        params,
        entities,
        cls_name,
        additional_params,
        result_model_cls,
    ):
        response = await client.get(path, params={**params.dict(), **additional_params})
        response.raise_for_status()

        cls = getattr(self, cls_name)

        with set_page(cls):
            expected = self._normalize_expected(paginate(entities, params))

        a, b = normalize(cls[result_model_cls], expected, response.json())
        assert a == b

    @mark.parametrize(
        "params,cls_name",
        [
            *[(p, "page") for p in _default_params],
            *[(p, "limit_offset_page") for p in _limit_offset_params],
        ],
        ids=[
            *[f"default-{key}" for key in _params_desc],
            *[f"limit-offset-{key}" for key in _params_desc],
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
        await self.run_pagination_test(
            client,
            path,
            params,
            entities,
            cls_name,
            additional_params,
            result_model_cls,
        )

    def _normalize_expected(self, result):
        return result


__all__ = [
    "BasePaginationTestCase",
]
