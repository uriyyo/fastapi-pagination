from itertools import islice
from typing import Generic, Iterable, Optional, TypeVar, Any

__all__ = [
    "Page",
    "Params",
    "LimitOffsetPage",
    "LimitOffsetParams",
    "paginate",
]

from .api import create_page
from .bases import AbstractParams
from .default import Page as DefaultPage
from .default import Params
from .limit_offset import LimitOffsetPage as DefaultLimitOffsetPage
from .limit_offset import LimitOffsetParams
from .types import AdditionalData, GreaterEqualZero
from .utils import verify_params

T = TypeVar("T")


class Page(DefaultPage[T], Generic[T]):
    total: Optional[GreaterEqualZero]  # type: ignore[assignment]


class LimitOffsetPage(DefaultLimitOffsetPage[T], Generic[T]):
    total: Optional[GreaterEqualZero]  # type: ignore[assignment]


def paginate(
    iterable: Iterable[Any],
    params: Optional[AbstractParams] = None,
    total: Optional[int] = None,
    *,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    items = [*islice(iterable, raw_params.offset, raw_params.offset + raw_params.limit)]
    return create_page(items, total, params, **(additional_data or {}))
