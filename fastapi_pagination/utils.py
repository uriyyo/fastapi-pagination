from __future__ import annotations

__all__ = [
    "verify_params",
    "is_async_callable",
]

import asyncio
import functools
from typing import Optional, Tuple, TypeVar, overload, Any

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
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))
