from typing import Callable, Optional, Sequence, TypeVar, Any

__all__ = ["paginate"]

from .api import create_page
from .bases import AbstractParams
from .types import AdditionalData, ItemsTransformer
from .utils import verify_params

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Callable[[Sequence[T]], int] = len,
    *,
    transformer: Optional[ItemsTransformer] = None,
    additional_data: AdditionalData = None,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    return create_page(
        sequence[raw_params.as_slice()],
        length_function(sequence),
        params,
        transformer=transformer,
        **(additional_data or {}),
    )
