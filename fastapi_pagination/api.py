import inspect
from contextvars import ContextVar
from typing import Awaitable, Callable, Optional, Sequence, Type, TypeVar, cast

from fastapi import Depends, FastAPI, Request, Response
from fastapi.dependencies.utils import (
    get_parameterless_sub_dependant,
    lenient_issubclass,
)
from fastapi.routing import APIRoute, APIRouter

from .bases import AbstractPage, AbstractParams
from .default import Page

T = TypeVar("T")
TAbstractParams = TypeVar("TAbstractParams", covariant=True, bound=AbstractParams)

params_value: ContextVar[AbstractParams] = ContextVar("params_value")
page_type: ContextVar[Type[AbstractPage]] = ContextVar("page_type", default=Page)

response_value: ContextVar[Response] = ContextVar("response_value")
request_value: ContextVar[Request] = ContextVar("request_value")


def resolve_params(params: Optional[AbstractParams] = None) -> AbstractParams:
    if params is None:
        try:
            return params_value.get()
        except LookupError:
            raise RuntimeError("Use params or add_pagination")

    return params


def create_page(items: Sequence[T], total: int, params: AbstractParams) -> AbstractPage[T]:
    return page_type.get().create(items, total, params)


def response() -> Response:
    try:
        return response_value.get()
    except LookupError:
        raise RuntimeError("response context var must be set")


def request() -> Request:
    try:
        return request_value.get()
    except LookupError:
        raise RuntimeError("request context var must be set")


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


async def _set_request_response(req: Request, res: Response) -> None:
    response_value.set(res)
    request_value.set(req)


async def _marker() -> None:
    pass


ParentT = TypeVar("ParentT", APIRouter, FastAPI)


def _update_route(route: APIRoute) -> None:
    if any(d.call is _marker for d in route.dependant.dependencies):
        return

    if not lenient_issubclass(route.response_model, AbstractPage):
        return

    cls = cast(Type[AbstractPage], route.response_model)

    dependencies = [
        Depends(_marker),
        Depends(_set_request_response),
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


__all__ = [
    "add_pagination",
    "create_page",
    "resolve_params",
    "response",
    "request",
    "set_page",
]
