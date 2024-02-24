from __future__ import annotations

__all__ = [
    "unwrap_annotated",
    "get_caller",
    "create_pydantic_model",
    "verify_params",
    "is_async_callable",
    "check_installed_extensions",
    "disable_installed_extensions_check",
    "FastAPIPaginationWarning",
    "IS_PYDANTIC_V2",
]

import asyncio
import functools
import inspect
import warnings
from typing import TYPE_CHECKING, Any, Optional, Tuple, Type, TypeVar, cast, overload

from pydantic import VERSION, BaseModel
from typing_extensions import Annotated, Literal, get_origin

if TYPE_CHECKING:
    from .bases import AbstractParams, BaseRawParams, CursorRawParams, RawParams
    from .types import ParamsType

    TParams = TypeVar("TParams", bound=AbstractParams)
    TModel = TypeVar("TModel", bound=BaseModel)

IS_PYDANTIC_V2 = VERSION.startswith("2.")


@overload
def verify_params(params: Optional[TParams], *params_types: Literal["limit-offset"]) -> Tuple[TParams, RawParams]:
    pass


@overload
def verify_params(params: Optional[TParams], *params_types: Literal["cursor"]) -> Tuple[TParams, CursorRawParams]:
    pass


@overload
def verify_params(params: Optional[TParams], *params_types: ParamsType) -> Tuple[TParams, BaseRawParams]:
    pass


def verify_params(params: Optional[TParams], *params_types: ParamsType) -> Tuple[TParams, BaseRawParams]:
    from .api import resolve_params

    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if raw_params.type not in params_types:
        raise ValueError(f"{raw_params.type!r} params not supported")

    return params, raw_params


def is_async_callable(obj: Any) -> bool:  # pragma: no cover
    # retrieve base function if embedded
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


_EXTENSIONS = [
    "databases",
    "django",
    "cassandra",
    "tortoise",
    "motor",
    "orm",
    "ormar",
    "pony",
    "piccolo",
    "gino",
    "beanie",
    "sqlmodel",
    "sqlalchemy",
    "asyncpg",
    "mongoengine",
    "pymongo",
]


def _check_installed(module: str) -> bool:
    try:
        __import__(module)
    except ImportError:
        return False
    else:
        return True


class FastAPIPaginationWarning(UserWarning):
    pass


_WARNING_MSG = """
Package "{ext}" is installed.

It's recommended to use extension "fastapi_pagination.ext.{ext}" instead of default 'paginate' implementation.

Otherwise, you can disable this warning by adding the following code to your code:
from fastapi_pagination.utils import disable_installed_extensions_check

disable_installed_extensions_check()
"""

_CHECK_INSTALLED_EXTENSIONS = True


def disable_installed_extensions_check() -> None:
    global _CHECK_INSTALLED_EXTENSIONS
    _CHECK_INSTALLED_EXTENSIONS = False


def check_installed_extensions() -> None:
    if not _CHECK_INSTALLED_EXTENSIONS:
        return

    for ext in _EXTENSIONS:
        if _check_installed(f"fastapi_pagination.ext.{ext}"):
            warnings.warn(
                _WARNING_MSG.format(ext=ext),
                FastAPIPaginationWarning,
                stacklevel=3,
            )
            break


def get_caller(depth: int = 1) -> Optional[str]:
    frame = inspect.currentframe()

    for _ in range(depth + 1):
        if frame is None:
            return None

        frame = frame.f_back

    return cast(Optional[str], frame and frame.f_globals.get("__name__"))


def create_pydantic_model(model_cls: Type[TModel], /, **kwargs: Any) -> TModel:
    if IS_PYDANTIC_V2:
        return model_cls.model_validate(kwargs, from_attributes=True)  # type: ignore

    return model_cls(**kwargs)


def unwrap_annotated(ann: Any) -> Any:
    if get_origin(ann) is Annotated:
        return ann.__args__[0]

    return ann
