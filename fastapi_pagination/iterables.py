from itertools import islice
from typing import Generic, Iterable, Optional, TypeVar

from pydantic import conint

from .api import create_page
from .bases import AbstractPage, AbstractParams
from .default import Page as DefaultPage
from .default import Params
from .limit_offset import LimitOffsetPage as DefaultLimitOffsetPage
from .limit_offset import LimitOffsetParams
from .utils import verify_params

T = TypeVar("T")


class Page(DefaultPage[T], Generic[T]):
    total: Optional[conint(ge=0)]  # type: ignore


class LimitOffsetPage(DefaultLimitOffsetPage[T], Generic[T]):
    total: Optional[conint(ge=0)]  # type: ignore


def paginate(
    iterable: Iterable[T],
    params: Optional[AbstractParams] = None,
    total: Optional[int] = None,
) -> AbstractPage[T]:
    params, raw_params = verify_params(params, "limit-offset")

    items = [*islice(iterable, raw_params.offset, raw_params.offset + raw_params.limit)]
    return create_page(items, total, params)


__all__ = [
    "Page",
    "Params",
    "LimitOffsetPage",
    "LimitOffsetParams",
    "paginate",
]
