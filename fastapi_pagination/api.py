__all__ = [
    "add_pagination",
    "create_page",
    "resolve_params",
    "resolve_items_transformer",
    "response",
    "request",
    "set_page",
    "set_items_transformer",
    "apply_items_transformer",
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
    overload,
    Literal,
)

from fastapi import Depends, FastAPI, Request, Response
from fastapi.dependencies.utils import (
    get_parameterless_sub_dependant,
    lenient_issubclass,
)
from fastapi.routing import APIRoute, APIRouter

from .bases import AbstractPage, AbstractParams
from .default import Page
from .types import ItemsTransformer, AsyncItemsTransformer, SyncItemsTransformer
from .utils import is_async_callable

T = TypeVar("T")
TAbstractParams = TypeVar("TAbstractParams", covariant=True, bound=AbstractParams)

_params_val: ContextVar[AbstractParams] = ContextVar("_params_val")
_page_val: ContextVar[Type[AbstractPage[Any]]] = ContextVar("_page_val", default=Page)

_rsp_val: ContextVar[Response] = ContextVar("_rsp_val")
_req_val: ContextVar[Request] = ContextVar("_req_val")

_items_val: ContextVar[Sequence[Any]] = ContextVar("_items_val")
_items_transformer_val: ContextVar[Optional[ItemsTransformer]] = ContextVar("_items_transformer_val", default=None)


def resolve_params(params: Optional[TAbstractParams] = None) -> TAbstractParams:
    if params is None:
        try:
            return cast(TAbstractParams, _params_val.get())
        except LookupError:
            raise RuntimeError("Use params or add_pagination")

    return params


def resolve_items_transformer(transformer: Optional[ItemsTransformer] = None) -> Optional[ItemsTransformer]:
    if transformer is None:
        return _items_transformer_val.get()

    return transformer


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


def set_items_transformer(transformer: ItemsTransformer) -> ContextManager[None]:
    return _ctx_var_with_reset(_items_transformer_val, transformer)


async def async_wrapped(obj: T) -> T:
    return obj


@overload
def apply_items_transformer(
    items: Sequence[Any],
    /,
    transformer: Optional[SyncItemsTransformer] = None,
    *,
    async_: Literal[False] = False,
) -> Sequence[Any]:
    pass


@overload
async def apply_items_transformer(
    items: Sequence[Any],
    /,
    transformer: Optional[AsyncItemsTransformer] = None,
    *,
    async_: Literal[True],
) -> Sequence[Any]:
    pass


def apply_items_transformer(
    items: Sequence[Any],
    /,
    transformer: Optional[ItemsTransformer] = None,
    *,
    async_: bool = False,
) -> Any:
    transformer = resolve_items_transformer(transformer)

    if transformer is None:
        return async_wrapped(items) if async_ else items

    is_coro = is_async_callable(transformer)

    if is_coro and not async_:
        raise ValueError("apply_items_transformer called with async_=False but transformer is async")

    if is_coro:
        return transformer(items)

    items = transformer(items)  # type: ignore[assignment]
    return async_wrapped(items) if async_ else items


def _create_params_dependency(
    params: Type[TAbstractParams],
) -> Callable[[TAbstractParams], AsyncIterator[TAbstractParams]]:
    async def _pagination_params(*args: Any, **kwargs: Any) -> AsyncIterator[TAbstractParams]:
        val = params(*args, **kwargs)
        with _ctx_var_with_reset(_params_val, cast(AbstractParams, val)):
            yield val

    _pagination_params.__signature__ = inspect.signature(params)  # type: ignore[attr-defined]

    return _pagination_params


async def _noop_dep() -> None:
    pass


def pagination_ctx(
    page: Optional[Type[AbstractPage[Any]]] = None,
    params: Optional[Type[AbstractParams]] = None,
    transformer: Optional[ItemsTransformer] = None,
    __page_ctx_dep__: bool = False,
) -> Callable[..., AsyncIterator[AbstractParams]]:
    if page is not None and params is None:
        params = page.__params_type__

    params_dep: Callable[..., Any]
    if params is not None:
        params_dep = _create_params_dependency(params)
    else:
        params_dep = _noop_dep

    async def _page_ctx_dependency(
        req: Request,
        res: Response,
        _params: Any = Depends(params_dep),
    ) -> AsyncIterator[AbstractParams]:
        with ExitStack() as stack:
            if page is not None:
                stack.enter_context(set_page(page))
            if transformer is not None:
                stack.enter_context(set_items_transformer(transformer))

            stack.enter_context(_ctx_var_with_reset(_rsp_val, res))
            stack.enter_context(_ctx_var_with_reset(_req_val, req))

            yield cast(AbstractParams, _params)

    if __page_ctx_dep__:
        _page_ctx_dependency.__page_ctx_dep__ = True  # type: ignore[attr-defined]

    return _page_ctx_dependency


ParentT = TypeVar("ParentT", APIRouter, FastAPI)


def _update_route(route: APIRoute) -> None:
    if any(hasattr(d.call, "__page_ctx_dep__") for d in route.dependant.dependencies):
        return

    if not lenient_issubclass(route.response_model, AbstractPage):
        return

    cls = cast(Type[AbstractPage[Any]], route.response_model)
    dep = Depends(pagination_ctx(cls, __page_ctx_dep__=True))

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
