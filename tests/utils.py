from collections.abc import Callable, Coroutine
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, TypeVar, Union

from faker import Faker
from pydantic import BaseModel

from fastapi_pagination.utils import IS_PYDANTIC_V2

faker = Faker()

T = TypeVar("T", bound=BaseModel)

if IS_PYDANTIC_V2:
    from pydantic import TypeAdapter

    def parse_obj_as(tp: Any, obj: Any) -> Any:
        return TypeAdapter(tp).validate_python(obj, from_attributes=True)

    def parse_obj(model: type[T], obj: Any) -> T:
        return model.model_validate(obj, from_attributes=True)
else:
    from pydantic import parse_obj_as as _parse_obj_as

    def parse_obj_as(tp: Any, obj: Any) -> Any:
        return _parse_obj_as(tp, obj)

    def parse_obj(model: type[T], obj: Any) -> T:
        return model.parse_obj(obj)


def normalize(model: type[T], *models: Any) -> list[T]:
    return [parse_obj(model, m) for m in models]


async def maybe_async(obj: Any) -> Any:
    if isinstance(obj, Coroutine):
        return await obj

    return obj


def create_ctx(
    ctx: Callable[[], Union[AbstractContextManager[Any], AbstractAsyncContextManager[Any]]],
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


__all__ = [
    "create_ctx",
    "faker",
    "maybe_async",
    "normalize",
    "parse_obj",
    "parse_obj_as",
]
