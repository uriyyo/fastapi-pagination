from itertools import islice
from typing import Any, Generic, Iterable, Optional, TypeVar

__all__ = [
    "LimitOffsetPage",
    "LimitOffsetParams",
    "Page",
    "Params",
    "paginate",
]

from .api import apply_items_transformer, create_page
from .bases import AbstractParams
from .default import Page as DefaultPage
from .default import Params
from .limit_offset import LimitOffsetPage as DefaultLimitOffsetPage
from .limit_offset import LimitOffsetParams
from .types import AdditionalData, SyncItemsTransformer
from .utils import verify_params

T = TypeVar("T")


class Page(DefaultPage[T], Generic[T]):
    pass


class LimitOffsetPage(DefaultLimitOffsetPage[T], Generic[T]):
    pass


def paginate(
    iterable: Iterable[Any],
    params: Optional[AbstractParams] = None,
    total: Optional[int] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    params_slice = raw_params.as_slice()

    items = [*islice(iterable, params_slice.start, params_slice.stop)]
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=total,
        params=params,
        **(additional_data or {}),
    )
