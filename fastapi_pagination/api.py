import inspect
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
)

from fastapi import Response

from .bases import AbstractPage, AbstractParams
from .page import Page
from .params import PaginationParams

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
            raise RuntimeError("Use explicit params or pagination dependency")

    return params


def using_params(
    params_type: Type[TAbstractParams],
) -> Callable[[TAbstractParams], Awaitable[TAbstractParams]]:
    async def _pagination_params(*args, **kwargs) -> params_type:  # type: ignore
        params = params_type(*args, **kwargs)  # type: ignore
        params_value.set(params)
        return params

    _pagination_params.__signature__ = inspect.signature(params_type)  # type: ignore

    return _pagination_params


pagination_params = using_params(PaginationParams)


def create_page(items: Sequence[T], total: int, params: AbstractParams) -> AbstractPage[T]:
    return page_type.get().create(items, total, params)


def using_page(page: Type[AbstractPage]) -> ContextManager[None]:
    token = page_type.set(page)

    @contextmanager
    def _reset() -> Iterator[None]:
        try:
            yield
        finally:
            page_type.reset(token)

    return _reset()


def use_as_page(page: Any) -> Any:
    using_page(page)
    return page


async def using_response(res: Response) -> None:
    response_value.set(res)


def response() -> Optional[Response]:
    return response_value.get()


__all__ = [
    "create_page",
    "resolve_params",
    "response",
    "pagination_params",
    "use_as_page",
    "using_params",
    "using_page",
    "using_response",
]
