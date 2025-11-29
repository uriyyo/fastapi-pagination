from __future__ import annotations

__all__ = [
    "CaseBuilder",
    "SuiteBuilder",
]

from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fastapi import FastAPI
from pydantic import BaseModel
from typing_extensions import Self

from fastapi_pagination import LimitOffsetPage, Page, add_pagination
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.pydantic.v1 import BaseModelV1
from tests.schemas import UserOut, UserOutV1, UserWithOrderOut, UserWithOrderOutV1

from .types import MakeOptionalPage, MakePydanticV1Page, PaginationCaseType, PaginationType

TRoute = TypeVar("TRoute", bound=Callable[..., Any])


@dataclass
class CaseBuilder:
    _builder: SuiteBuilder
    _pagination_types: set[PaginationType]
    _case_types: set[PaginationCaseType] = field(default_factory=set)
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


TSuiteBuilder_co = TypeVar("TSuiteBuilder_co", bound="SuiteBuilder", covariant=True)


# TODO: maybe overengineered a bit here?)
@dataclass
class BuilderClasses(Generic[TSuiteBuilder_co]):
    _builder: TSuiteBuilder_co

    if TYPE_CHECKING:
        page_size: type[AbstractPage[Any]]
        limit_offset: type[AbstractPage[Any]]
        cursor: type[AbstractPage[Any]]
        model: type[BaseModel]
        model_with_rel: type[BaseModel]

        def update(
            self,
            page_size: type[AbstractPage[Any]] | None = None,
            limit_offset: type[AbstractPage[Any]] | None = None,
            cursor: type[AbstractPage[Any]] | None = None,
            model: type[BaseModel] | None = None,
            model_with_rel: type[BaseModel] | None = None,
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


_pagination_case_to_path: dict[PaginationCaseType, str] = {
    "default": "",
    "non-scalar": "non-scalar/",
    "relationship": "relationship/",
    "optional": "optional/",
}


@dataclass
class SuiteBuilder:
    app: FastAPI = field(default_factory=FastAPI)

    _page_size_cls: type[AbstractPage[[Any]]] = Page
    _limit_offset_cls: type[AbstractPage[Any]] = LimitOffsetPage
    _cursor_cls: type[AbstractPage[Any]] = CursorPage

    _model_cls: type[BaseModel] = UserOut
    _model_with_rel_cls: type[BaseModel] = UserWithOrderOut

    _model_cls_v1: type[BaseModelV1] = UserOutV1
    _model_with_rel_cls_v1: type[BaseModelV1] = UserWithOrderOutV1

    if TYPE_CHECKING:

        @classmethod
        def with_classes(
            cls,
            page_size: type[AbstractPage[Any]] | None = None,
            limit_offset: type[AbstractPage[Any]] | None = None,
            cursor: type[AbstractPage[Any]] | None = None,
            model: type[BaseModel] | None = None,
            model_with_rel: type[BaseModel] | None = None,
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
    def page_size(self) -> CaseBuilder:
        return CaseBuilder(self, {"page-size"})

    @property
    def limit_offset(self) -> CaseBuilder:
        return CaseBuilder(self, {"limit-offset"})

    @property
    def both(self) -> CaseBuilder:
        return CaseBuilder(self, {"page-size", "limit-offset"})

    @property
    def cursor(self) -> CaseBuilder:
        return CaseBuilder(self, {"cursor"})

    def get_route_path(
        self,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
    ) -> str:
        try:
            return f"/{pagination_type}/{_pagination_case_to_path[case_type]}"
        except KeyError:
            raise ValueError(f"Unknown case type {case_type}") from None

    def get_page_cls_for(
        self,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
        pydantic_v1: bool = False,
    ) -> type[AbstractPage[Any]]:
        if pagination_type == "page-size":
            page_cls = self._page_size_cls
        elif pagination_type == "limit-offset":
            page_cls = self._limit_offset_cls
        elif pagination_type == "cursor":
            page_cls = self._cursor_cls
        else:
            raise ValueError(f"Unknown pagination type {pagination_type}")

        if pydantic_v1:
            page_cls = MakePydanticV1Page[page_cls]

        if case_type == "optional":
            page_cls = MakeOptionalPage[page_cls]

        return page_cls

    def get_model_cls_for(
        self,
        case_type: PaginationCaseType,
        pydantic_v1: bool = False,
    ) -> type[BaseModel]:
        if pydantic_v1:
            if case_type == "relationship":
                return self._model_with_rel_cls_v1

            return self._model_cls_v1

        if case_type == "relationship":
            return self._model_with_rel_cls

        return self._model_cls

    def get_response_model_for(
        self,
        pagination_type: PaginationType,
        case_type: PaginationCaseType,
        pydantic_v1: bool = False,
    ) -> Any:
        page_cls = self.get_page_cls_for(pagination_type, case_type, pydantic_v1)
        model_cls = self.get_model_cls_for(case_type, pydantic_v1)

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
            path=self.get_route_path(pagination_type, case_type),
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
