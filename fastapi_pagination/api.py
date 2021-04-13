import inspect
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from typing import (
    Any,
    Awaitable,
    Callable,
    ContextManager,
    Iterator,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from fastapi import Depends, FastAPI, Response
from fastapi.dependencies.utils import (
    get_parameterless_sub_dependant,
    lenient_issubclass,
)
from fastapi.routing import APIRoute, APIRouter

from .bases import AbstractPage, AbstractParams
from .default import Page, Params
from .utils import deprecated

T = TypeVar("T")
TAbstractParams = TypeVar("TAbstractParams", covariant=True, bound=AbstractParams)

params_value: ContextVar[AbstractParams] = ContextVar("pagination_value")
response_value: ContextVar[Optional[Response]] = ContextVar("response_value", default=None)
page_type: ContextVar[Type[AbstractPage]] = ContextVar("page_type", default=Page)


def resolve_params(params: Optional[AbstractParams] = None) -> AbstractParams:
    if params is None:
        try:
            return params_value.get()
        except LookupError:
            raise RuntimeError("Use params or add_pagination")

    return params


def create_page(items: Sequence[T], total: int, params: AbstractParams) -> AbstractPage[T]:
    return page_type.get().create(items, total, params)


def response() -> Optional[Response]:
    return response_value.get()


def set_page(page: Type[AbstractPage]) -> None:
    page_type.set(page)


def _create_page_dependency(page: Type[AbstractPage]) -> Callable[[], Awaitable[None]]:
    async def _set_page_type() -> None:
        page_type.set(page)

    return _set_page_type


def _create_params_dependency(
    params: Type[TAbstractParams],
) -> Callable[[TAbstractParams], Awaitable[TAbstractParams]]:
    async def _pagination_params(*args, **kwargs) -> params:  # type: ignore
        val = params(*args, **kwargs)  # type: ignore
        params_value.set(val)

    _pagination_params.__signature__ = inspect.signature(params)  # type: ignore

    return _pagination_params


async def _set_response(res: Response) -> None:
    response_value.set(res)


async def _marker() -> None:
    pass


ParentT = TypeVar("ParentT", APIRouter, FastAPI)


def _update_route(route: APIRoute) -> None:
    if all(
        (
            not any(d.call is _marker for d in route.dependant.dependencies),
            lenient_issubclass(route.response_model, AbstractPage),
        )
    ):
        cls = cast(Type[AbstractPage], route.response_model)

        dependencies = [
            Depends(_marker),
            Depends(_set_response),
            Depends(_create_params_dependency(cls.__params_type__)),
            Depends(_create_page_dependency(cls)),
        ]

        route.dependencies.extend(dependencies)
        route.dependant.dependencies.extend(
            get_parameterless_sub_dependant(
                depends=d,
                path=route.path_format,
            )
            for d in dependencies
        )


def add_pagination(parent: ParentT) -> ParentT:
    for route in parent.routes:
        if isinstance(route, APIRoute):
            _update_route(route)

    return parent


@deprecated
def using_params(
    params_type: Type[TAbstractParams],
) -> Callable[[TAbstractParams], Awaitable[TAbstractParams]]:  # pragma: no cover
    async def _pagination_params(*args, **kwargs) -> params_type:  # type: ignore
        params = params_type(*args, **kwargs)  # type: ignore
        params_value.set(params)
        return params

    _pagination_params.__signature__ = inspect.signature(params_type)  # type: ignore

    return _pagination_params


with warnings.catch_warnings():
    pagination_params = using_params(Params)


@deprecated
def using_page(page: Type[AbstractPage]) -> ContextManager[None]:  # pragma: no cover
    token = page_type.set(page)

    @contextmanager
    def _reset() -> Iterator[None]:
        try:
            yield
        finally:
            page_type.reset(token)

    return _reset()


@deprecated
def use_as_page(page: Any) -> Any:  # pragma: no cover
    using_page(page)
    return page


@deprecated
async def using_response(res: Response) -> None:  # pragma: no cover
    response_value.set(res)


__all__ = [
    "add_pagination",
    "create_page",
    "resolve_params",
    "response",
    "set_page",
    # deprecated api
    "using_response",
    "using_params",
    "using_page",
    "use_as_page",
    "pagination_params",
]
