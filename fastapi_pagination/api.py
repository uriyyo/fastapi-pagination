__all__ = [
    "add_pagination",
    "create_page",
    "resolve_params",
    "response",
    "request",
    "set_page",
    "pagination_ctx",
    "pagination_items",
]

import inspect
from contextlib import ExitStack, contextmanager, suppress
from contextvars import ContextVar
from typing import (
    Any,
    AsyncIterator,
    Callable,
    ContextManager,
    Iterator,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

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

_params_val: ContextVar[AbstractParams] = ContextVar("_params_val")
_page_val: ContextVar[Type[AbstractPage[Any]]] = ContextVar("_page_val", default=Page)

_rsp_val: ContextVar[Response] = ContextVar("_rsp_val")
_req_val: ContextVar[Request] = ContextVar("_req_val")

_items_val: ContextVar[Sequence[Any]] = ContextVar("_items_val")


def resolve_params(params: Optional[TAbstractParams] = None) -> TAbstractParams:
    if params is None:
        try:
            return cast(TAbstractParams, _params_val.get())
        except LookupError:
            raise RuntimeError("Use params or add_pagination")

    return params


def pagination_items() -> Sequence[Any]:
    try:
        return _items_val.get()
    except LookupError:
        raise RuntimeError("pagination_items must be called inside create_page")


def create_page(
    items: Sequence[T],
    total: Optional[int] = None,
    params: Optional[AbstractParams] = None,
    **kwargs: Any,
) -> AbstractPage[T]:
    kwargs["params"] = params

    if total is not None:  # temporary to support old signature
        kwargs["total"] = total

    with _ctx_var_with_reset(_items_val, items):
        return _page_val.get().create(items, **kwargs)


def response() -> Response:
    try:
        return _rsp_val.get()
    except LookupError:
        raise RuntimeError("response context var must be set")


def request() -> Request:
    try:
        return _req_val.get()
    except LookupError:
        raise RuntimeError("request context var must be set")


def _ctx_var_with_reset(var: ContextVar[T], value: T) -> ContextManager[None]:
    token = var.set(value)

    @contextmanager
    def _reset_ctx() -> Iterator[None]:
        yield

        with suppress(ValueError):
            var.reset(token)

    return _reset_ctx()


def set_page(page: Type[AbstractPage[Any]]) -> ContextManager[None]:
    return _ctx_var_with_reset(_page_val, page)


def _create_params_dependency(
    params: Type[TAbstractParams],
) -> Callable[[TAbstractParams], AsyncIterator[TAbstractParams]]:
    async def _pagination_params(*args: Any, **kwargs: Any) -> AsyncIterator[TAbstractParams]:
        val = params(*args, **kwargs)
        with _ctx_var_with_reset(_params_val, cast(AbstractParams, val)):
            yield val

    _pagination_params.__signature__ = inspect.signature(params)  # type: ignore[attr-defined]

    return _pagination_params


def pagination_ctx(
    page: Type[AbstractPage[Any]],
    params: Optional[Type[AbstractParams]] = None,
) -> Callable[..., AsyncIterator[AbstractParams]]:
    if params is None:
        params = page.__params_type__

    async def _page_ctx_dependency(
        req: Request,
        res: Response,
        _params: Any = Depends(_create_params_dependency(params)),  # type: ignore[arg-type]
    ) -> AsyncIterator[AbstractParams]:
        with ExitStack() as stack:
            stack.enter_context(set_page(page))
            stack.enter_context(_ctx_var_with_reset(_rsp_val, res))
            stack.enter_context(_ctx_var_with_reset(_req_val, req))

            yield cast(AbstractParams, _params)

    _page_ctx_dependency.__page_ctx_dep__ = True  # type: ignore[attr-defined]

    return _page_ctx_dependency


ParentT = TypeVar("ParentT", APIRouter, FastAPI)


def _update_route(route: APIRoute) -> None:
    if any(hasattr(d.call, "__page_ctx_dep__") for d in route.dependant.dependencies):
        return

    if not lenient_issubclass(route.response_model, AbstractPage):
        return

    cls = cast(Type[AbstractPage[Any]], route.response_model)
    dep = Depends(pagination_ctx(cls))

    route.dependencies.append(dep)
    route.dependant.dependencies.append(
        get_parameterless_sub_dependant(
            depends=dep,
            path=route.path_format,
        )
    )


def _add_pagination(parent: ParentT) -> None:
    if hasattr(parent, "openapi_schema"):
        parent.openapi_schema = None

    for route in parent.routes:
        if isinstance(route, APIRoute):
            _update_route(route)


def add_pagination(parent: ParentT) -> ParentT:
    _add_pagination(parent)

    @parent.on_event("startup")
    def on_startup() -> None:
        _add_pagination(parent)

    return parent
