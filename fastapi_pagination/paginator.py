from typing import Optional, Sequence, TypeVar

from .api import create_page, resolve_params
from .bases import AbstractPage, AbstractParams

T = TypeVar("T")


def paginate(sequence: Sequence[T], params: Optional[AbstractParams] = None) -> AbstractPage[T]:
    params = resolve_params(params)
    limit_offset_params = params.to_limit_offset()

    return create_page(
        items=sequence[limit_offset_params.offset : limit_offset_params.offset + limit_offset_params.limit],
        total=len(sequence),
        params=params,
    )


__all__ = ["paginate"]
