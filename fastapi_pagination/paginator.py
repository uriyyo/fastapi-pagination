from typing import Callable, Optional, Sequence, TypeVar, Any

__all__ = ["paginate"]

from .api import create_page, apply_items_transformer
from .bases import AbstractParams
from .types import AdditionalData, SyncItemsTransformer
from .utils import verify_params

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Callable[[Sequence[T]], int] = len,
    *,
    transformer: Optional[SyncItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    items = sequence[raw_params.as_slice()]
    t_items = apply_items_transformer(items, transformer)

    return create_page(
        t_items,
        length_function(sequence),
        params,
        **(additional_data or {}),
    )
