from __future__ import annotations

__all__ = [
    "verify_params",
    "is_async_callable",
    "check_installed_extensions",
    "FastAPIPaginationWarning",
]

import asyncio
import functools
import warnings
from typing import Any, Optional, Tuple, TypeVar, overload

from typing_extensions import Literal

from .bases import AbstractParams, BaseRawParams, CursorRawParams, RawParams
from .types import ParamsType

TParams = TypeVar("TParams", bound=AbstractParams)


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
warnings.simplefilter("ignore", FastAPIPaginationWarning)
"""


def check_installed_extensions() -> None:
    for ext in _EXTENSIONS:
        if _check_installed(f"fastapi_pagination.ext.{ext}"):
            warnings.warn(
                _WARNING_MSG.format(ext=ext),
                FastAPIPaginationWarning,
                stacklevel=3,
            )
            break
