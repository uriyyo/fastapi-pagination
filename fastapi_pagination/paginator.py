from itertools import islice
from typing import Iterable, Optional, TypeVar

from .api import create_page, resolve_params
from .bases import AbstractPage, AbstractParams

T = TypeVar("T")


def paginate(
    sequence: Iterable[T],
    params: Optional[AbstractParams] = None,
) -> AbstractPage[T]:
    params = resolve_params(params)
    raw_params = params.to_raw_params()
    sliced_sequence = list(islice(sequence, raw_params.offset, raw_params.offset + raw_params.limit))

    return create_page(
        items=sliced_sequence,
        total=len(sliced_sequence),
        params=params,
    )


__all__ = ["paginate"]
