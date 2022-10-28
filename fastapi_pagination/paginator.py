from typing import Callable, Optional, Sequence, TypeVar

from .api import create_page
from .bases import AbstractPage, AbstractParams
from .types import AdditionalData
from .utils import verify_params

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Callable[[Sequence[T]], int] = len,
    *,
    additional_data: AdditionalData = None,
) -> AbstractPage[T]:
    params, raw_params = verify_params(params, "limit-offset")

    return create_page(
        sequence[raw_params.offset : raw_params.offset + raw_params.limit],
        length_function(sequence),
        params,
        **(additional_data or {}),
    )


__all__ = ["paginate"]
