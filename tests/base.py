from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field, replace
from functools import cache
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Generic, Optional, TypeVar

import pytest
from fastapi.applications import FastAPI
from pydantic import BaseModel
from typing_extensions import Literal, Self, TypeAlias

from fastapi_pagination import add_pagination, set_page
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.customization import CustomizedPage, UseOptionalParams
from fastapi_pagination.default import Page, Params
from fastapi_pagination.limit_offset import LimitOffsetPage, LimitOffsetParams
from fastapi_pagination.paginator import paginate

from .schemas import UserOut, UserWithOrderOut
from .utils import normalize

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

PaginationType: TypeAlias = Literal[
    "page-size",
    "limit-offset",
]
PaginationCaseType: TypeAlias = Literal[
    "default",
    "non-scalar",
    "relationship",
    "optional",
]

_pagination_case_to_path: dict[PaginationCaseType, str] = {
    "default": "",
    "non-scalar": "non-scalar/",
    "relationship": "relationship/",
    "optional": "optional/",
}


def _get_route_path(pagination_type: PaginationType, case_type: PaginationCaseType) -> str:
    try:
        return f"/{pagination_type}/{_pagination_case_to_path[case_type]}"
    except KeyError:
        raise ValueError(f"Unknown case type {case_type}") from None


TRoute = TypeVar("TRoute", bound=Callable[..., Any])


@dataclass
class TestCaseBuilder:
    _builder: SuiteBuilder
    _pagination_types: set[PaginationType]
    _case_types: set[PaginationCaseType] = field(default_factory=lambda: {"default"})
    _add_kwargs: dict[str, Any] = field(default_factory=dict)

    def _add_case(self, case_type: PaginationCaseType) -> set[PaginationCaseType]:
        return {*self._case_types, case_type}

    @property
    def empty(self) -> Self:
        return replace(self, _case_types=set())

    @property
    def default(self) -> Self:
        return replace(self, _case_types=self._add_case("default"))

    @property
    def non_scalar(self) -> Self:
        return replace(self, _case_types=self._add_case("non-scalar"))

    @property
    def relationship(self) -> Self:
        return replace(self, _case_types=self._add_case("relationship"))

    @property
    def optional(self) -> Self:
        return replace(self, _case_types=self._add_case("optional"))

    def with_kwargs(self, **kwargs: Any) -> Self:
        return replace(self, _add_kwargs={**self._add_kwargs, **kwargs})

    def __call__(self, func: TRoute) -> TRoute:
        for pagination_type in self._pagination_types:
            for case_type in self._case_types:
                self._builder.add(
                    func,
                    pagination_type,
                    case_type,
                )

        return func


if TYPE_CHECKING:
    TPage = TypeVar("TPage", bound=AbstractPage[Any])

    MakeOptionalPage = Annotated[
        TPage,
        ...,
    ]
else:

    class MakeOptionalPage:
        @classmethod
        @cache
        def __class_getitem__(cls, item):
            return CustomizedPage[item, UseOptionalParams()]


TSuiteBuilder_co = TypeVar("TSuiteBuilder_co", bound="SuiteBuilder", covariant=True)


# TODO: maybe overengineered a bit here?)
@dataclass
class BuilderClasses(Generic[TSuiteBuilder_co]):
    _builder: TSuiteBuilder_co

    if TYPE_CHECKING:
        page_size: type[AbstractPage[Any]]
        limit_offset: type[AbstractPage[Any]]
        model: type[BaseModel]
        model_with_rel: type[BaseModel]

        def update(
            self,
            page_size: Optional[type[AbstractPage[Any]]] = None,
            limit_offset: Optional[type[AbstractPage[Any]]] = None,
            model: Optional[type[BaseModel]] = None,
            model_with_rel: Optional[type[BaseModel]] = None,
        ) -> TSuiteBuilder_co:
            pass
    else:

        def __getattr__(self, item: str) -> Any:
            return getattr(self._builder, f"_{item}_cls")

        def update(
            self,
            **kwargs: Any,
        ) -> Any:
            return replace(
                self._builder,
                **{f"_{k}_cls": v for k, v in kwargs.items() if v is not None},
            )


@dataclass
class SuiteBuilder:
    app: FastAPI = field(default_factory=FastAPI)

    _page_size_cls: type[AbstractPage[[Any]]] = Page
    _limit_offset_cls: type[AbstractPage[Any]] = LimitOffsetPage

    _model_cls: type[BaseModel] = UserOut
    _model_with_rel_cls: type[BaseModel] = UserWithOrderOut

    if TYPE_CHECKING:

        @classmethod
        def with_classes(
            cls,
            page_size: Optional[type[AbstractPage[Any]]] = None,
            limit_offset: Optional[type[AbstractPage[Any]]] = None,
            model: Optional[type[BaseModel]] = None,
            model_with_rel: Optional[type[BaseModel]] = None,
        ) -> Self:
            pass
    else:

        @classmethod
        def with_classes(
            cls,
            **kwargs: Any,
        ) -> Self:
            return cls(**{f"_{k}_cls": v for k, v in kwargs.items() if v is not None})

    @property
    def classes(self) -> BuilderClasses:
        return BuilderClasses(self)

    @property
    def page_size(self) -> TestCaseBuilder:
        return TestCaseBuilder(self, {"page-size"})

    @property
    def limit_offset(self) -> TestCaseBuilder:
        return TestCaseBuilder(self, {"limit-offset"})

    @property
    def both(self) -> TestCaseBuilder:
        return TestCaseBuilder(self, {"page-size", "limit-offset"})

    def get_page_cls_for(
        self,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
    ) -> type[AbstractPage[Any]]:
        if pagination_type == "page-size":
            page_cls = self._page_size_cls
        elif pagination_type == "limit-offset":
            page_cls = self._limit_offset_cls
        else:
            raise ValueError(f"Unknown pagination type {pagination_type}")

        if case_type == "optional":
            page_cls = MakeOptionalPage[self._page_size_cls]

        return page_cls

    def get_model_cls_for(
        self,
        case_type: PaginationCaseType,
    ) -> type[BaseModel]:
        if case_type == "relationship":
            return self._model_with_rel_cls

        return self._model_cls

    def get_response_model_for(
        self,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
    ) -> Any:
        page_cls = self.get_page_cls_for(pagination_type, case_type)
        model_cls = self.get_model_cls_for(case_type)

        return page_cls[model_cls]

    def add(
        self,
        func: TRoute,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
        methods: Iterable[str] = ("GET",),
        **kwargs: Any,
    ) -> TRoute:
        self.app.add_api_route(
            path=_get_route_path(pagination_type, case_type),
            endpoint=func,
            response_model=self.get_response_model_for(pagination_type, case_type),
            methods=[*methods],
            **kwargs,
        )

        return func

    def lifespan(self, lifespan: Any) -> Self:
        old_lifespan = self.app.router.lifespan_context

        @asynccontextmanager
        async def _lifespan_context(*args: Any):
            async with AsyncExitStack() as stack:
                state = await stack.enter_async_context(old_lifespan(*args))

                if hasattr(lifespan, "__aenter__"):  # noqa: SIM108
                    ctx = lifespan
                else:
                    ctx = asynccontextmanager(lifespan)()

                await stack.enter_async_context(ctx)

                yield state

        self.app.router.lifespan_context = _lifespan_context
        return self

    def new(self) -> Self:
        return replace(self, app=FastAPI())

    def build(self) -> FastAPI:
        return add_pagination(self.app)


SuiteDecl: TypeAlias = tuple[
    AbstractParams,
    PaginationType,
    PaginationCaseType,
    str,
]


@pytest.mark.usefixtures("db_type")
class BasePaginationTestSuite:
    is_async: ClassVar[bool] = True
    markers: ClassVar[set[str]] = set()

    pagination_types: ClassVar[set[PaginationType]] = {"page-size", "limit-offset"}
    case_types: ClassVar[set[PaginationCaseType]] = {"default"}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        marker = pytest.mark.parametrize(
            ("params", "pagination_type", "pagination_case_type"),
            [
                pytest.param(param, pagination_type, pagination_case_type, id=id_)
                for param, pagination_type, pagination_case_type, id_ in cls.generate_suites()
            ],
        )

        @marker
        @pytest.mark.asyncio(loop_scope="session")
        async def _run_pagination(
            self,
            client,
            params,
            pagination_type,
            pagination_case_type,
            entities,
            builder,
        ):
            await self.run_pagination_test(
                client,
                params,
                pagination_type,
                pagination_case_type,
                entities,
                builder,
            )

        cls.test_pagination = _run_pagination

        is_async = cls.is_async

        @pytest.fixture(scope="session")
        def is_async_db(_):
            return is_async

        cls.is_async_db = is_async_db

    @classmethod
    def generate_suites(cls) -> Iterable[SuiteDecl]:
        if "page-size" in cls.pagination_types:
            for case in {*cls.case_types} - {"optional"}:
                for param, name in zip(_default_params, _params_desc):
                    yield param, "page-size", case, f"page-size-{case}-{name}"

            if "optional" in cls.case_types:
                yield MakeOptionalPage[Page].__params_type__(), "page-size", "optional", "page-size-optional"

        if "limit-offset" in cls.pagination_types:
            for case in {*cls.case_types} - {"optional"}:
                for param, name in zip(_limit_offset_params, _params_desc):
                    yield param, "limit-offset", case, f"limit-offset-{case}-{name}"

            if "optional" in cls.case_types:
                yield (
                    MakeOptionalPage[LimitOffsetPage].__params_type__(),
                    "limit-offset",
                    "optional",
                    "limit-offset-optional",
                )

    @classmethod
    def create_builder(cls) -> SuiteBuilder:
        return SuiteBuilder()

    @pytest.fixture(scope="session")
    def builder(self) -> SuiteBuilder:
        return self.create_builder()

    async def run_pagination_test(
        self,
        client,
        params,
        pagination_type,
        pagination_case_type,
        entities,
        builder,
    ):
        path = _get_route_path(pagination_type, pagination_case_type)

        response = await client.get(path, params=params.dict(exclude_none=True))
        response.raise_for_status()

        cls = builder.get_response_model_for(pagination_type, pagination_case_type)

        with set_page(cls):
            expected = self._normalize_expected(paginate(entities, params))

        a, b = normalize(cls, expected, response.json())
        assert a == b

    def _normalize_expected(self, result):
        return result


TBasePaginationTestCase = TypeVar("TBasePaginationTestCase", bound=type[BasePaginationTestSuite])


def add_cases(*cases: PaginationCaseType) -> Callable[[TBasePaginationTestCase], TBasePaginationTestCase]:
    def decorator(cls: TBasePaginationTestCase) -> TBasePaginationTestCase:
        cls.case_types = {*cls.case_types, *cases}
        return cls

    return decorator


def only_cases(*cases: PaginationCaseType) -> Callable[[TBasePaginationTestCase], TBasePaginationTestCase]:
    def decorator(cls: TBasePaginationTestCase) -> TBasePaginationTestCase:
        cls.case_types = {*cases}
        return cls

    return decorator


__all__ = [
    "BasePaginationTestSuite",
    "MakeOptionalPage",
    "SuiteBuilder",
    "add_cases",
    "only_cases",
]
