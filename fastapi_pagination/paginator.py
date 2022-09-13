from typing import Callable, Optional, Sequence, TypeVar

from .api import create_page
from .bases import AbstractPage, AbstractParams
from .utils import verify_params

T = TypeVar("T")


def paginate(
    sequence: Sequence[T],
    params: Optional[AbstractParams] = None,
    length_function: Callable[[Sequence[T]], int] = len,
) -> AbstractPage[T]:
    params = verify_params(params, "limit-offset")
    raw_params = params.to_raw_params().as_limit_offset()

    return create_page(
        items=sequence[raw_params.offset : raw_params.offset + raw_params.limit],
        total=length_function(sequence),
        params=params,
    )


__all__ = ["paginate"]
