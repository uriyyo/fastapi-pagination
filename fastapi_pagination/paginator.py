from collections.abc import Sequence
from typing import Any, Callable, Optional, TypeVar

__all__ = ["paginate"]

from .bases import AbstractParams
from .config import Config
from .flow import flow_expr, run_sync_flow
from .flows import generic_flow
from .types import AdditionalData, SyncItemsTransformer
from .utils import check_installed_extensions

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Optional[Callable[[Sequence[T]], int]] = None,
    *,
    safe: bool = False,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
    config: Optional[Config] = None,
) -> Any:
    if not safe:
        check_installed_extensions()

    if length_function is None:
        length_function = len

    return run_sync_flow(
        generic_flow(
            limit_offset_flow=flow_expr(lambda r: sequence[r.as_slice()]),
            total_flow=flow_expr(lambda: length_function(sequence)),
            params=params,
            transformer=transformer,
            additional_data=additional_data,
            config=config,
        )
    )
