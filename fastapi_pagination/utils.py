from __future__ import annotations

from typing import TYPE_CHECKING, Optional, TypeVar

from .api import resolve_params

if TYPE_CHECKING:
    from .bases import AbstractParams
    from .types import ParamsType

T = TypeVar("T")


def verify_params(params: Optional[AbstractParams], *params_types: ParamsType) -> AbstractParams:
    params = resolve_params(params)
    raw_params = params.to_raw_params()

    if raw_params.type not in params_types:
        raise ValueError(f"{raw_params.type!r} params not supported")

    return params


__all__ = [
    "verify_params",
]
