from typing import Any, Callable, Optional, Sequence, TypeVar

__all__ = ["paginate"]

from .api import apply_items_transformer, create_page
from .bases import AbstractParams
from .types import AdditionalData, SyncItemsTransformer
from .utils import check_installed_extensions, verify_params

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Callable[[Sequence[T]], int] = len,
    *,
    safe: bool = False,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: Optional[AdditionalData] = None,
) -> Any:
    if not safe:
        check_installed_extensions()

    params, raw_params = verify_params(params, "limit-offset")

    items = sequence[raw_params.as_slice()]
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        total=length_function(sequence) if raw_params.include_total else None,
        params=params,
        **(additional_data or {}),
    )
