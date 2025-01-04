__all__ = [
    "Flow",
    "flow",
    "run_async_flow",
    "run_sync_flow",
]

from collections.abc import Awaitable, Generator
from typing import Any, Callable, TypeVar, Union, cast

from typing_extensions import ParamSpec, TypeAlias

from fastapi_pagination.utils import await_if_coro

P = ParamSpec("P")
R = TypeVar("R")

Flow: TypeAlias = Generator[
    Callable[[], Union[Any, Awaitable[Any]]],
    Any,
    R,
]

TFlow = TypeVar("TFlow", bound=Flow[Any])


def flow(func: Callable[P, TFlow]) -> Callable[P, TFlow]:
    return func


def run_sync_flow(gen: Flow[R], /) -> R:
    try:
        callback = gen.send(None)
        while True:
            callback = gen.send(callback())
    except StopIteration as exc:
        return cast(R, exc.value)


async def run_async_flow(gen: Flow[R], /) -> R:
    try:
        callback = gen.send(None)
        while True:
            callback = gen.send(await await_if_coro(callback()))
    except StopIteration as exc:
        return cast(R, exc.value)
