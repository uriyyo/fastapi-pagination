from collections.abc import Callable, Coroutine
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, TypeVar

from faker import Faker
from fastapi import __version__
from pydantic import BaseModel

from fastapi_pagination.pydantic.v2 import is_pydantic_v2_model

faker = Faker()

T = TypeVar("T", bound=BaseModel)


def parse_obj(model: type[T], obj: Any) -> T:
    if is_pydantic_v2_model(model):
        return model.model_validate(obj, from_attributes=True)

    return model.parse_obj(obj)


def normalize(model: type[T], *models: Any) -> list[T]:
    return [parse_obj(model, m) for m in models]


async def maybe_async(obj: Any) -> Any:
    if isinstance(obj, Coroutine):
        return await obj

    return obj


def create_ctx(
    ctx: Callable[[], AbstractContextManager[Any] | AbstractAsyncContextManager[Any]],
    is_async: bool,
) -> Any:
    async def ctx_func():
        if is_async:
            async with ctx() as c:
                yield c
        else:
            with ctx() as c:
                yield c

    return ctx_func


IS_FASTAPI_V_0_112_4_OR_NEWER = tuple(int(part) for part in __version__.split(".") if part.isdigit()) >= (0, 112, 4)


__all__ = [
    "IS_FASTAPI_V_0_112_4_OR_NEWER",
    "create_ctx",
    "faker",
    "maybe_async",
    "normalize",
    "parse_obj",
]
