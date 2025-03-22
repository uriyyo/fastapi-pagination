from collections.abc import Iterable
from itertools import islice
from typing import Any, Optional, TypeVar

__all__ = [
    "LimitOffsetPage",
    "LimitOffsetParams",
    "Page",
    "Params",
    "paginate",
]

from .bases import AbstractParams
from .config import Config
from .default import Page, Params
from .flow import flow_expr, run_sync_flow
from .flows import generic_flow
from .limit_offset import LimitOffsetPage, LimitOffsetParams
from .types import AdditionalData, SyncItemsTransformer

T = TypeVar("T")


def paginate(
    iterable: Iterable[Any],
    params: Optional[AbstractParams] = None,
    total: Optional[int] = None,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    return run_sync_flow(
        generic_flow(
            limit_offset_flow=flow_expr(
                lambda r: [
                    *islice(
                        iterable,
                        r.as_slice().start,
                        r.as_slice().stop,
                    )
                ],
            ),
            total_flow=flow_expr(lambda: total),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
