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

TArg = TypeVar("TArg")
R = TypeVar("R")

Flow: TypeAlias = Generator[
    Union[Awaitable[TArg], TArg],
    TArg,
    R,
]

TFlow = TypeVar("TFlow", bound=Flow[Any, Any])


def flow(func: Callable[P, TFlow]) -> Callable[P, TFlow]:
    return func


def run_sync_flow(gen: Flow[Any, R], /) -> R:
    try:
        res = gen.send(None)

        while True:
            try:
                res = gen.send(res)
            except StopIteration:  # noqa: PERF203
                raise
            except BaseException as exc:  # noqa: BLE001
                res = gen.throw(exc)
    except StopIteration as exc:
        return cast(R, exc.value)


async def run_async_flow(gen: Flow[Any, R], /) -> R:
    try:
        res = gen.send(None)

        while True:
            try:
                res = await await_if_coro(res)
                res = gen.send(res)
            except StopIteration:  # noqa: PERF203
                raise
            except BaseException as exc:  # noqa: BLE001
                res = gen.throw(exc)
    except StopIteration as exc:
        return cast(R, exc.value)
