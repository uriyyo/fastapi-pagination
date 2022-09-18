from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, TypeVar, overload

from typing_extensions import Literal

from .api import resolve_params

if TYPE_CHECKING:
    from .bases import (
        AbstractParams,
        BaseRawParams,
        CursorRawParams,
        RawParams,
    )
    from .types import ParamsType

T = TypeVar("T")
TParams = TypeVar("TParams", bound="AbstractParams")


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
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if raw_params.type not in params_types:
        raise ValueError(f"{raw_params.type!r} params not supported")

    return params, raw_params


__all__ = [
    "verify_params",
]
