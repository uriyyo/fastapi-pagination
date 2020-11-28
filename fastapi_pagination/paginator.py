from typing import Optional, Sequence, TypeVar

from .page import BasePage, create_page
from .params import PaginationParamsType, resolve_params

T = TypeVar("T")


def paginate(sequence: Sequence[T], params: Optional[PaginationParamsType] = None) -> BasePage[T]:
    params = resolve_params(params)
    limit_offset_params = params.to_limit_offset()

    return create_page(
        items=sequence[limit_offset_params.offset : limit_offset_params.offset + limit_offset_params.limit],
        total=len(sequence),
        params=params,
    )


__all__ = ["paginate"]
